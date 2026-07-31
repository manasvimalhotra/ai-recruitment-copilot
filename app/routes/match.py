from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
 
from app.database import get_db
from app.models.candidate import Candidate
from app.models.job import JobPosting
from app.services import matching
from app.utils.helpers import json_to_list
 
router = APIRouter(prefix="/api/match", tags=["Matching"])
 
 
def _candidate_dict(c: Candidate) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "skills": json_to_list(c.skills),
        "total_experience_years": c.total_experience_years,
    }
 
 
def _job_dict(j: JobPosting) -> dict:
    return {
        "id": j.id,
        "title": j.title,
        "required_skills": json_to_list(j.required_skills),
        "min_experience_years": j.min_experience_years,
    }
 
 
@router.get("/{job_id}")
def match_candidates_to_job(job_id: int, db: Session = Depends(get_db)):
    """
    Candidate Matching panel: returns every candidate's match score against
    this job, sorted best-match first.
    """
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")
 
    job_data = _job_dict(job)
    candidates = db.query(Candidate).all()
    if not candidates:
        return {"job": job_data, "matches": []}
 
    results = []
    for c in candidates:
        c_data = _candidate_dict(c)
        score = matching.calculate_match(c_data, job_data)
        results.append({**c_data, **score})
 
    results.sort(key=lambda r: r["match_percent"], reverse=True)
    return {"job": job_data, "matches": results}
 
 
@router.get("/{job_id}/candidate/{candidate_id}")
def skill_gap_for_candidate(job_id: int, candidate_id: int, db: Session = Depends(get_db)):
    """
    Skill Gap Analysis panel: per-skill breakdown of one candidate against
    one job, plus a short templated recommendation.
    """
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")
 
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
 
    job_data = _job_dict(job)
    candidate_data = _candidate_dict(candidate)
 
    score = matching.calculate_match(candidate_data, job_data)
    gap = matching.analyze_skill_gap(candidate_data, job_data)
 
    return {
        "job": job_data,
        "candidate": candidate_data,
        "match": score,
        **gap,
    }
