"""Embed and index the saved company profiles into the vector store."""

import json
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

from sentence_transformers import SentenceTransformer  # noqa: E402

from src.core.chunking import chunk_text  # noqa: E402
from src.core.vector_store import Point, get_vector_store  # noqa: E402


FIXTURES_PATH = Path("tests/fixtures/sample_profiles.json")


def profile_to_text(profile: dict) -> str:
    """Convert a structured profile into searchable text."""
    return (
        f"{profile['company_name']}. "
        f"Value: {profile['value_proposition']} "
        f"Customer: {profile['target_customer']}. "
        f"Features: {' '.join(profile['key_features'])}. "
        f"Keywords: {', '.join(profile['positioning_keywords'])}."
    )


def main() -> None:
    print(f"Loading fixtures from {FIXTURES_PATH}...")
    profiles = json.loads(FIXTURES_PATH.read_text())

    print("Loading embedder...")
    embedder = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)

    print("Initializing vector store...")
    store = get_vector_store()

    points: list[Point] = []
    for slug, profile in profiles.items():
        text = profile_to_text(profile)
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            points.append(Point(
                id=f"{slug}-chunk-{i}",
                values=embedder.encode(chunk).tolist(),
                metadata={
                    "company": profile["company_name"],
                    "slug": slug,
                    "chunk_index": i,
                    "text": chunk,
                    "source_url": profile["source_url"],
                },
            ))

    print(f"Upserting {len(points)} chunks...")
    store.upsert(points)

    # Test queries
    print("\n" + "=" * 60)
    print("TEST QUERIES")
    print("=" * 60)

    test_queries = [
        "AI agents and automation",
        "developer tools for cloud",
        "no-code workflows",
    ]

    for q in test_queries:
        print(f"\nQuery: {q!r}")
        query_vec = embedder.encode(q).tolist()
        hits = store.search(query_vec, top_k=3)
        for hit in hits:
            print(f"  {hit.score:.3f} | {hit.metadata['company']:12} | {hit.metadata['text'][:80]}...")

    print("\n✅ All profiles indexed and queryable")


if __name__ == "__main__":
    main()