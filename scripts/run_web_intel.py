"""CLI to test the Web Intelligence Agent.

Usage from project root:
    python scripts/run_web_intel.py https://linear.app Linear
"""

import json
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

from src.agents.web_intel import analyze_company  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_web_intel.py <url> [company_name]")
        sys.exit(1)

    url = sys.argv[1]
    company_name = sys.argv[2] if len(sys.argv) > 2 else None

    profile = analyze_company(url=url, company_name=company_name)

    print("\n" + "=" * 60)
    print("EXTRACTED PROFILE")
    print("=" * 60)
    print(json.dumps(profile.model_dump(), indent=2))


if __name__ == "__main__":
    main()