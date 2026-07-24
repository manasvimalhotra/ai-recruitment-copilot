"""
upload.py
---------
API route for uploading a resume file. This ties together:
  1. services/parser.py    -> raw text extraction
  2. services/extractor.py -> structured field extraction
  3. models/candidate.py   -> persistence to MySQL
"""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.schemas.candidate import UploadResponse, CandidateResponse
from app.services.parser import extract_text, UnsupportedFileTypeError
from app.services.extractor import extract_profile
from app.utils.helpers import (
    is_allowed_file,
    generate_unique_filename,
    save_upload_file,
    save_extracted_json,
    list_to_json,
)

router = APIRouter(prefix="/api/upload", tags=["Upload"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
EXTRACTED_DIR = os.getenv("EXTRACTED_DIR", "extracted_data")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))


@router.post("/resume", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts a single PDF or DOCX resume, parses it, extracts a structured
    profile, saves both the raw file and the DB record, and returns the
    created candidate profile.
    """
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a .pdf or .docx file.",
        )

    file_bytes = await file.read()

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max allowed is {MAX_UPLOAD_SIZE_MB}MB.",
        )

    # Save the raw file under a unique name so re-uploads never collide
    unique_name = generate_unique_filename(file.filename)
    file_path = save_upload_file(UPLOAD_DIR, unique_name, file_bytes)

    # Step 1: raw text extraction
    try:
        raw_text = extract_text(file_path)
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from this file. It may be a scanned/image-based document.",
        )

    # Step 2: structured field extraction
    profile = extract_profile(raw_text)

    # Step 3: persist to DB
    candidate = Candidate(
        name=profile.get("name"),
        email=profile.get("email"),
        phone=profile.get("phone"),
        skills=list_to_json(profile.get("skills", [])),
        education=list_to_json(profile.get("education", [])),
        experience=list_to_json(profile.get("experience", [])),
        total_experience_years=profile.get("total_experience_years"),
        raw_text=raw_text,
        source_filename=file.filename,
        extraction_accuracy=profile.get("extraction_accuracy"),
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    # Also keep a JSON copy on disk for quick inspection/debugging
    save_extracted_json(EXTRACTED_DIR, candidate.id, profile)

    response_candidate = CandidateResponse(
        id=candidate.id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        skills=profile.get("skills", []),
        education=profile.get("education", []),
        experience=profile.get("experience", []),
        total_experience_years=candidate.total_experience_years,
        source_filename=candidate.source_filename,
        extraction_accuracy=candidate.extraction_accuracy,
        created_at=candidate.created_at,
    )

    return UploadResponse(
        message="Resume uploaded and parsed successfully.",
        candidate=response_candidate,
    )
