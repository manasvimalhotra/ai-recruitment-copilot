"""
SQLAlchemy model representing a parsed candidate profile.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func

from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)

    # Structured content (stored as JSON-encoded text for simplicity in MySQL)
    skills = Column(Text, nullable=True)          # JSON list, e.g. ["Python", "SQL"]
    education = Column(Text, nullable=True)       # JSON list of education entries
    experience = Column(Text, nullable=True)      # JSON list of work experience entries

    total_experience_years = Column(Float, nullable=True)

    # Raw text kept for re-processing / auditing
    raw_text = Column(Text, nullable=True)

    # File tracking
    source_filename = Column(String(255), nullable=True)
    extraction_accuracy = Column(Float, nullable=True)  # % of fields successfully extracted

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
