# common/config.py

# ---------------------------
# RAG / Shubham Chat Bot
# ---------------------------
DOCS_PATH = "docs/shubham_profile.docx"  # your single DOCX

# Chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# Embeddings (set OPENAI_API_KEY in env)
USE_OPENAI_EMBEDDINGS = True
OPENAI_EMBED_MODEL = "text-embedding-3-small"
EMBED_BATCH_SIZE = 64
RAG_CACHE_DIR = "rag_cache"

# Audio (constants used by the agent)
USER_AUDIO_SAMPLE_RATE = 48000
USER_AUDIO_SECS_PER_CHUNK = 0.05
AGENT_AUDIO_SAMPLE_RATE = 16000
