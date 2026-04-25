"""CLI to test the Hiring Signals Agent.

Usage: python -m scripts.run_hiring stripe Stripe
"""

import json
import logging
import sys

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

from src.agents.hiring import analyze_hiring  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.run_hiring <slug> [company_name]")
        print("Try slugs: stripe, notion, vercel, supabase, gitlab, brex, ramp")
        sys.exit(1)

    slug = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None

    snapshot = analyze_hiring(slug, name)

    print("\n" + "=" * 60)
    print("HIRING SNAPSHOT")
    print("=" * 60)
    print(json.dumps(snapshot.model_dump(), indent=2))


if __name__ == "__main__":
    main()