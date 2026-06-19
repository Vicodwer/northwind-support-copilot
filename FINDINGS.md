# FINDINGS.md
## De-risk Spike — Northwind Support Copilot

**Date:** June 2025  
**Author:** Vishal Kumar Pagadala 
**Spike script:** `spike/spike.py`  
**Full results:** `spike/results.json`

---

## 1. What the Spike Tested

This spike tested the single riskiest assumption in the Northwind Support Copilot design:

> **"Semantic retrieval will return the correct source document chunk in the
> top-5 results for at least 80% of real support agent questions."**

If this assumption fails (hit-rate < 60%), the entire downstream pipeline —
prompt assembly, LLM generation, and citations — produces unreliable answers,
regardless of how good the LLM is.

---

## 2. Setup

| Parameter | Value |
|---|---|
| Embedding model | `all-MiniLM-L6-v2` (local, free — see note below) |
| Vector store | Chroma (in-memory, cosine similarity) |
| Chunk size | 512 tokens |
| Chunk overlap | 50 tokens |
| Top-k retrieved | 5 |
| Documents ingested | 10 (synthetic Northwind sample docs) |
| Total chunks stored | 10 |

> **Model swap note:** the original plan was `text-embedding-3-small` (OpenAI),
> but the available API key had no billing quota. I substituted a free,
> local embedding model (`all-MiniLM-L6-v2`, 384-dim, via `sentence-transformers`)
> so the spike could run without any API cost. This is a smaller/weaker model
> than `text-embedding-3-small`, so these results are a **conservative lower
> bound** — a production embedding model would likely perform at least as well.

---

## 3. Test Queries and Results

| # | Question | Expected Source | Hit? |
|---|----------|-----------------|------|
| 1 | What is the refund policy for annual subscriptions? | refund_policy.md | ✅ Y |
| 2 | How long does a refund take to appear on a credit card? | refund_policy.md | ✅ Y |
| 3 | How do I reset a user password in the admin panel? | admin_guide.md | ✅ Y |
| 4 | What happens to customer data when an account is cancelled? | data_retention_policy.md | ✅ Y |
| 5 | Which integrations are available on the Pro plan? | pricing_and_plans.md | ✅ Y |
| 6 | How do I export all data before cancelling my account? | data_export_guide.md | ✅ Y |
| 7 | What is the SLA for a critical priority support ticket? | support_sla.md | ✅ Y |
| 8 | Can a customer switch from annual to monthly billing mid-cycle? | billing_faq.md | ✅ Y |
| 9 | How do I add a new team member to an existing workspace? | user_management.md | ✅ Y |
| 10 | What are the minimum system requirements for the desktop app? | system_requirements.md | ✅ Y |

---

## 4. Results

| Metric | Value |
|--------|-------|
| **Total queries tested** | 10 |
| **Hits (correct doc in top-5)** | 10 |
| **Misses** | 0 |
| **Hit-rate** | **100%** |
| **Pass threshold** | ≥ 80% |
| **Do-not-proceed floor** | < 60% |
| **Verdict** | ✅ PASS |

---

## 5. Key Observations

### What worked well
- Every query retrieved its correct source document — semantic similarity
  reliably matched agent-style questions to the right policy/procedural doc
  even when question vocabulary (e.g. "switch from annual to monthly")
  did not exactly match document headings.
- Topically distinct documents (refund policy, billing FAQ, admin guide, etc.)
  produced clearly separable embeddings with no cross-document confusion.

### An important caveat on this result
A 100% hit-rate this clean is a signal to look closer, not just celebrate.
Two structural reasons this spike was easier than a real-world test:

1. **Each document fit inside a single 512-token chunk.** With only 10 total
   chunks in the entire collection — one per document — there was no
   chunk-boundary problem and no risk of an answer being split across chunks.
   This spike did not actually test chunking behavior at all.
2. **The corpus was synthetic and topically non-overlapping.** Each sample
   document covers a clearly distinct topic (refunds vs. billing vs. admin
   vs. SLA). Real Northwind documentation is likely to have more overlapping,
   ambiguous, and messier content — multiple docs touching the same topic,
   inconsistent terminology, longer pages that span several chunks.

### Implication
This result demonstrates the retrieval *mechanism* works correctly end-to-end
(embed → store → query → match), but it does **not yet prove** the system
will hold up against the real-world messiness the project brief specifically
asks for ("Real and slightly messy is the requirement. No toy datasets.").

---

## 6. Implications for the Full Project

The spike confirms the riskiest assumption is **mechanically sound**: semantic
retrieval correctly routes questions to source documents when documents are
topically distinct. This de-risks the core architecture decision (Chroma +
sentence embeddings + cosine similarity) and justifies proceeding to the full
build.

However, because the test corpus was small (10 docs, 10 chunks, 1 chunk/doc),
this result should be treated as a **necessary but not sufficient** validation.
Before treating retrieval as fully de-risked for production, the same test
should be re-run against:
- A larger, real Northwind/capstone corpus (15–30 docs, per the spec)
- Documents long enough to require multi-chunk splitting
- Documents with topical overlap (e.g. two docs that both mention billing)

---

## 7. Recommended Next Steps

- [x] Mechanism validated — proceed to full pipeline design (prompt assembler → LLM → citations)
- [ ] **Re-run the spike against the real 15–30 document corpus** (per project spec) before finalizing the hit-rate claim in the PRD
- [ ] Once documents are long enough to multi-chunk, re-test to confirm chunk-overlap handles answers that span chunk boundaries
- [ ] Run the Tier B chunking comparison spike (Step 8) to validate behavior under more realistic, longer documents
- [ ] If swapping to a production embedding model (e.g. text-embedding-3-small) later, re-run this spike to confirm hit-rate holds or improves

---

## 8. Confidence Statement

> Before the spike, retrieval was rated a High-likelihood, High-impact risk —
> the single riskiest assumption in the project. The spike returned a 100%
> hit-rate, which raises confidence that the core retrieval mechanism (embed →
> Chroma → cosine similarity) is sound. However, because the test corpus was
> small and each document fit in one chunk, this result mainly proves the
> *plumbing* works, not that retrieval will hold up on a larger, messier,
> real-world corpus. My confidence in the underlying mechanism is high; my
> confidence in the 100% number generalizing to the full project is moderate
> until re-tested on real documents.

---

*Spike run by: Vishal Kumar Pagadala | June 2025*