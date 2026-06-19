# Cost Model
## Northwind Support Copilot — v1

**Author:** Vishal Kumar Pagadala  
**Date:** June 2025  
**Pricing verified:** June 2026 (OpenAI public pricing)

---

## 1. Pricing Inputs

| Component | Model | Input cost | Output cost |
|---|---|---|---|
| LLM (legacy, matches Tech Design Doc) | gpt-4o-mini | $0.15 / 1M tokens | $0.60 / 1M tokens |
| LLM (current recommended alternative) | gpt-4.1-mini | $0.40 / 1M tokens | $1.60 / 1M tokens |
| Embedding | text-embedding-3-small | $0.02 / 1M tokens | n/a (input-only) |

> Embedding is roughly **7–20x cheaper than the LLM call** per token — at this
> scale, embedding cost is essentially noise next to LLM generation cost.
> This is a useful sanity check: if your cost model shows embedding as the
> dominant expense, something in the token math is wrong.

---

## 2. Per-Query Cost Breakdown

### Assumptions (based on PRD FR-02, FR-03 and Tech Design prompt structure)

| Token source | Estimated tokens |
|---|---|
| System prompt (instructions + grounding rules) | ~200 |
| Retrieved context (5 chunks × ~150 tokens) | ~750 |
| User question | ~50 |
| **Total LLM input** | **~1,000** |
| LLM answer + citations (output) | ~300 |
| Query embedding (question only) | ~50 |

### Scenario A — Answer only (no bounded action triggered)

| Step | Tokens | Rate | Cost |
|---|---|---|---|
| Query embedding | 50 | $0.02/1M | $0.000001 |
| LLM input | 1,000 | $0.15/1M | $0.000150 |
| LLM output | 300 | $0.60/1M | $0.000180 |
| **Total (gpt-4o-mini)** | | | **$0.000331** |

### Scenario B — Answer + bounded action (draft ticket reply)

The bounded action is a second LLM call using the answer as context.

| Step | Tokens | Rate | Cost |
|---|---|---|---|
| Scenario A subtotal | — | — | $0.000331 |
| Draft-reply LLM input | 500 | $0.15/1M | $0.000075 |
| Draft-reply LLM output | 300 | $0.60/1M | $0.000180 |
| **Total (gpt-4o-mini)** | | | **$0.000586** |

### Comparison: gpt-4.1-mini (current recommended model)

| Scenario | gpt-4o-mini | gpt-4.1-mini |
|---|---|---|
| Answer only | $0.00033 | $0.00084 |
| Answer + draft reply | $0.00059 | $0.00154 |

**Conclusion:** Both models land **roughly 60–150x under** the PRD's
$0.05/query ceiling (NFR-02). Cost is not the binding constraint for this
system at any reasonable usage volume — latency and groundedness are the
real engineering challenges, not API spend.

---

## 3. One-Time Ingestion (Embedding) Cost

| Item | Value |
|---|---|
| Documents | 15–30 |
| Avg tokens/doc | ~2,000 (varies by source) |
| Total corpus tokens | ~30,000–60,000 |
| Embedding cost | $0.02/1M × 0.06M ≈ **$0.0012** |

Re-indexing the entire knowledge base costs **less than a tenth of a cent**.
This means frequent re-indexing (e.g. nightly, on every doc change) is
financially free — the only real cost of re-indexing is engineering time and
pipeline complexity, not API spend.

---

## 4. Volume Projections

Northwind has ~30 support agents. At an estimated 50 queries/agent/day,
with 20% of queries triggering the bounded action:

| Daily query volume | Daily cost (gpt-4o-mini) | Monthly cost (22 business days) |
|---|---|---|
| 100 queries (pilot, 3 agents) | $0.04 | $0.88 |
| 1,500 queries (full rollout, 30 agents) | $0.59 | $13.00 |
| 5,000 queries (Northwind + 2 sister brands) | $1.97 | $43.34 |
| 10,000 queries (aggressive growth scenario) | $3.94 | $86.68 |

> Even at 10,000 queries/day — roughly 6x Northwind's current full team
> volume — total monthly LLM spend stays under $100. This is a strong
> signal that handle-time reduction (the business KPI), not infrastructure
> cost, should drive the go/no-go decision on this project.

---

## 5. Cost Optimization Opportunities

Even though cost is not currently a constraint, these are the levers
available if usage scales far beyond projection:

| Lever | Mechanism | Estimated savings |
|---|---|---|
| **Batch API for re-indexing** | OpenAI's Batch API offers a 50% discount in exchange for up to 24-hour processing | 50% on all ingestion/re-index costs |
| **Prompt caching** | Cache the static system prompt portion (instructions, grounding rules) across requests | ~10–20% on LLM input cost at scale |
| **Reduce top-k** | Retrieve 3 chunks instead of 5 if hit-rate testing shows no quality loss | ~30–40% reduction in context tokens |
| **Smaller embedding model** | Already using the cheapest production-grade OpenAI embedding model | n/a — already optimal |
| **Skip bounded action by default** | Only draft a reply when the agent explicitly requests it (already FR-04's design) | Avoids ~45% of total cost on queries that don't need a draft |

---

## 6. Guardrail Recommendation

Given the wide margin between actual cost (~$0.0003–0.0006/query) and the
PRD's ceiling ($0.05/query), recommend tightening NFR-02's **do-not-ship
floor** from "> $0.15 triggers redesign" down to a tighter operational
alert threshold — e.g. **alert if average cost per query exceeds $0.01** —
since any cost approaching that level would indicate an unexpected failure
mode (e.g. retrieved context far larger than expected, or an infinite
retry loop), not normal operation.

---

*Cost model by: Vishal Kumar Pagadala | June 2025 | Pricing verified June 2026*