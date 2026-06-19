# app/config.py
import os

# ---- DATA PATHS ----
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "spike", "docs")

# ---- MODEL CONFIGURATION ----
USE_OLLAMA = True
OLLAMA_MODEL = "phi3:latest"        # generation model (obedient for instructions)
HF_MODEL = "google/flan-t5-large"   # fallback if USE_OLLAMA is False
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ---- RETRIEVAL & CHUNKING ----
CHUNK_SIZE = 256
CHUNK_OVERLAP = 50
TOP_K = 12                          # increased for better recall

# ---- KPI TARGETS ----
TARGETS = {
    "faithfulness": 0.90,
    "answer_relevancy": 0.80,
    "context_precision": 0.70,
    "context_recall": 0.80,
}
FLOORS = {
    "faithfulness": 0.70,
    "answer_relevancy": 0.70,
    "context_precision": 0.60,
    "context_recall": 0.60,
}