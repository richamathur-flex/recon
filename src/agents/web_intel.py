"""Web Intelligence Agent — extracts a structured profile from a company homepage."""

import json
import logging

import httpx
from selectolax.parser import HTMLParser

from src.llm import chat_json
from src.schemas import CompanyProfile

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a competitive intelligence analyst. Given the text content
of a company's homepage, extract a structured profile.

Return a JSON object with exactly these keys:
- company_name (string)
- value_proposition (string, one clear sentence)
- target_customer (string, who they sell to)
- key_features (array of 3-5 strings, each a short feature description)
- positioning_keywords (array of 3-5 strings, marketing keywords they use)
- source_url (string, echo back the URL provided)

Be factual. Only include information actually present in the page text.
If a field is unclear, write "unclear" rather than inventing details."""


def _fetch_html(url: str, timeout: int = 30) -> str:
    """Fetch raw HTML for a URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Recon Research Agent; "
            "https://github.com/richamathur-flex/recon)"
        )
    }
    response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    return response.text


def _extract_clean_text(html: str, max_chars: int = 8000) -> str:
    """Strip HTML tags, scripts, styles. Return clean text."""
    tree = HTMLParser(html)

    # Remove noise
    for tag in tree.css("script, style, nav, footer, noscript"):
        tag.decompose()

    text = tree.body.text(separator="\n", strip=True) if tree.body else ""

    # Collapse repeated whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = "\n".join(lines)

    return cleaned[:max_chars]


def analyze_company(url: str, company_name: str | None = None) -> CompanyProfile:
    """Fetch a company's homepage and extract a structured profile.

    Args:
        url: Homepage URL (e.g., "https://linear.app")
        company_name: Optional hint for the company name. If omitted,
            the LLM infers it from the page.

    Returns:
        Validated CompanyProfile object.
    """
    logger.info("Analyzing %s", url)

    html = _fetch_html(url)
    page_text = _extract_clean_text(html)

    user_message = (
        f"URL: {url}\n"
        f"Hint (company name): {company_name or 'unknown — please infer'}\n\n"
        f"PAGE CONTENT:\n{page_text}"
    )

    raw_json = chat_json(system=SYSTEM_PROMPT, user=user_message)
    data = json.loads(raw_json)

    # Pydantic validation — raises if shape is wrong
    profile = CompanyProfile(**data)

    logger.info("Extracted profile for %s", profile.company_name)
    return profile