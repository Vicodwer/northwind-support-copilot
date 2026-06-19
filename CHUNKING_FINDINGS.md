# CHUNKING_FINDINGS.md
## Chunking Strategy Comparison Spike (Tier B Stretch)

**Date:** June 19, 2026
**Author:** Vishal Kumar Pagadala
**Script:** `spike/chunking_comparison.py`  
**Full results:** `spike/results_chunking_comparison.json`

---

## 1. What This Spike Tested

The original de-risk spike (`FINDINGS.md`) used a 512-token chunk size with
documents short enough that each one collapsed into a single chunk — meaning
chunking strategy had no effect on the result. This spike fixes that gap.

**Question:** When chunking strategy actually has room to matter (i.e.
documents are forced to split into multiple chunks), does a fixed-size or a
recursive/semantic chunker retrieve more accurately?

| Strategy | How it splits |
|---|---|
| **Fixed-size** | Sliding 120-token window, 20-token overlap. Can split mid-sentence. |
| **Recursive/semantic** | Splits on paragraph/header boundaries first; only falls back to sentence-level splitting if a paragraph alone exceeds the target size. Never cuts mid-sentence. |

> Both strategies use a 120-token target — deliberately smaller than the
> 512-token size used in the main spike — specifically so each document
> splits into multiple chunks and chunking strategy can actually be observed.

---

## 2. Results

| Metric | Fixed-size | Recursive/semantic |
|---|---|---|
| Total chunks | 41 | 40 |
| Avg tokens/chunk | 99.2 | 86.0 |
| Ingest time (ms) | 857.4 | 478.4 |
| **Hit-rate** | 100.0% | 100.0% |
| Hits / total | 10/10 | 10/10 |
| Avg query latency (ms) | 12.3 | 8.9 |

**Verdict:** Tie on hit-rate — use chunk count / latency as tie-breaker.

---

## 3. Key Observations

- **Perfect Recall Accuracy:** Both strategies achieved a perfect 100% retrieval hit-rate on this test setup, meaning the core semantic meaning was captured successfully by both approaches.
- **Improved Efficiency and Speed:** The recursive strategy proved significantly faster, reducing database ingestion time by almost half (478.4 ms vs 857.4 ms) and shaving off critical query processing latency (8.9 ms vs 12.3 ms).
- **Lower Index Overheads:** Recursive chunking produced slightly fewer total chunks (40 vs 41) with a lower average token size per chunk (86.0 vs 99.2). This means it creates cleaner, less redundant storage boundaries while keeping document text together.

---

## 4. Recommendation

Recursive chunking produced a matching 100.0% hit-rate vs 100.0% for fixed-size, but it managed it with a smaller overall chunk count and roughly 27% faster search response speeds. Recommend recursive chunking for the full build: it safely preserves paragraph structural blocks (no harsh mid-sentence structural breaks), executes database updates much faster, and lowers production database embedding footprints.

---

## 5. Caveat

This comparison still uses synthetic, topically-distinct documents. As noted
in `FINDINGS.md`, a re-test on the real 15–30 document corpus (per the
project spec) is recommended before finalizing this recommendation for
production.

---

*Spike run by: Vishal Kumar Pagadala | June 19, 2026*
