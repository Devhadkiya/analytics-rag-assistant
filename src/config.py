"""Configuration, loaded from the environment."""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

CORPUS_DIR = os.getenv("CORPUS_DIR", "data/handbook")
CHROMA_DIR = os.getenv("CHROMA_DIR", ".chroma")
COLLECTION = "handbook"

# Chunking. Small chunks retrieve precisely but lose the context a definition
# depends on; large chunks keep context but dilute the embedding. The overlap
# is what stops a definition being split away from its own heading.
CHUNK_TOKENS = int(os.getenv("CHUNK_TOKENS", "220"))
CHUNK_OVERLAP_TOKENS = int(os.getenv("CHUNK_OVERLAP_TOKENS", "60"))

TOP_K = int(os.getenv("TOP_K", "4"))
# Below this cosine similarity the assistant says it does not know rather than
# answering from the closest-but-irrelevant chunk.
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.25"))
