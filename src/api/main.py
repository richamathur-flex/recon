"""FastAPI REST interface for Recon."""

import logging

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from src.agents.web_intel import analyze_company  # noqa: E402
from src.agents.hiring import analyze_hiring  # noqa: E402
from src.orchestrator.graph import research  # noqa: E402

app = FastAPI(
    title="Recon API",
    description="Autonomous research agent — competitive intelligence on demand.",
    version="0.1.0",
)


class ResearchRequest(BaseModel):
    company_name: str
    company_url: str
    company_slug: str


class ResearchResponse(BaseModel):
    company_name: str
    brief: str


@app.get("/")
def root():
    return {"service": "recon", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/profile/{url:path}")
def get_profile(url: str, name: str = ""):
    """Run only the Web Intelligence agent."""
    try:
        profile = analyze_company(url, name or None)
        return profile.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hiring/{slug}")
def get_hiring(slug: str, name: str = ""):
    """Run only the Hiring Signals agent."""
    try:
        snapshot = analyze_hiring(slug, name or None)
        return snapshot.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research", response_model=ResearchResponse)
def post_research(req: ResearchRequest):
    """Run the full research pipeline."""
    try:
        brief = research(req.company_name, req.company_url, req.company_slug)
        return ResearchResponse(company_name=req.company_name, brief=brief)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))