# Failure Modes and Recovery Strategies
## Northwind Support Copilot — v1

**Author:** Vishal Kumar Pagadala 
**Date:** June 2025  
**Status:** Draft  
**Version:** 1.0

---

## 1. Philosophy

A system that fails silently is more dangerous than one that fails loudly.
The goal of this document is not to prevent every failure — that's
impossible — but to ensure every failure mode has a **known, tested
fallback** so the system degrades predictably instead of producing a
confident, wrong answer. This is the engineering answer to the demo that
hallucinated in front of a customer.

**Design principle:** when in doubt, the system should say "I don't know"
or escalate to a human — never guess.

---

## 2. Failure Mode Table

| # | Failure Mode | Likelihood | Detection | Recovery / Fallback | User-Facing Behavior |
|---|---|---|---|---|---|
| F-01 | **LLM API down or timing out** | Low | HTTP error / timeout on `chat_completion()` call | Retry once with exponential backoff (1s, then 3s); if still failing, return a static fallback message | "Our AI assistant is temporarily unavailable. Please search the help center directly or escalate to your team lead." |
| F-02 | **Chroma vector store unavailable** | Low | Connection error on `collection.query()` | Retry once (500ms backoff); if still failing, skip retrieval and route directly to a "no answer available" response — never call the LLM with no context | "I couldn't search the knowledge base right now. Please try again in a moment." |
| F-03 | **Retrieval miss (low-relevance chunks)** | Medium | Top-1 similarity score below threshold (e.g. < 0.5 cosine) | Do not call the LLM with weak context. Return graceful fallback (this is FR-06 from the Tech Design Doc) | "I couldn't find a reliable answer in the knowledge base for this question. Try rephrasing, or escalate to a specialist." |
| F-04 | **Out-of-scope question** (not covered by any document) | Medium | Same mechanism as F-03 — low similarity across all retrieved chunks | Same fallback as F-03 — the system cannot distinguish "out of scope" from "poorly retrieved" without a separate classifier, so it is treated identically | Same fallback message as F-03 |
| F-05 | **Bounded action (draft reply) fails** | Low | Second LLM call errors or times out | The primary answer + citations still return successfully — only the draft reply field is null | Answer displays normally; UI shows "Draft reply unavailable — try again" instead of blocking the whole response |
| F-06 | **LLM returns an ungrounded / hallucinated answer despite good retrieval** | Medium | Post-hoc groundedness check (LLM-as-judge or rule-based citation match) flags the answer as unsupported | Do not display the answer as-is. Either retry generation once with a stricter prompt, or fall back to "no reliable answer" | Same fallback as F-03, with an internal flag logged for review |
| F-07 | **Rate limit exceeded (OpenAI 429)** | Low–Medium at scale | HTTP 429 response | Queue the request with backoff per `Retry-After` header; if queue exceeds 5 seconds, fail to fallback rather than make the agent wait indefinitely | "High demand right now — please try again in a few seconds." |
| F-08 | **Malformed or empty user input** | Low | Pydantic validation fails on `QueryInput` (e.g. `min_length=5` violated) | Reject at the API boundary before any retrieval/LLM call — cheapest possible failure | "Please enter a more complete question." |
| F-09 | **PII redaction filter fails silently** | Low | No direct detection (this is the hardest failure mode to detect — see Privacy doc limitations) | Periodic automated audit (sampling logged queries/answers for PII patterns) catches this after the fact, not in real time | No immediate user-facing change — this is an operational/compliance failure, not a UX failure |
| F-10 | **Embedding model / API version mismatch after an update** | Low | New deployments re-embed a canary document and compare similarity score against expected baseline before going live | Block deployment if canary check fails; do not silently switch embedding models without re-indexing the full corpus | n/a — caught before reaching production |

---

## 3. Graceful Degradation Ladder

When multiple things go wrong at once, the system should degrade in this order
— each level is a smaller promise than the one above it:

```
Level 0 (normal):     Grounded answer + citations + optional draft reply
        ↓ (if action fails)
Level 1:               Grounded answer + citations, no draft reply
        ↓ (if retrieval is weak)
Level 2:               "No reliable answer found" + suggestion to rephrase
        ↓ (if Chroma/LLM is down)
Level 3:               Static fallback message + link to manual help center
        ↓ (if even the API layer is down)
Level 4 (total outage): Agent's existing manual workflow (search docs directly) —
                        the system fails OPEN, not closed; agents are never
                        blocked from doing their job without the copilot
```

> **Critical design choice:** the copilot is an *assistant*, not a
> *gatekeeper*. At every failure level, the agent retains their original,
> pre-copilot workflow as a fallback. The system should never be a single
> point of failure for support operations.

---

## 4. Monitoring and Alerting

| Signal | Threshold | Action |
|---|---|---|
| F-01/F-02 error rate | > 1% of requests in 5 min | Page on-call engineer |
| F-03/F-04 fallback rate | > 30% of requests in 1 hour | Alert — may indicate a corpus coverage gap or a retrieval regression, not necessarily an outage |
| F-06 groundedness flag rate | > 10% of requests in 1 day | Alert — investigate prompt or retrieval quality |
| F-07 rate limit hits | Any occurrence | Log only — informs whether to request a quota increase |

---

## 5. What This Document Does Not Cover (Honest Scope Limits)

- **Multi-region failover** — v1 runs in a single region; full disaster
  recovery is out of scope until usage volume justifies the complexity
- **Adversarial input handling** (prompt injection via retrieved documents) —
  worth a dedicated security review before production, not covered here
- **Cascading failures** (e.g. Chroma down *and* LLM rate-limited
  simultaneously) — the system handles each failure independently; true
  chaos-engineering testing is a post-v1 activity

---

*Failure mode analysis by: Vishal Kumar Pagadala | June 2025*