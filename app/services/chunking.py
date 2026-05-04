import tiktoken
from typing import List


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks based on token count.
    chunk_size: 500 tokens — large enough for context, small enough for precision
    chunk_overlap: 50 tokens — ensures no context is lost between chunks
    """
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(text)
    
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = encoder.decode(chunk_tokens)
        chunks.append(chunk_text)
        
        # Move forward by chunk_size minus overlap
        start += chunk_size - chunk_overlap
        
        # Stop if remaining tokens are too small
        if start >= len(tokens):
            break
    
    return chunks