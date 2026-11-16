# -*- coding: utf-8 -*-
"""
Pure-Python text chunking and cosine similarity.

Replaces FAISS (and the LangChain vector-store dependency) for this demo-scale
RAG workload. Embeddings are stored as JSON in OBS and retrieved by exact
cosine similarity over the chunk vectors.
"""
import math


def chunk_text(text, chunk_size=1000, overlap=100):
    """Split text into overlapping character windows."""
    text = text or ""
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if not text:
        return []
    chunks = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(text):
        chunk = text[start : start + chunk_size]
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks


def cosine(a, b):
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def top_k(query_vec, chunk_vecs, k=4):
    """Return indices of the k most similar chunks to the query vector."""
    scored = [(cosine(query_vec, v), i) for i, v in enumerate(chunk_vecs)]
    scored.sort(key=lambda t: t[0], reverse=True)
    return [i for _, i in scored[:k]]
