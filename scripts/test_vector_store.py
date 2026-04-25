"""Verify the vector store abstraction works."""

import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

from sentence_transformers import SentenceTransformer  # noqa: E402

from src.core.vector_store import Point, get_vector_store  # noqa: E402


def main() -> None:
    print("Loading embedder...")
    embedder = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)

    print("Initializing vector store...")
    store = get_vector_store()

    docs = [
        ("doc1", "Linear is a project management tool for software teams"),
        ("doc2", "Stripe is a payment processing platform for online businesses"),
        ("doc3", "Notion is a workspace tool combining notes, tasks, and docs"),
    ]

    print("Embedding and upserting...")
    points = [
        Point(id=doc_id, values=embedder.encode(text).tolist(), metadata={"text": text})
        for doc_id, text in docs
    ]
    store.upsert(points)

    print("\nSearch: 'collaborative tool for engineers'")
    query = embedder.encode("collaborative tool for engineers").tolist()
    for hit in store.search(query, top_k=3):
        print(f"  {hit.score:.3f} | {hit.id} | {hit.metadata['text']}")

    print("\n✅ Vector store abstraction working")


if __name__ == "__main__":
    main()