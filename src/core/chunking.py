"""Simple semantic chunking for documents."""

import re


def chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks at sentence boundaries.

    Tries to split on sentence endings; falls back to hard char limit.
    """
    if len(text) <= max_chars:
        return [text]

    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            # Start new chunk with overlap from previous
            if chunks and overlap > 0:
                tail = chunks[-1][-overlap:]
                current = f"{tail} {sentence}"
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks