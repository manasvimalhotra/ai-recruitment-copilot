# AI Recruitment & Talent Management Copilot

**Milestone 1 (Weeks 1-2): Resume Parsing & Candidate Profiling**

This milestone implements:
- Resume upload (PDF/DOCX)
- Text extraction (pdfplumber, PyPDF2, python-docx)
- NLP-based candidate field extraction (spaCy + regex): name, email, phone,
  skills, education, experience, total years of experience
- Structured candidate profiles saved to MySQL
- CSV export of all candidates (pandas)

**Milestone 2 (Weeks 3-4): Matching & Skill Analysis**

This milestone adds:
- Job posting management (title, required skills + level, minimum experience)
- Candidate-job matching engine with a 0-100 hiring/match score
- Skill-gap analysis per candidate per job, with a templated recommendation
- Dashboard sidebar with Job Postings and Matching & Skill Analysis views

## Project Structure

```
AI-Recruitment-Copilot/
|
|-- app/
|   |-- main.py                 # FastAPI entry point
|   |-- routes/
|   |   |-- upload.py           # POST /api/upload/resume
|   |   |-- candidate.py        # GET/DELETE candidates, CSV export
|   |   |-- job.py              # Job posting CRUD
|   |   `-- match.py            # Candidate-job matching + skill gap
|   |-- services/
|   |   |-- parser.py           # File -> raw text
|   |   |-- extractor.py        # Raw text -> structured fields
|   |   `-- matching.py         # Match scoring + skill-gap analysis
|   |-- models/
|   |   |-- candidate.py        # SQLAlchemy ORM model
|   |   `-- job.py              # SQLAlchemy ORM model for job postings
|   |-- schemas/
|   |   |-- candidate.py        # Pydantic request/response models
|   |   `-- job.py              # Pydantic request/response models for jobs
|   |-- static/
|   |   `-- index.html          # Frontend dashboard (served at /dashboard)
|   |-- database.py             # MySQL connection (SQLAlchemy + pymysql)
|   `-- utils/
|       `-- helpers.py          # File validation, JSON helpers
|
|-- uploads/                    # Uploaded resumes land here
|-- extracted_data/             # JSON copy of each parsed profile
|-- requirements.txt
|-- .env.example
`-- README.md
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

Tables are auto-created on startup - no manual migration needed for this milestone.

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

Visit **http://localhost:8000/docs** for interactive Swagger API docs, or
**http://localhost:8000/dashboard/** for the visual dashboard (upload resumes,
view live parsing stats, browse/delete candidates, export CSV).

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/upload/resume` | Upload a resume (PDF/DOCX), parse it, save profile |
| GET | `/api/candidates/` | List all candidate profiles (paginated) |
| GET | `/api/candidates/{id}` | Get one candidate profile |
| DELETE | `/api/candidates/{id}` | Delete a candidate profile |
| GET | `/api/candidates/export/csv` | Export all candidates as CSV |
| POST | `/api/jobs/` | Create a job posting (title, required skills + level, min. experience) |
| GET | `/api/jobs/` | List all job postings |
| GET | `/api/jobs/{id}` | Get one job posting |
| DELETE | `/api/jobs/{id}` | Delete a job posting |
| GET | `/api/match/{job_id}` | Ranked candidate matches for a job (match %) |
| GET | `/api/match/{job_id}/candidate/{candidate_id}` | Per-skill gap breakdown + recommendation for one candidate/job pair |

## Frontend Dashboard

A lightweight dashboard is included at `app/static/index.html` - plain HTML/CSS/
JavaScript, no framework or build step required. FastAPI serves it directly via
a `StaticFiles` mount, so it runs off the same server as the API (no CORS setup
or separate process needed).

**Access it at:** http://localhost:8000/dashboard/

It has three tabs in the sidebar:

- **Dashboard** (Milestone 1) - upload panel, live parsing stats, and the
  candidate table with CSV export
- **Job Postings** (Milestone 2) - create/list/delete job postings with
  required skills and minimum experience
- **Matching & Skill Analysis** (Milestone 2) - pick a job to see candidates
  ranked by match %, click a candidate to see a per-skill gap breakdown
  (bars + "Has" vs "Required" level) and a text recommendation

Everything talks to the API through `fetch()` calls - no separate build step.
No React/Vue/build tooling is used intentionally, to keep the project easy to
run with zero extra setup.

## Matching & Skill Gap Analysis (`app/services/matching.py`)

**Match score** - a 0-100 score combining:
- 70% skill coverage: how many of the job's required skills the candidate
  has, with partial credit if they have a skill but at a level below what's
  required
- 30% experience fit: candidate's years vs. the job's minimum, capped at
  100% once the minimum is met (more experience doesn't inflate the score
  further)

**Skill-gap breakdown** - for each required skill, compares the candidate's
level against what's required and returns a bar percentage plus a
`meets_requirement` flag.

**Important caveat**: resumes only state whether a candidate has a skill -
not their proficiency at it. So a candidate's level per skill
(Basic/Intermediate/Advanced) is *approximated* from their overall
`total_experience_years` (3+ yrs -> Advanced, 1-3 -> Intermediate, <1 -> Basic),
applied uniformly across all their skills. This is a reasonable heuristic for
an early milestone, not a measured skill level - a good next step would be
weighting recency/context per skill instead of one blanket experience-based
level.

**Recommendations** are template-generated from the list of missing skills
(no external AI/LLM call), keeping this milestone fully offline like
Milestone 1's extraction logic.

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
    "experience": [{"title": "Software Engineer", "company": "ABC Corp", "duration": "2021-2024"}],
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
- **Education/Experience**: section-header detection + line grouping. Experience
  entries parse out title/company/duration, and duration ranges (e.g.
  `2021-2024`) are used to estimate `total_experience_years` when the resume
  doesn't state it explicitly.
- **Extraction accuracy**: % of core fields successfully populated, shown per-candidate

## Known limitations (to address in later milestones)

- No structured institution names for education entries yet (degree line is captured as-is)
- Scanned/image-based PDFs (no embedded text) aren't supported yet - would need OCR (e.g. `pytesseract`)
- Skills list is a static dictionary - consider moving to a DB table or expanding via a taxonomy (e.g. ESCO/O*NET) later
- No authentication yet on API routes
- Skill proficiency levels are approximated from total years of experience,
  not measured per-skill (see the caveat in the Matching section above)
- Match scoring is a fixed 70/30 skills/experience weighting - not yet
  configurable per job or role type

## Getting Started (for teammates)

Each person runs their own local copy - `.env` and `venv/` are intentionally
excluded from Git (see `.gitignore`), so nobody shares database passwords.

```bash
git clone https://github.com/manasvimalhotra/ai-recruitment-copilot.git
cd ai-recruitment-copilot
```

Then follow the [Setup](#setup) steps above:
1. Create a venv and `pip install -r requirements.txt`
2. `python -m spacy download en_core_web_sm`
3. Set up **your own local MySQL** and create the `recruitment_copilot` database
4. Copy `.env.example` to `.env` and fill in **your own** MySQL credentials
5. `uvicorn app.main:app --reload`

## Contributing changes (fork workflow)

This project uses a fork-based workflow - each contributor works in their own
fork rather than pushing directly to this repo.

**One-time setup, per contributor:**

1. Click **Fork** on the GitHub repo page to create your own copy.
2. Clone *your fork* (not this repo):
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-recruitment-copilot.git
   cd ai-recruitment-copilot
   ```
3. Add this repo as `upstream`, so you can pull the latest changes later:
   ```bash
   git remote add upstream https://github.com/manasvimalhotra/ai-recruitment-copilot.git
   ```
4. Follow the [Setup](#setup) steps above to get it running locally.

**Making a change:**

```bash
git checkout -b feature/your-feature-name
# ...make your changes...
git add .
git commit -m "Describe what you changed"
git push origin feature/your-feature-name
```

Then open a **Pull Request** on GitHub from your fork's branch into this
repo's `main` branch for review.

**Staying up to date with the latest changes:**

```bash
git fetch upstream
git merge upstream/main
```

## Next Milestones (per project plan)

-Milestone 3:Interview Assistance & ATS Integration
- Milestone 4: Interview scheduling & communication automation
