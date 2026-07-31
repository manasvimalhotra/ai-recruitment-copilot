from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
 
from app.database import Base
 
 
class JobPosting(Base):
    __tablename__ = "job_postings"
 
    id = Column(Integer, primary_key=True, index=True)
 
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
 
    # JSON list of {"skill": "python", "level": "advanced"} objects.
    # "level" is one of: basic, intermediate, advanced -- used only to
    # judge how big a candidate's skill gap is, not as a hard filter.
    required_skills = Column(Text, nullable=True)
 
    min_experience_years = Column(Float, nullable=True)
 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
 









