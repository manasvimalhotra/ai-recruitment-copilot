"""
main.py
-------
FastAPI application entry point for the AI Recruitment & Talent
Management Copilot -- Milestone 1: Resume Parsing & Candidate Profiling.
 
Run locally with:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
 
from app.database import init_db
from app.routes import upload, candidate, job, match
 
app = FastAPI(
    title="AI Recruitment & Talent Management Copilot",
    description="Milestone 1: Resume Parsing & Candidate Profiling. Milestone 2: Matching & Skill Analysis.",
    version="0.2.0",
)
 
# Allow the React dashboard (or any frontend) to call this API during development.
# Tighten allow_origins to your actual frontend URL before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
app.include_router(upload.router)
app.include_router(candidate.router)
app.include_router(job.router)
app.include_router(match.router)
 
# Frontend dashboard -- served at /dashboard/ so it doesn't collide with
# the existing "/" API-info route below.
app.mount("/dashboard", StaticFiles(directory="app/static", html=True), name="dashboard")
 
 
@app.on_event("startup")
def on_startup():
    """Creates DB tables if they don't already exist."""
    init_db()
 
 
@app.get("/")
def root():
    return {
        "message": "AI Recruitment & Talent Management Copilot API is running.",
        "docs": "/docs",
    }
 
 
@app.get("/health")
def health_check():
    return {"status": "ok"}
