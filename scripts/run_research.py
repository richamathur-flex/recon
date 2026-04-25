"""End-to-end research pipeline runner.

Usage: python -m scripts.run_research stripe https://stripe.com Stripe
"""

import logging
import sys

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

from src.orchestrator.graph import research  # noqa: E402


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: python -m scripts.run_research <slug> <url> <name>")
        print("Example: python -m scripts.run_research stripe https://stripe.com Stripe")
        sys.exit(1)

    slug, url, name = sys.argv[1], sys.argv[2], sys.argv[3]

    print(f"\n🔍 Researching {name}...\n")
    brief = research(name, url, slug)

    print("\n" + "=" * 60)
    print("RESEARCH BRIEF")
    print("=" * 60)
    print(brief)


if __name__ == "__main__":
    main()