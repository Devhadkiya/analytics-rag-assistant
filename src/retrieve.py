"""Retrieval: embed the question, pull the nearest chunks, drop weak hits."""
from __future__ import annotations

import chromadb
from openai import OpenAI

from config import (CHROMA_DIR, COLLECTION, EMBEDDING_MODEL, MIN_SIMILARITY,
                    OPENAI_API_KEY, TOP_K)


class NotIndexed(RuntimeError):
    """The corpus has not been indexed yet."""


def get_collection():
    try:
        return chromadb.PersistentClient(path=CHROMA_DIR).get_collection(COLLECTION)
    except Exception as exc:                      # chroma raises several types
        raise NotIndexed(
            f"No index found at {CHROMA_DIR!r}. Run `python src/ingest.py` first."
        ) from exc


def retrieve(question: str, k: int = TOP_K,
             min_similarity: float = MIN_SIMILARITY) -> list[dict]:
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    collection = get_collection()                 # fails early with a clear message
    client = OpenAI(api_key=OPENAI_API_KEY)
    qvec = client.embeddings.create(model=EMBEDDING_MODEL,
                                    input=[question]).data[0].embedding

    res = collection.query(query_embeddings=[qvec], n_results=k)

    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0],
                               res["distances"][0]):
        similarity = 1.0 - dist          # cosine space
        if similarity < min_similarity:
            continue                     # plausible-looking but not relevant
        hits.append({"text": doc, "source": meta["source"],
                     "heading": meta["heading"],
                     "similarity": round(similarity, 3)})
    return hits
