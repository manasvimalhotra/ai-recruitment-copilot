"""
Pydantic schemas used for API request/response validation.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EducationEntry(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None


class ExperienceEntry(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None


class CandidateBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    education: List[EducationEntry] = []
    experience: List[ExperienceEntry] = []
    total_experience_years: Optional[float] = None


class CandidateCreate(CandidateBase):
    source_filename: Optional[str] = None
    raw_text: Optional[str] = None
    extraction_accuracy: Optional[float] = None


class CandidateResponse(CandidateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_filename: Optional[str] = None
    extraction_accuracy: Optional[float] = None
    created_at: Optional[datetime] = None


class UploadResponse(BaseModel):
    message: str
    candidate: CandidateResponse
