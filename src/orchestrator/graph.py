"""LangGraph orchestrator — runs all agents and synthesizes a brief."""

from __future__ import annotations

import asyncio
import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.hiring import analyze_hiring
from src.agents.web_intel import analyze_company
from src.llm import chat_json
from src.schemas import CompanyProfile, HiringSnapshot

logger = logging.getLogger(__name__)


# ============================================================
# Shared graph state
# ============================================================

class ResearchState(TypedDict, total=False):
    company_name: str
    company_url: str
    company_slug: str
    web_profile: CompanyProfile | None
    hiring_snapshot: HiringSnapshot | None
    final_report: str


# ============================================================
# Nodes
# ============================================================

def web_intel_node(state: ResearchState) -> dict:
    """Run Web Intelligence Agent."""
    logger.info("→ Web Intel node")
    try:
        profile = analyze_company(state["company_url"], state["company_name"])
        return {"web_profile": profile}
    except Exception as e:
        logger.error("Web Intel failed: %s", e)
        return {"web_profile": None}


def hiring_node(state: ResearchState) -> dict:
    """Run Hiring Signals Agent."""
    logger.info("→ Hiring node")
    try:
        snapshot = analyze_hiring(state["company_slug"], state["company_name"])
        return {"hiring_snapshot": snapshot}
    except Exception as e:
        logger.error("Hiring failed: %s", e)
        return {"hiring_snapshot": None}


def synthesizer_node(state: ResearchState) -> dict:
    """Combine agent outputs into a final research brief."""
    logger.info("→ Synthesizer node")

    profile = state.get("web_profile")
    hiring = state.get("hiring_snapshot")

    profile_block = (
        f"VALUE PROPOSITION: {profile.value_proposition}\n"
        f"TARGET CUSTOMER: {profile.target_customer}\n"
        f"KEY FEATURES: {', '.join(profile.key_features)}\n"
        f"POSITIONING: {', '.join(profile.positioning_keywords)}\n"
        if profile else "No web intelligence available.\n"
    )

    hiring_block = (
        f"OPENINGS: {hiring.total_openings}\n"
        f"TOP DEPARTMENTS: {', '.join(hiring.top_departments)}\n"
        f"KEY SKILLS: {', '.join(hiring.key_skills)}\n"
        f"STRATEGIC SIGNAL: {hiring.strategic_signal}\n"
        if hiring and hiring.total_openings > 0
        else "No hiring data available.\n"
    )

    system = (
        "You are a senior research analyst. Given multi-source intelligence on a company, "
        "produce a concise research brief in Markdown format. "
        "Structure: ## Executive Summary (2 sentences), ## Positioning (3 bullets), "
        "## Hiring & Strategic Signals (3 bullets), ## Bottom Line (1 sentence). "
        "Return JSON with one key 'brief' containing the Markdown string."
    )

    user = (
        f"COMPANY: {state['company_name']}\n\n"
        f"--- WEB INTEL ---\n{profile_block}\n"
        f"--- HIRING ---\n{hiring_block}"
    )

    raw = chat_json(system=system, user=user)
    import json
    data = json.loads(raw)
    return {"final_report": data.get("brief", "Synthesis failed.")}


# ============================================================
# Build the graph
# ============================================================

def build_graph():
    g = StateGraph(ResearchState)

    g.add_node("web_intel", web_intel_node)
    g.add_node("hiring", hiring_node)
    g.add_node("synthesizer", synthesizer_node)

    # Fan-out from START to both agents (parallel)
    g.add_edge(START, "web_intel")
    g.add_edge(START, "hiring")

    # Fan-in to synthesizer
    g.add_edge("web_intel", "synthesizer")
    g.add_edge("hiring", "synthesizer")

    g.add_edge("synthesizer", END)

    return g.compile()


# Singleton
_GRAPH = None

def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def research(company_name: str, company_url: str, company_slug: str) -> str:
    """Run the full research pipeline. Returns the Markdown brief."""
    graph = get_graph()
    final_state = graph.invoke({
        "company_name": company_name,
        "company_url": company_url,
        "company_slug": company_slug,
    })
    return final_state.get("final_report", "No report generated.")