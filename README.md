# AI Recruitment & Talent Management Copilot

**Milestone 1 (Weeks 1–2): Resume Parsing & Candidate Profiling**

This milestone implements:
- Resume upload (PDF/DOCX)
- Text extraction (pdfplumber, PyPDF2, python-docx)
- NLP-based candidate field extraction (spaCy + regex): name, email, phone,
  skills, education, experience, total years of experience
- Structured candidate profiles saved to MySQL
- CSV export of all candidates (pandas)

## Project Structure

```
AI-Recruitment-Copilot/
│
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── routes/
│   │   ├── upload.py           # POST /api/upload/resume
│   │   └── candidate.py        # GET/DELETE candidates, CSV export
│   ├── services/
│   │   ├── parser.py           # File -> raw text
│   │   └── extractor.py        # Raw text -> structured fields
│   ├── models/
│   │   └── candidate.py        # SQLAlchemy ORM model
│   ├── schemas/
│   │   └── candidate.py        # Pydantic request/response models
│   ├── database.py             # MySQL connection (SQLAlchemy + pymysql)
│   └── utils/
│       └── helpers.py          # File validation, JSON helpers
│
├── uploads/                    # Uploaded resumes land here
├── extracted_data/             # JSON copy of each parsed profile
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### 1. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Download the spaCy language model (used for name detection)

```bash
python -m spacy download en_core_web_sm
```

### 3. Set up MySQL

Create a database:

```sql
CREATE DATABASE recruitment_copilot;
```

Copy `.env.example` to `.env` and fill in your MySQL credentials:

```bash
cp .env.example .env
```

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=recruitment_copilot
```

Tables are auto-created on startup — no manual migration needed for this milestone.

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

Visit **http://localhost:8000/docs** for interactive Swagger API docs.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/upload/resume` | Upload a resume (PDF/DOCX), parse it, save profile |
| GET | `/api/candidates/` | List all candidate profiles (paginated) |
| GET | `/api/candidates/{id}` | Get one candidate profile |
| DELETE | `/api/candidates/{id}` | Delete a candidate profile |
| GET | `/api/candidates/export/csv` | Export all candidates as CSV |

## Example: uploading a resume with curl

```bash
curl -X POST "http://localhost:8000/api/upload/resume" \
  -F "file=@/path/to/resume.pdf"
```

Example response:

```json
{
  "message": "Resume uploaded and parsed successfully.",
  "candidate": {
    "id": 1,
    "name": "Jane Doe",
    "email": "jane.doe@email.com",
    "phone": "+91 98765 43210",
    "skills": ["python", "sql", "fastapi", "docker"],
    "education": [{"degree": "B.Tech Computer Science, XYZ University", "institution": null, "year": null}],
    "experience": [{"title": "Software Engineer, ABC Corp (2021-2024)", "company": null, "duration": null}],
    "total_experience_years": 3.0,
    "source_filename": "jane_resume.pdf",
    "extraction_accuracy": 100.0,
    "created_at": "2026-07-22T10:00:00"
  }
}
```

## Notes on the extraction logic (`app/services/extractor.py`)

This milestone uses a **rule-based + spaCy NER hybrid** rather than an LLM API,
so it runs fully offline:
- **Name**: spaCy `PERSON` entity from the first few lines of the resume
- **Email/Phone**: regex patterns
- **Skills**: keyword match against `SKILLS_DB` (extend this list as you test more resumes)
- **Education/Experience**: section-header detection + line grouping (intentionally simple for Milestone 1 — refine in Milestone 2)
- **Extraction accuracy**: % of core fields successfully populated, shown per-candidate

## Known limitations (to address in later milestones)

- Education/experience parsing is line-based, not deeply structured (no separate company/duration parsing yet)
- Scanned/image-based PDFs (no embedded text) aren't supported yet — would need OCR (e.g. `pytesseract`)
- Skills list is a static dictionary — consider moving to a DB table or expanding via a taxonomy (e.g. ESCO/O*NET) later
- No authentication yet on API routes

## Next Milestones (per project plan)

- Milestone 2: Job posting management + candidate-job matching
- Milestone 3: AI-powered candidate ranking/scoring
- Milestone 4: Interview scheduling & communication automation
