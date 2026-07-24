import re
import spacy
from typing import Optional
 
# Load once at module import time (expensive to reload per request)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Model not downloaded yet -- caller should run:
    #   python -m spacy download en_core_web_sm
    nlp = None
 
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
 
# Matches a contiguous run of digits + phone-ish separators (spaces, dashes,
# dots, parens, leading +), rather than assuming fixed group sizes like
# "3 digits - 3 digits - 4 digits". Real numbers vary a lot in how they're
# grouped (e.g. Indian mobiles are often split 5+5, like 98200-11223), and
# a rigid pattern silently truncates anything that doesn't match its shape.
# We instead grab the whole run and validate/clean it in extract_phone().
PHONE_REGEX = re.compile(r"\+?\(?[\d][\d\s().-]{6,17}\d")
 
YEARS_EXPERIENCE_REGEX = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)\s*(?:of)?\s*experience", re.IGNORECASE
)
 
SECTION_HEADERS = {
    "education": ["education", "academic background", "qualifications"],
    "experience": ["experience", "work experience", "employment history", "professional experience"],
    "skills": ["skills", "technical skills", "core competencies"],
}
 
# A starter skills dictionary -- extend this over the internship as you
# see more resume formats. Consider loading this from a config/DB table later.
SKILLS_DB = [
    "python", "java", "c++", "c#", "javascript", "typescript", "sql", "mysql",
    "postgresql", "mongodb", "fastapi", "flask", "django", "react", "angular",
    "vue", "node.js", "express", "aws", "azure", "gcp", "docker", "kubernetes",
    "git", "linux", "machine learning", "deep learning", "nlp", "spacy",
    "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "power bi",
    "tableau", "excel", "rest api", "graphql", "html", "css", "jira", "agile",
]
 
 
def _split_into_sections(text: str) -> dict:
    
    lines = text.split("\n")
    sections = {"other": []}
    current = "other"
 
    for line in lines:
        stripped = line.strip().lower()
        matched = False
        for section, headers in SECTION_HEADERS.items():
            if any(stripped == h or stripped.startswith(h) for h in headers):
                current = section
                sections.setdefault(current, [])
                matched = True
                break
        if not matched:
            sections.setdefault(current, [])
            sections[current].append(line)
 
    return sections
 
 
def extract_email(text: str) -> Optional[str]:
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else None
 
 
# A bare year range like "2018-2024" is 8 digits and passes the length
# check below, but it's clearly not a phone number -- filter it out
# explicitly rather than by digit count alone.
YEAR_RANGE_REGEX = re.compile(r"^(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}$")
 
 
def extract_phone(text: str) -> Optional[str]:
    for match in PHONE_REGEX.finditer(text):
        candidate = match.group(0).strip()
        # Trim stray separators the loose regex might grab at the edges
        # (e.g. a trailing "-" or "." caught right before a line break).
        candidate = candidate.strip(" .-")
 
        if YEAR_RANGE_REGEX.match(candidate.strip("()[] ")):
            continue
 
        digits = re.sub(r"\D", "", candidate)
        # Filter out short false-positives (dates, zip codes, etc.)
        if 7 <= len(digits) <= 15:
            return candidate
    return None
 
 
def _looks_like_a_name(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 40:
        return False
    if "@" in line or any(ch.isdigit() for ch in line):
        return False
    if any(bad in line.lower() for bad in ["resume", "curriculum", "cv", "profile"]):
        return False
 
    words = line.split()
    if not (2 <= len(words) <= 4):
        return False
 
    # Every word should look like a name token: starts capitalized,
    # rest lowercase letters only (allows hyphens/apostrophes).
    for w in words:
        core = w.replace("-", "").replace("'", "").replace(".", "")
        if not core.isalpha():
            return False
        if not core[0].isupper():
            return False
 
    return True
 
 
def extract_name(text: str) -> Optional[str]:
    
    lines = [l for l in text.split("\n") if l.strip()]
 
    # Check the first few lines directly -- handles the common case where
    # line 1 is a title like "RESUME" / "CURRICULUM VITAE" and the actual
    # name is on the next line.
    for line in lines[:3]:
        if _looks_like_a_name(line):
            return line.strip()
 
    if nlp is None:
        return None
 
    header_text = "\n".join(lines[:5])
    doc = nlp(header_text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    return None
 
 
def extract_skills(text: str) -> list:
    lower_text = text.lower()
    found = [skill for skill in SKILLS_DB if skill in lower_text]
    # Preserve nice casing for known acronyms
    return sorted(set(found))
 
 
def extract_total_experience(text: str) -> Optional[float]:
    match = YEARS_EXPERIENCE_REGEX.search(text)
    if match:
        return float(match.group(1))
    return None
 
 
def extract_education(sections: dict) -> list:
    """Very lightweight: returns each non-empty line under 'education' as an entry."""
    lines = [l.strip() for l in sections.get("education", []) if l.strip()]
    return [{"degree": line, "institution": None, "year": None} for line in lines]
 
 
def extract_experience(sections: dict) -> list:
    
    lines = [l.strip() for l in sections.get("experience", []) if l.strip()]
    return [{"title": line, "company": None, "duration": None} for line in lines]
 
 
def calculate_extraction_accuracy(profile: dict) -> float:
   
    core_fields = ["name", "email", "phone", "skills", "education", "experience"]
    filled = 0
    for field in core_fields:
        value = profile.get(field)
        if value:
            filled += 1
    return round((filled / len(core_fields)) * 100, 1)
 
 
def extract_profile(text: str) -> dict:
   
    sections = _split_into_sections(text)
 
    profile = {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(sections),
        "experience": extract_experience(sections),
        "total_experience_years": extract_total_experience(text),
    }
    profile["extraction_accuracy"] = calculate_extraction_accuracy(profile)
    return profile