#!/usr/bin/env python3
"""
spike/chunking_comparison.py
=============================
Tier B stretch spike — compares two chunking strategies on the same corpus
and the same test queries.

Strategy A — FIXED-SIZE:    sliding window, splits mid-sentence if needed.
Strategy B — RECURSIVE:     respects paragraph/sentence boundaries; only
                              splits a paragraph if it alone exceeds the
                              target chunk size.

IMPORTANT — why CHUNK_SIZE is smaller here than in spike.py:
  In the main spike (spike.py), each sample document fit inside a single
  512-token chunk, so chunking strategy couldn't make any difference —
  there was nothing to chunk. To actually exercise chunking behavior, this
  script uses a much smaller target size (120 tokens) so each document
  splits into multiple chunks. This is a deliberate test-design choice,
  documented in CHUNKING_FINDINGS.md.

Usage:
    python spike/chunking_comparison.py

No new dependencies required — reuses tiktoken, chromadb, sentence-transformers
already installed for spike.py.
"""

import json
import re
import time
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
import tiktoken

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
DOCS_DIR      = Path("spike/docs")
TARGET_SIZE   = 120     # tokens — deliberately small to force multi-chunking
OVERLAP       = 20      # tokens (fixed-size strategy only)
TOP_K         = 5
EMBED_MODEL   = "all-MiniLM-L6-v2"

print("🔧  Loading local embedding model...")
_model = SentenceTransformer(EMBED_MODEL)
_enc = tiktoken.get_encoding("cl100k_base")
print("✅  Model loaded\n")


# Reuse the same test queries as the main spike, for a fair comparison.
TEST_QUERIES = [
    {"question": "What is the refund policy for annual subscriptions?",          "expected_source": "refund_policy.md"},
    {"question": "How long does a refund take to appear on a credit card?",       "expected_source": "refund_policy.md"},
    {"question": "How do I reset a user password in the admin panel?",            "expected_source": "admin_guide.md"},
    {"question": "What happens to customer data when an account is cancelled?",   "expected_source": "data_retention_policy.md"},
    {"question": "Which integrations are available on the Pro plan?",             "expected_source": "pricing_and_plans.md"},
    {"question": "How do I export all data before cancelling my account?",        "expected_source": "data_export_guide.md"},
    {"question": "What is the SLA for a critical priority support ticket?",       "expected_source": "support_sla.md"},
    {"question": "Can a customer switch from annual to monthly billing mid-cycle?","expected_source": "billing_faq.md"},
    {"question": "How do I add a new team member to an existing workspace?",      "expected_source": "user_management.md"},
    {"question": "What are the minimum system requirements for the desktop app?", "expected_source": "system_requirements.md"},
]


# ─── STRATEGY A: FIXED-SIZE CHUNKING ──────────────────────────────────────────
def chunk_fixed(text: str, source: str) -> list[dict]:
    """
    Sliding-window token chunking. Splits at fixed token boundaries,
    regardless of sentence or paragraph structure. Simple, fast, but can
    cut a sentence (or an answer) in half.
    """
    tokens = _enc.encode(text)
    chunks = []
    start = 0
    idx = 0

    while start < len(tokens):
        end = min(start + TARGET_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append({
            "id":     f"{source}::fixed::{idx}",
            "text":   _enc.decode(chunk_tokens),
            "source": source,
            "tokens": len(chunk_tokens),
        })
        start += TARGET_SIZE - OVERLAP
        idx += 1

    return chunks


# ─── STRATEGY B: RECURSIVE / SEMANTIC CHUNKING ────────────────────────────────
def split_sentences(text: str) -> list[str]:
    """Split text into sentences on '.', '!', '?' followed by whitespace."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in sentences if s.strip()]


def chunk_recursive(text: str, source: str) -> list[dict]:
    """
    Recursive/semantic chunking:
      1. Split on paragraph breaks (blank lines / markdown headers) first.
      2. Greedily merge consecutive paragraphs into a chunk until adding the
         next paragraph would exceed TARGET_SIZE tokens.
      3. If a single paragraph alone exceeds TARGET_SIZE, fall back to
         splitting it by sentences (never mid-sentence).

    This preserves semantic units (a policy clause, a step, a Q&A pair)
    instead of cutting at an arbitrary token count.
    """
    # Split on blank lines AND markdown headers, keep both as boundaries
    raw_paragraphs = re.split(r"\n\s*\n|\n(?=#{1,3}\s)", text.strip())
    paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]

    chunks = []
    buffer = ""
    buffer_tokens = 0
    idx = 0

    def flush():
        nonlocal buffer, buffer_tokens, idx
        if buffer.strip():
            chunks.append({
                "id":     f"{source}::recursive::{idx}",
                "text":   buffer.strip(),
                "source": source,
                "tokens": buffer_tokens,
            })
            idx += 1
        buffer = ""
        buffer_tokens = 0

    for para in paragraphs:
        para_tokens = len(_enc.encode(para))

        if para_tokens > TARGET_SIZE:
            # Paragraph itself is too big — flush what we have, then
            # split this paragraph by sentences instead of cutting blindly.
            flush()
            sent_buffer = ""
            sent_tokens = 0
            for sent in split_sentences(para):
                s_tok = len(_enc.encode(sent))
                if sent_tokens + s_tok > TARGET_SIZE and sent_buffer:
                    chunks.append({
                        "id":     f"{source}::recursive::{idx}",
                        "text":   sent_buffer.strip(),
                        "source": source,
                        "tokens": sent_tokens,
                    })
                    idx += 1
                    sent_buffer = ""
                    sent_tokens = 0
                sent_buffer += " " + sent
                sent_tokens += s_tok
            if sent_buffer.strip():
                chunks.append({
                    "id":     f"{source}::recursive::{idx}",
                    "text":   sent_buffer.strip(),
                    "source": source,
                    "tokens": sent_tokens,
                })
                idx += 1
            continue

        if buffer_tokens + para_tokens > TARGET_SIZE and buffer:
            flush()

        buffer += "\n\n" + para
        buffer_tokens += para_tokens

    flush()
    return chunks


# ─── SHARED: EMBED, INGEST, QUERY ─────────────────────────────────────────────
def embed(texts: list[str]) -> list[list[float]]:
    return _model.encode(texts, show_progress_bar=False).tolist()


def build_collection(chroma_client, name: str, chunker) -> tuple:
    """Chunk all docs with the given chunker, embed, store in a fresh collection."""
    doc_files = sorted(list(DOCS_DIR.glob("*.md")) + list(DOCS_DIR.glob("*.txt")))

    try:
        chroma_client.delete_collection(name)
    except Exception:
        pass
    collection = chroma_client.create_collection(name=name, metadata={"hnsw:space": "cosine"})

    all_chunks = []
    for doc_path in doc_files:
        text = doc_path.read_text(encoding="utf-8", errors="replace")
        all_chunks.extend(chunker(text, doc_path.name))

    t0 = time.perf_counter()
    vectors = embed([c["text"] for c in all_chunks])
    ingest_ms = (time.perf_counter() - t0) * 1000

    collection.add(
        ids=[c["id"] for c in all_chunks],
        embeddings=vectors,
        documents=[c["text"] for c in all_chunks],
        metadatas=[{"source": c["source"]} for c in all_chunks],
    )

    avg_tokens = sum(c["tokens"] for c in all_chunks) / len(all_chunks) if all_chunks else 0
    stats = {
        "total_chunks": len(all_chunks),
        "avg_tokens_per_chunk": round(avg_tokens, 1),
        "ingest_ms": round(ingest_ms, 1),
    }
    return collection, stats


def is_hit(expected_source: str, retrieved_sources: list[str]) -> bool:
    exp = expected_source.lower().replace(".md", "")
    return any(exp in s.lower().replace(".md", "") for s in retrieved_sources)


def evaluate(collection) -> dict:
    hits = 0
    latencies = []

    for q in TEST_QUERIES:
        t0 = time.perf_counter()
        q_vec = embed([q["question"]])[0]
        raw = collection.query(query_embeddings=[q_vec], n_results=TOP_K,
                               include=["metadatas"])
        latencies.append((time.perf_counter() - t0) * 1000)

        sources = [m["source"] for m in raw["metadatas"][0]]
        if is_hit(q["expected_source"], sources):
            hits += 1

    return {
        "hits": hits,
        "total": len(TEST_QUERIES),
        "hit_rate": round(100 * hits / len(TEST_QUERIES), 1),
        "avg_query_latency_ms": round(sum(latencies) / len(latencies), 1),
    }


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    chroma_client = chromadb.EphemeralClient()

    print("🚀  Chunking Strategy Comparison Spike")
    print(f"    Target chunk size: {TARGET_SIZE} tokens (deliberately small — see script docstring)\n")

    print("── Building Strategy A: FIXED-SIZE ─────────────────────────────────")
    coll_a, stats_a = build_collection(chroma_client, "strategy_fixed", chunk_fixed)
    print(f"    {stats_a['total_chunks']} chunks, avg {stats_a['avg_tokens_per_chunk']} tokens/chunk")

    print("\n── Building Strategy B: RECURSIVE / SEMANTIC ───────────────────────")
    coll_b, stats_b = build_collection(chroma_client, "strategy_recursive", chunk_recursive)
    print(f"    {stats_b['total_chunks']} chunks, avg {stats_b['avg_tokens_per_chunk']} tokens/chunk")

    print("\n── Running test queries against BOTH strategies ────────────────────")
    results_a = evaluate(coll_a)
    results_b = evaluate(coll_b)

    print("\n" + "=" * 78)
    print("  CHUNKING STRATEGY COMPARISON")
    print("=" * 78)
    print(f"{'Metric':<28} {'Fixed-size':<22} {'Recursive/semantic'}")
    print("-" * 78)
    print(f"{'Total chunks':<28} {stats_a['total_chunks']:<22} {stats_b['total_chunks']}")
    print(f"{'Avg tokens/chunk':<28} {stats_a['avg_tokens_per_chunk']:<22} {stats_b['avg_tokens_per_chunk']}")
    print(f"{'Ingest time (ms)':<28} {stats_a['ingest_ms']:<22} {stats_b['ingest_ms']}")
    print(f"{'Hit rate':<28} {str(results_a['hit_rate'])+'%':<22} {str(results_b['hit_rate'])+'%'}")
    print(f"{'Hits':<28} {str(results_a['hits'])+'/'+str(results_a['total']):<22} {str(results_b['hits'])+'/'+str(results_b['total'])}")
    print(f"{'Avg query latency (ms)':<28} {results_a['avg_query_latency_ms']:<22} {results_b['avg_query_latency_ms']}")
    print("-" * 78)

    if results_a["hit_rate"] > results_b["hit_rate"]:
        verdict = "Fixed-size wins on hit-rate."
    elif results_b["hit_rate"] > results_a["hit_rate"]:
        verdict = "Recursive/semantic wins on hit-rate."
    else:
        verdict = "Tie on hit-rate — use chunk count / latency as tie-breaker."

    print(f"\n  VERDICT: {verdict}")
    print("=" * 78)

    output = {
        "config": {"target_size": TARGET_SIZE, "overlap_fixed_only": OVERLAP, "top_k": TOP_K},
        "fixed":     {**stats_a, **results_a},
        "recursive": {**stats_b, **results_b},
        "verdict":   verdict,
    }
    out_path = Path("spike/results_chunking_comparison.json")
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n💾  Full results saved to {out_path}")
    print("    Use these numbers when filling in CHUNKING_FINDINGS.md")


if __name__ == "__main__":
    main()