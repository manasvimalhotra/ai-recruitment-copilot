
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
 
VALID_LEVELS = {"basic", "intermediate", "advanced"}
 
 
class RequiredSkill(BaseModel):
    skill: str
    level: str = Field(default="intermediate")  # basic | intermediate | advanced
 
 
class JobPostingBase(BaseModel):
    title: str
    description: Optional[str] = None
    required_skills: List[RequiredSkill] = []
    min_experience_years: Optional[float] = None
 
 
class JobPostingCreate(JobPostingBase):
    pass
 
 
class JobPostingResponse(JobPostingBase):
    model_config = ConfigDict(from_attributes=True)
 
    id: int
    created_at: Optional[datetime] = None