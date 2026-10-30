"""Ingest the corpus: read -> chunk -> embed -> store in Chroma.

Chunks are cut on token count with overlap, and every chunk carries the
heading it came from. Carrying the heading is what keeps "Definition: a user
is active if ..." attached to the metric it defines when the chunk boundary
falls in the wrong place.
"""
from __future__ import annotations

import argparse
import pathlib
import re

import chromadb
import tiktoken
from openai import OpenAI

from config import (CHROMA_DIR, CHUNK_OVERLAP_TOKENS, CHUNK_TOKENS, COLLECTION,
                    CORPUS_DIR, EMBEDDING_MODEL, OPENAI_API_KEY)

ENC = tiktoken.get_encoding("cl100k_base")


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) pairs on '## ' headings."""
    parts = re.split(r"^##\s+(.+)$", text, flags=re.M)
    if len(parts) == 1:
        return [("", text.strip())]
    out = []
    for i in range(1, len(parts), 2):
        out.append((parts[i].strip(), parts[i + 1].strip()))
    return out


def chunk_tokens(text: str, size: int, overlap: int) -> list[str]:
    toks = ENC.encode(text)
    if len(toks) <= size:
        return [text]
    chunks, start = [], 0
    while start < len(toks):
        window = toks[start:start + size]
        chunks.append(ENC.decode(window))
        if start + size >= len(toks):
            break
        start += size - overlap
    return chunks


def build_chunks(corpus_dir: str) -> list[dict]:
    records = []
    for path in sorted(pathlib.Path(corpus_dir).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for heading, body in split_sections(text):
            for i, piece in enumerate(chunk_tokens(body, CHUNK_TOKENS,
                                                   CHUNK_OVERLAP_TOKENS)):
                # Prepend the heading so the chunk is self-describing.
                content = f"{heading}\n\n{piece}".strip() if heading else piece
                records.append({
                    "id": f"{path.stem}::{heading or 'root'}::{i}",
                    "text": content,
                    "source": path.name,
                    "heading": heading,
                })
    return records


def embed(client: OpenAI, texts: list[str]) -> list[list[float]]:
    out = []
    for i in range(0, len(texts), 64):           # batch to stay under limits
        resp = client.embeddings.create(model=EMBEDDING_MODEL,
                                        input=texts[i:i + 64])
        out.extend(d.embedding for d in resp.data)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=CORPUS_DIR)
    args = ap.parse_args()

    if not OPENAI_API_KEY:
        raise SystemExit("OPENAI_API_KEY is not set. Copy .env.example to .env.")

    records = build_chunks(args.corpus)
    if not records:
        raise SystemExit(f"No .md files found in {args.corpus}")

    client = OpenAI(api_key=OPENAI_API_KEY)
    vectors = embed(client, [r["text"] for r in records])

    chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    # Cosine, so similarity = 1 - distance and the threshold in config means
    # what it says.
    try:
        chroma.delete_collection(COLLECTION)
    except Exception:
        pass
    coll = chroma.create_collection(COLLECTION,
                                    metadata={"hnsw:space": "cosine"})
    coll.add(
        ids=[r["id"] for r in records],
        embeddings=vectors,
        documents=[r["text"] for r in records],
        metadatas=[{"source": r["source"], "heading": r["heading"]}
                   for r in records],
    )
    print(f"Indexed {len(records)} chunks from {args.corpus} into {CHROMA_DIR}")


if __name__ == "__main__":
    main()
