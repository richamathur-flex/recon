"""Hiring Signals Agent — analyzes a company's job postings."""

import json
import logging
from typing import Any

import httpx

from src.llm import chat_json
from src.schemas import HiringSnapshot

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a workforce intelligence analyst. Given a list of a company's
open job postings, extract strategic signals.

Return a JSON object with exactly these keys:
- company_name (string)
- total_openings (integer)
- top_departments (array of 3-5 strings, e.g. "Engineering", "Sales")
- key_skills (array of 5-8 strings — technologies/skills appearing repeatedly)
- strategic_signal (string, one sentence — what does the hiring pattern reveal about strategy?)
- locations (array of up to 5 most common locations)

Be analytical. The strategic_signal field is the most important — derive a real insight,
not a generic statement."""


def _try_greenhouse(slug: str) -> list[dict[str, Any]] | None:
    """Try Greenhouse public API. Returns list of jobs or None if not on Greenhouse."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        r = httpx.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get("jobs", [])
    except Exception as e:
        logger.debug("Greenhouse fetch failed for %s: %s", slug, e)
    return None


def _try_lever(slug: str) -> list[dict[str, Any]] | None:
    """Try Lever public API. Returns list of jobs or None if not on Lever."""
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        r = httpx.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.debug("Lever fetch failed for %s: %s", slug, e)
    return None


def _normalize_jobs(jobs: list[dict], source: str) -> list[dict[str, str]]:
    """Normalize jobs from any board into a common shape."""
    normalized: list[dict[str, str]] = []

    if source == "greenhouse":
        for j in jobs:
            normalized.append({
                "title": j.get("title", ""),
                "location": j.get("location", {}).get("name", "Remote"),
                "department": (j.get("departments") or [{}])[0].get("name", "Other"),
            })
    elif source == "lever":
        for j in jobs:
            normalized.append({
                "title": j.get("text", ""),
                "location": j.get("categories", {}).get("location", "Remote"),
                "department": j.get("categories", {}).get("team", "Other"),
            })

    return normalized


def fetch_jobs(company_slug: str) -> tuple[list[dict[str, str]], str]:
    """Try Greenhouse, then Lever. Returns (jobs, source_used)."""
    jobs = _try_greenhouse(company_slug)
    if jobs is not None:
        return _normalize_jobs(jobs, "greenhouse"), "greenhouse"

    jobs = _try_lever(company_slug)
    if jobs is not None:
        return _normalize_jobs(jobs, "lever"), "lever"

    return [], "none"


def analyze_hiring(
    company_slug: str,
    company_name: str | None = None,
) -> HiringSnapshot:
    """Fetch and analyze a company's hiring signals.

    Args:
        company_slug: The company's identifier on Greenhouse/Lever
            (e.g., "stripe", "notion", "vercel"). Often the company name lowercased.
        company_name: Display name. Inferred if missing.

    Returns:
        Validated HiringSnapshot.
    """
    logger.info("Analyzing hiring for %s", company_slug)

    jobs, source = fetch_jobs(company_slug)

    if not jobs:
        logger.warning("No jobs found for %s on Greenhouse or Lever", company_slug)
        return HiringSnapshot(
            company_name=company_name or company_slug.title(),
            total_openings=0,
            top_departments=[],
            key_skills=[],
            strategic_signal="No public job board detected.",
            locations=[],
            source="none",
        )

    logger.info("Found %d jobs on %s", len(jobs), source)

    # Build a compact summary for the LLM (don't dump all 200 jobs raw)
    job_lines = [f"- {j['title']} ({j['department']}, {j['location']})" for j in jobs[:80]]
    job_summary = "\n".join(job_lines)

    user_message = (
        f"Company: {company_name or company_slug}\n"
        f"Source: {source}\n"
        f"Total openings: {len(jobs)}\n\n"
        f"JOBS:\n{job_summary}"
    )

    raw = chat_json(system=SYSTEM_PROMPT, user=user_message)
    data = json.loads(raw)
    data["source"] = source

    snapshot = HiringSnapshot(**data)
    logger.info("Hiring snapshot for %s: %d openings", snapshot.company_name, snapshot.total_openings)
    return snapshot