"""Semantic text chunking service."""

import re
from typing import List


class SemanticChunker:
    """Split text into overlapping paragraph-based chunks."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    async def chunk_text(self, text: str) -> List[str]:
        """Return semantic chunks (paragraphs combined up to chunk_size)."""
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]

        chunks: List[str] = []
        current = ""

        for para in paragraphs:
            if current and len(current) + len(para) > self.chunk_size:
                chunks.append(current.strip())
                current = current[-self.overlap:] + "\n\n" + para
            else:
                current = f"{current}\n\n{para}" if current else para

        if current:
            chunks.append(current.strip())

        return chunks
