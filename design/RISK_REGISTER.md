# Risk Register
## Northwind Support Copilot — v1

**Author:** Vishal Kumar Pagadala  
**Date:** June 2025  
**Version:** 1.0

---

## Risk Table

> Likelihood: High / Medium / Low  
> Impact: High / Medium / Low  
> Score: H+H = Critical · H+M or M+H = High · M+M = Medium · anything with L = Low

| ID | Risk | Likelihood | Impact | Score | Mitigation |
|----|------|-----------|--------|-------|------------|
| **R-01** ⚠️ | **Semantic retrieval fails on loosely-formatted help docs — the top-5 chunks do not contain the answer for most real questions** | **High** | **High** | **Critical** | **Run de-risk spike (Step 5): embed 15–30 real docs into Chroma, fire 8–10 real questions, measure hit-rate. Do not proceed to full build if hit-rate < 60%.** |
| R-02 | LLM generates claims not present in retrieved chunks (hallucination) | Medium | High | High | Strict system prompt: "cite only what appears in the context; if unsure, say so." Add groundedness eval gate before shipping. |
| R-03 | Document corpus is too inconsistently formatted (mix of PDFs, markdown, changelogs) for a single chunking strategy | Medium | Medium | Medium | Compare fixed-size vs. recursive chunking in Tier B spike. Pick the strategy with higher hit-rate on the same 10 questions. |
| R-04 | Support agents over-trust copilot answers without verifying source citations | Medium | High | High | UI always surfaces the source document alongside the answer. Include citation-check step in agent training. Soft launch to 3 agents before full rollout. |
| R-05 | API costs exceed $0.05/query ceiling at real usage volumes (50 queries/day/agent × 30 agents) | Low | Medium | Low | Build cost model in Tier A. Default to gpt-4o-mini. Cache embeddings. Monitor cost per query from day one with instrumented logging. |

---

## Riskiest Assumption — Full Breakdown

> The spike in Step 5 exists entirely to test this one assumption.  
> If it holds, the project is feasible. If it fails, the project design changes significantly.

### R-01: Semantic retrieval will find the correct document chunk for at least 80% of real support questions

---

### What the assumption is

When a support agent types a real question (e.g. *"What is Northwind's refund policy for annual subscriptions?"*),  
the system embeds that question using `text-embedding-3-small` and queries Chroma with cosine similarity.  

**The assumption:** the correct source document chunk appears in the top-5 results at least 80% of the time.

---

### Why it is risky

This is the single most load-bearing assumption in the entire system.

Every downstream component — the prompt assembler, the LLM, the citations, the draft reply — is only as good as what the retriever hands it. If the retriever returns the wrong chunks:

- The LLM generates a plausible-sounding but **wrong** answer
- The citations point to the **wrong** document
- The agent has **no way to know** the answer is grounded in incorrect context
- This is exactly the failure mode that burned Northwind in the previous demo

Unlike hallucination (which a good prompt can reduce), a retrieval miss is silent and upstream. The LLM cannot fix a miss — it only sees what the retriever passes it.

---

### How it could fail

| Failure Mode | Root Cause |
|---|---|
| Question uses different vocabulary than the source doc | Semantic gap: "cancel my plan" vs "terminate subscription" |
| Answer is spread across multiple chunks and no single chunk is sufficient | Chunking strategy splits the answer across boundaries |
| Source documents are scanned PDFs with poor OCR quality | Embedding quality degrades on noisy text |
| Help docs use product jargon not in the embedding model's training distribution | Domain shift in embeddings |
| The correct document simply isn't in the corpus | Corpus coverage gap |

---

### What happens if it fails

| Hit-rate result | Consequence |
|---|---|
| ≥ 80% | Proceed to full build. Retrieval is reliable. |
| 60–79% | Investigate chunking strategy. Try recursive / semantic chunking. May still be viable with tuning. |
| < 60% | **Do not build on top of this retriever.** Redesign: consider hybrid search (BM25 + semantic), smaller chunks, re-ranking, or a different embedding model. |

A hit-rate below 60% means the LLM will hallucinate on at least 40% of queries — unacceptable for a system Northwind is deploying to customer-facing agents.

---

### How the spike tests it (preview of Step 5)

```
Script:   spike/spike.py
Runtime:  ~2-3 hours
Output:   FINDINGS.md + printed table

Process:
  1. Load 15–30 real documents (PDF / markdown)
  2. Chunk with fixed-size strategy (512-token, 50-token overlap)
  3. Embed each chunk with text-embedding-3-small
  4. Store in a local Chroma collection
  5. Write 8–10 real questions that a support agent would ask
  6. For each question:
       a. Embed the question
       b. Retrieve top-5 chunks from Chroma
       c. Manually check: does any chunk contain the correct answer?
       d. Record: hit (Y) or miss (N)
  7. Calculate hit-rate = hits / total questions
  8. Write FINDINGS.md with results + recommendation
```

**Pass criteria:** hit-rate ≥ 80%  
**Do-not-proceed floor:** hit-rate < 60%

---

## Risk Matrix (visual summary)

```
IMPACT
  │
H │   R-02  R-04  │  R-01 ⚠️
  │               │
M │         R-03  │
  │               │
L │         R-05  │
  └───────────────┴──────────
       Low     Medium   High   LIKELIHOOD
```

`⚠️ R-01 is the riskiest assumption — it is Critical (High × High) and directly tested by the spike.`

---

*End of Risk Register — v1.0*