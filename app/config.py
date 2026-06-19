# app/config.py
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "spike", "docs")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
USE_OLLAMA = True
OLLAMA_MODEL = "phi3:latest"
HF_MODEL = "google/flan-t5-large"   # fallback if not using Ollama
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
TOP_K = 4

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