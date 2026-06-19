#!/usr/bin/env python3
"""
spike/spike.py
==============
De-risk spike — Northwind Support Copilot

Tests the riskiest assumption:
  "Semantic retrieval will find the correct document chunk
   for at least 80% of real support questions."

Usage:
  1. Add your 15–30 documents (.md or .txt) to spike/docs/
  2. Update TEST_QUERIES below with real questions + expected source filenames
  3. Run:  python spike/spike.py
  4. Fill in FINDINGS.md with the printed results

Runtime: ~1–3 minutes (all local, no API calls, no cost)
Cost:    $0.00 — uses a free local embedding model (all-MiniLM-L6-v2)
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
import tiktoken

load_dotenv()

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
DOCS_DIR         = Path("spike/docs")
CHUNK_SIZE       = 512          # tokens per chunk
CHUNK_OVERLAP    = 50           # token overlap between consecutive chunks
TOP_K            = 5            # chunks retrieved per query
EMBED_MODEL      = "all-MiniLM-L6-v2"   # free, local, no API key needed
EMBED_BATCH_SIZE = 50           # chunks embedded per batch
COLLECTION_NAME  = "northwind_spike"

# Load the local embedding model once (downloads ~80MB on first run)
print("🔧  Loading local embedding model (first run downloads ~80MB)...")
_model = SentenceTransformer(EMBED_MODEL)
print("✅  Model loaded\n")


# ─── TEST QUERIES ─────────────────────────────────────────────────────────────
# HOW TO FILL THIS IN:
#   - Write questions exactly as a support agent would type them
#   - Set expected_source to the filename of the document that holds the answer
#   - Partial match is fine: "refund_policy" will match "refund_policy.md"
#   - Aim for 8–10 questions covering different documents and question types
#
TEST_QUERIES = [
    {
        "question": "What is the refund policy for annual subscriptions?",
        "expected_source": "refund_policy.md",
        "notes": "Core policy — agents ask this daily"
    },
    {
        "question": "How long does a refund take to appear on a credit card?",
        "expected_source": "refund_policy.md",
        "notes": "Same doc, different angle — tests within-doc recall"
    },
    {
        "question": "How do I reset a user password in the admin panel?",
        "expected_source": "admin_guide.md",
        "notes": "Common procedural question"
    },
    {
        "question": "What happens to customer data when an account is cancelled?",
        "expected_source": "data_retention_policy.md",
        "notes": "Privacy / policy retrieval"
    },
    {
        "question": "Which integrations are available on the Pro plan?",
        "expected_source": "pricing_and_plans.md",
        "notes": "Plan feature lookup"
    },
    {
        "question": "How do I export all data before cancelling my account?",
        "expected_source": "data_export_guide.md",
        "notes": "Procedural — export workflow"
    },
    {
        "question": "What is the SLA for a critical priority support ticket?",
        "expected_source": "support_sla.md",
        "notes": "SLA policy retrieval"
    },
    {
        "question": "Can a customer switch from annual to monthly billing mid-cycle?",
        "expected_source": "billing_faq.md",
        "notes": "Edge-case billing question"
    },
    {
        "question": "How do I add a new team member to an existing workspace?",
        "expected_source": "user_management.md",
        "notes": "User management procedural"
    },
    {
        "question": "What are the minimum system requirements for the desktop app?",
        "expected_source": "system_requirements.md",
        "notes": "Technical spec retrieval"
    },
]


# ─── CHUNKING ─────────────────────────────────────────────────────────────────
def chunk_text(text: str, source_filename: str) -> list[dict]:
    """
    Split a document into overlapping token-based chunks.

    Returns a list of chunk dicts, each with:
      id, text, source, chunk_index, token_count
    """
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    start = 0
    chunk_index = 0

    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_content = enc.decode(chunk_tokens)

        chunks.append({
            "id":          f"{source_filename}::chunk_{chunk_index}",
            "text":        chunk_content,
            "source":      source_filename,
            "chunk_index": chunk_index,
            "token_count": len(chunk_tokens),
        })

        start += CHUNK_SIZE - CHUNK_OVERLAP
        chunk_index += 1

    return chunks


# ─── EMBEDDING ────────────────────────────────────────────────────────────────
def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings locally. Returns list of float vectors."""
    vectors = _model.encode(texts, show_progress_bar=False)
    return vectors.tolist()


# ─── INGESTION ────────────────────────────────────────────────────────────────
def ingest_documents(collection) -> int:
    """
    Load all .md and .txt files from DOCS_DIR.
    Chunk, embed, and store in Chroma.
    Returns total number of chunks stored.
    """
    doc_files = sorted(
        list(DOCS_DIR.glob("*.md")) + list(DOCS_DIR.glob("*.txt"))
    )

    if not doc_files:
        print(f"\n❌  No documents found in {DOCS_DIR}")
        print(f"    Run:  python spike/create_sample_docs.py")
        print(f"    Or add your own .md / .txt files to {DOCS_DIR}\n")
        return 0

    print(f"📄  Found {len(doc_files)} document(s) in {DOCS_DIR}\n")

    all_chunks: list[dict] = []

    for doc_path in doc_files:
        raw_text = doc_path.read_text(encoding="utf-8", errors="replace")
        doc_chunks = chunk_text(raw_text, doc_path.name)
        all_chunks.extend(doc_chunks)
        print(f"    {doc_path.name:<35} → {len(doc_chunks)} chunk(s)")

    total = len(all_chunks)
    print(f"\n📦  Total chunks to embed: {total}")
    print(f"🔢  Model: {EMBED_MODEL}\n")

    # Embed in batches to stay within rate limits
    num_batches = (total + EMBED_BATCH_SIZE - 1) // EMBED_BATCH_SIZE

    for batch_num, i in enumerate(range(0, total, EMBED_BATCH_SIZE), start=1):
        batch = all_chunks[i : i + EMBED_BATCH_SIZE]
        texts = [c["text"] for c in batch]

        print(f"    Embedding batch {batch_num}/{num_batches} "
              f"({len(batch)} chunks)...", end=" ", flush=True)

        embeddings = embed_texts(texts)

        collection.add(
            ids=[c["id"] for c in batch],
            embeddings=embeddings,
            documents=[c["text"] for c in batch],
            metadatas=[
                {"source": c["source"], "chunk_index": c["chunk_index"]}
                for c in batch
            ],
        )

        print("✅")
        time.sleep(0.3)   # gentle rate-limit buffer

    print(f"\n✅  Ingestion complete — {total} chunks stored in Chroma")
    return total


# ─── RETRIEVAL + EVALUATION ───────────────────────────────────────────────────
def is_hit(expected_source: str, retrieved_sources: list[str]) -> bool:
    """
    True if the expected source document appears anywhere in the top-k results.
    Uses partial, case-insensitive matching so "refund_policy" matches
    "refund_policy.md".
    """
    exp = expected_source.lower().replace(".md", "").replace(".txt", "")
    for src in retrieved_sources:
        src_clean = src.lower().replace(".md", "").replace(".txt", "")
        if exp in src_clean or src_clean in exp:
            return True
    return False


def run_queries(collection) -> list[dict]:
    """
    Embed each test question, retrieve top-k chunks, evaluate hit/miss.
    Returns list of result dicts.
    """
    results = []

    for i, query in enumerate(TEST_QUERIES, start=1):
        question        = query["question"]
        expected_source = query["expected_source"]

        # Embed the question
        q_vector = embed_texts([question])[0]

        # Query Chroma
        raw = collection.query(
            query_embeddings=[q_vector],
            n_results=TOP_K,
            include=["documents", "metadatas", "distances"],
        )

        retrieved_sources = [m["source"] for m in raw["metadatas"][0]]
        top_chunk_preview = (raw["documents"][0][0][:150] + "..."
                             if raw["documents"][0] else "—")
        hit = is_hit(expected_source, retrieved_sources)

        results.append({
            "q_num":             i,
            "question":          question,
            "expected_source":   expected_source,
            "retrieved_sources": retrieved_sources,
            "top_chunk_preview": top_chunk_preview,
            "hit":               hit,
            "notes":             query.get("notes", ""),
        })

        badge = "✅ HIT " if hit else "❌ MISS"
        print(f"  Q{i:02d} {badge} | {question[:65]}")

        time.sleep(0.1)

    return results


# ─── OUTPUT ───────────────────────────────────────────────────────────────────
def print_results_table(results: list[dict]) -> float:
    """Print the results table and return the hit-rate (0.0–1.0)."""
    hits  = sum(1 for r in results if r["hit"])
    total = len(results)
    rate  = hits / total if total else 0.0

    print("\n" + "=" * 80)
    print("  SPIKE RESULTS — Retrieval Hit-Rate Test")
    print("=" * 80)

    header = f"{'#':<4} {'Question':<48} {'Expected Source':<26} {'Hit?'}"
    print(header)
    print("-" * 80)

    for r in results:
        q   = (r["question"][:46] + "..") if len(r["question"]) > 46 else r["question"]
        src = r["expected_source"][:24]
        hit = "Y  ✅" if r["hit"] else "N  ❌"
        print(f"{r['q_num']:<4} {q:<48} {src:<26} {hit}")

    print("-" * 80)
    print(f"\n  HIT RATE :  {hits} / {total}  =  {rate*100:.0f}%")

    if rate >= 0.80:
        verdict = "✅  PASS — retrieval meets the ≥80% target. Proceed to full build."
    elif rate >= 0.60:
        verdict = ("⚠️   MARGINAL — between 60-79%. Investigate chunking strategy "
                   "before proceeding (see Tier B spike).")
    else:
        verdict = ("❌  FAIL — below 60% floor. Redesign retrieval before building "
                   "the full pipeline. Consider hybrid search, smaller chunks, or "
                   "a different embedding model.")

    print(f"\n  VERDICT :  {verdict}")
    print("=" * 80)

    return rate


def save_results(results: list[dict], hit_rate: float) -> None:
    """Save full results to spike/results.json for FINDINGS.md reference."""
    output = {
        "config": {
            "chunk_size":    CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "top_k":         TOP_K,
            "embed_model":   EMBED_MODEL,
        },
        "hit_rate":    round(hit_rate * 100, 1),
        "hits":        sum(1 for r in results if r["hit"]),
        "total":       len(results),
        "results":     results,
    }
    out_path = Path("spike/results.json")
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n💾  Full results saved to {out_path}")
    print(f"    Use these numbers when filling in FINDINGS.md")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main() -> None:
    chroma_client = chromadb.EphemeralClient()   # in-memory; fresh each run

    # Drop and recreate the collection so each run is clean
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print("\n🚀  Northwind Support Copilot — De-risk Spike")
    print(f"    Chunk: {CHUNK_SIZE} tokens | Overlap: {CHUNK_OVERLAP} | Top-k: {TOP_K}")

    # ── Phase 1: Ingest ──────────────────────────────────────────────────────
    print("\n── PHASE 1: INGESTION ──────────────────────────────────────────────────")
    total_chunks = ingest_documents(collection)
    if total_chunks == 0:
        return

    # ── Phase 2: Retrieval test ───────────────────────────────────────────────
    print("\n── PHASE 2: RETRIEVAL TEST ─────────────────────────────────────────────")
    results = run_queries(collection)

    # ── Phase 3: Output ───────────────────────────────────────────────────────
    print("\n── PHASE 3: RESULTS ────────────────────────────────────────────────────")
    hit_rate = print_results_table(results)
    save_results(results, hit_rate)


if __name__ == "__main__":
    main()