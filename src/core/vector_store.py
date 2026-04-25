"""Vector store abstraction supporting multiple backends.

The VectorStore protocol defines the contract; concrete implementations
(Pinecone, Qdrant) plug in behind it. Application code depends on the
protocol, not the implementation.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Protocol

from pinecone import Pinecone, ServerlessSpec
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# Domain types
# ============================================================

class Point:
    """A single vector with metadata, ready for upsert."""

    def __init__(
        self,
        id: str,
        values: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.id = id
        self.values = values
        self.metadata = metadata or {}


class SearchResult:
    """A single hit returned by a vector search."""

    def __init__(
        self,
        id: str,
        score: float,
        metadata: dict[str, Any],
    ) -> None:
        self.id = id
        self.score = score
        self.metadata = metadata

    def __repr__(self) -> str:
        return f"SearchResult(id={self.id!r}, score={self.score:.3f})"


# ============================================================
# Protocol — the contract every backend must satisfy
# ============================================================

class VectorStore(Protocol):
    """Contract for any vector database backend."""

    def upsert(self, points: list[Point]) -> None:
        """Insert or update points."""
        ...

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Return the top_k most similar points, optionally filtered."""
        ...

    def delete(self, ids: list[str]) -> None:
        """Delete points by ID."""
        ...


# ============================================================
# Pinecone implementation
# ============================================================

class PineconeStore:
    """VectorStore backed by Pinecone Serverless."""

    def __init__(
        self,
        api_key: str,
        index_name: str,
        dimension: int = 768,
        cloud: str = "aws",
        region: str = "us-east-1",
    ) -> None:
        self._client = Pinecone(api_key=api_key)
        self._index_name = index_name
        self._dimension = dimension

        if not self._client.has_index(index_name):
            logger.info("Creating Pinecone index %s", index_name)
            self._client.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=cloud, region=region),
            )

        self._index = self._client.Index(index_name)

    def upsert(self, points: list[Point]) -> None:
        if not points:
            return
        vectors = [
            {"id": p.id, "values": p.values, "metadata": p.metadata}
            for p in points
        ]
        self._index.upsert(vectors=vectors)
        logger.info("Upserted %d points to Pinecone", len(points))

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        kwargs: dict[str, Any] = {
            "vector": query_vector,
            "top_k": top_k,
            "include_metadata": True,
        }
        if filters:
            kwargs["filter"] = filters

        response = self._index.query(**kwargs)
        return [
            SearchResult(
                id=match["id"],
                score=match["score"],
                metadata=match.get("metadata", {}),
            )
            for match in response["matches"]
        ]

    def delete(self, ids: list[str]) -> None:
        if ids:
            self._index.delete(ids=ids)


# ============================================================
# Qdrant implementation (local Docker, optional)
# ============================================================

class QdrantStore:
    """VectorStore backed by Qdrant (local or cloud)."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "recon-v1",
        dimension: int = 768,
    ) -> None:
        self._client = QdrantClient(url=url)
        self._collection = collection_name

        existing = [c.name for c in self._client.get_collections().collections]
        if collection_name not in existing:
            logger.info("Creating Qdrant collection %s", collection_name)
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )

    def _to_uuid(self, raw_id: str) -> str:
        """Qdrant requires UUIDs or ints. Hash string IDs deterministically."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_id))

    def upsert(self, points: list[Point]) -> None:
        if not points:
            return
        struct_points = [
            PointStruct(
                id=self._to_uuid(p.id),
                vector=p.values,
                payload={**p.metadata, "_original_id": p.id},
            )
            for p in points
        ]
        self._client.upsert(collection_name=self._collection, points=struct_points)
        logger.info("Upserted %d points to Qdrant", len(points))

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        # Note: simple filter support; Qdrant has richer filter syntax
        # we'll add later as needed.
        results = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=top_k,
        )
        return [
            SearchResult(
                id=str(r.payload.get("_original_id", r.id)),
                score=r.score,
                metadata={k: v for k, v in r.payload.items() if k != "_original_id"},
            )
            for r in results
        ]

    def delete(self, ids: list[str]) -> None:
        if ids:
            self._client.delete(
                collection_name=self._collection,
                points_selector=[self._to_uuid(i) for i in ids],
            )


# ============================================================
# Factory — pick the backend from config
# ============================================================

def get_vector_store() -> VectorStore:
    """Return the configured vector store backend."""
    backend = getattr(settings, "vector_store", "pinecone").lower()

    if backend == "pinecone":
        return PineconeStore(
            api_key=settings.pinecone_api_key,
            index_name=settings.pinecone_index_name,
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_region,
        )
    elif backend == "qdrant":
        return QdrantStore()
    else:
        raise ValueError(f"Unknown vector store backend: {backend}")