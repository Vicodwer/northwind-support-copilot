# North-Star and Guardrail Metrics
## Northwind Support Copilot — v1

**Author:** Vishal Kumar Pagadala
**Date:** June 2025  
**Status:** Draft  
**Version:** 1.0

---

## 1. Why This Document Exists

A team can hit every KPI target in the PRD and still ship something that
quietly degrades the business — for example, by improving latency at the
cost of groundedness, or improving hit-rate by retrieving more chunks
(which raises cost and latency). A **north-star metric** prevents
optimizing the wrong thing. **Guardrail metrics** prevent optimizing the
north-star at the expense of something that must never break.

---

## 2. North-Star Metric

> ## **Handle-time reduction (%)**
> *The percentage decrease in average agent handle-time per support ticket,
> measured by comparing copilot-assisted agents against a control group
> over a rolling 2-week window.*

### Why this, and not a technical metric
Groundedness, relevance, and hit-rate are **necessary but not sufficient**.
A system can be 95% grounded and still fail the business if agents don't
trust it enough to use it, or if it's too slow to fit into a live customer
conversation. Handle-time reduction is the one number that only goes up
when the *whole system* — accuracy, speed, and agent trust — is working
together. It is the same business KPI defined in the PRD (Section 6) and
sits at the top of the metric tree (Step 7).

### Target
| | Value |
|---|---|
| Target | ≥ 20% handle-time reduction vs. control group |
| Measurement window | Rolling 2-week A/B test, re-measured monthly post-launch |
| Minimum viable signal to continue investment | ≥ 10% (below this, re-evaluate before further investment) |

---

## 3. Guardrail Metrics

Guardrails are **trip-wires, not targets** — the system is never optimized
*toward* a guardrail. It is simply never allowed to cross one. Each
guardrail below was derived from a specific earlier deliverable in this
project; that traceability is intentional.

| Guardrail | Threshold | Source | What happens if crossed |
|---|---|---|---|
| **Groundedness floor** | Must stay ≥ 80% | PRD Section 6 KPI table | Pause rollout; investigate prompt/retrieval before re-enabling for new agents |
| **Retrieval hit-rate floor** | Must stay ≥ 60% | Risk Register R-01 do-not-proceed floor | Treat as a Sev-2 incident — this is the riskiest assumption breaking in production |
| **p95 latency ceiling** | Must stay < 8 seconds | PRD NFR-01 hard limit | Auto-alert on-call; if sustained > 1 hour, disable the bounded action (Step 12 Section 4) to reduce load |
| **Cost-per-query alert** | Must stay < $0.01 | Cost Model Section 6 (tightened from PRD's looser $0.15 ceiling) | Investigate — at this margin above expected cost (~$0.0006), something is structurally wrong, not just "usage is high" |
| **PII leakage** | Zero tolerance — any confirmed unredacted PII in logs is a guardrail breach, not a metric to trend | Privacy doc Section 7 (known limitation) | Immediate incident response; affected logs purged; redaction filter patched before resuming |
| **Fallback rate ceiling** | Must stay < 30% of all queries in any rolling hour | Failure Modes F-03/F-04 monitoring threshold | Indicates a corpus coverage gap or retrieval regression — investigate before it erodes agent trust in the tool |

---

## 4. How North-Star and Guardrails Interact

```
                    ┌─────────────────────────────┐
                    │   NORTH-STAR (optimize for)  │
                    │   Handle-time reduction ≥20%  │
                    └───────────────┬───────────────┘
                                    │
                 only valid if ALL guardrails hold
                                    │
        ┌────────────┬─────────────┼─────────────┬────────────┐
        ▼            ▼             ▼             ▼            ▼
  Groundedness   Hit-rate      Latency        Cost          PII
    ≥ 80%         ≥ 60%        < 8 sec      < $0.01/q    zero leak
```

A handle-time improvement achieved by **violating a guardrail does not
count** — for example, if handle-time drops because agents are blindly
trusting fast-but-wrong answers, that is a guardrail failure (groundedness)
masquerading as a north-star win, and must be caught by monitoring both
simultaneously, not the north-star metric in isolation.

---

## 5. Monitoring Cadence

| Metric type | Review cadence | Owner |
|---|---|---|
| North-star (handle-time reduction) | Monthly (requires A/B aggregation time) | Support Team Manager + AI Engineer |
| Guardrails | Real-time alerting (automated thresholds) | On-call AI Engineer |
| Guardrail trend review | Weekly | AI Engineer |

---

## 6. Honest Limitation

The north-star metric requires a working A/B test against a control group
of non-copilot-assisted agents, which is **not yet built in v1** — this
spec assumes that instrumentation exists at rollout time. Until then, hit-
rate and groundedness (validated in this project's spike) serve as the
best available *leading indicators* of north-star performance.

---

*North-star and guardrail metrics by: Vishal Kumar Pagadala | June 2025*