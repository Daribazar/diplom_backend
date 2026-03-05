"""Semantic text chunking service."""
from typing import List
import re


class SemanticChunker:
    """Chunks text based on semantic meaning."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target size for each chunk
            overlap: Overlap between chunks for context
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    async def chunk_text(self, text: str) -> List[str]:
        """
        Chunk text into semantic segments.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', text.strip())
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding paragraph exceeds chunk size
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Add overlap from end of current chunk
                    overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    # Single paragraph larger than chunk_size
                    current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
