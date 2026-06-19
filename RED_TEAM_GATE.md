# LLM-Integrated Task — Red-Team Gate
## Northwind Support Copilot

**Author:** Vishal Kumar Pagadala 
**Date:** June 2025  
**Status:** Required pass/fail gate — must include all 4 parts below

---

## 1. The Prompt

```
You are a skeptical staff engineer doing a design review on a PRD for an
AI Support Copilot at a B2B SaaS company. Below is the KPI section from
the PRD. Find weak or unmeasurable metrics and missing failure modes.
Be specific — point to exact lines, not general advice.

[PASTE: PRD.md Section 6 — the full KPI table, six rows: Groundedness,
Answer Relevance, Retrieval Hit-Rate, p95 Latency, Cost per Query,
Handle-Time Reduction]
```

---

## 2. The Model's Response

> **1. "Answer Relevance" is underspecified.** The row says "Human eval on
> 50 labelled test questions (pass/fail)" but defines no rubric for what
> counts as a pass. Without a scoring guide, two reviewers could disagree
> on the same answer, and there's no inter-rater reliability check
> mentioned. This metric is currently more of an intention than a
> measurement.
>
> **2. The groundedness eval has no judge validation step.** Using an
> LLM-as-judge to score groundedness is reasonable, but the PRD doesn't
> say which model judges, or how you'd catch the judge itself being wrong
> or inconsistent. An ungrounded judge producing a "grounded" score is a
> silent failure mode this metric can't catch.
>
> **3. Sample sizes imply false precision.** A retrieval hit-rate of "≥80%"
> measured on only 8–10 queries means a single miss swings the number by
> roughly 10 percentage points. Stating a precise target and floor against
> such a small sample overstates how confidently you can actually measure
> this in the spike phase.
>
> **4. There is no metric for citation accuracy specifically.**
> Groundedness measures whether a *claim* is supported by retrieved
> context, but doesn't verify the *citation* attached to that claim points
> to the right source. A model could state something true and grounded but
> cite the wrong document — which would still erode agent trust and isn't
> caught by any current KPI.
>
> **5. There's no metric for the bounded action's own error rate.** All
> six KPIs measure the *answer*. None measure whether the drafted ticket
> reply itself is accurate. Since a bad draft reply could be sent to a real
> customer, this is arguably a more severe failure mode than a bad chat
> answer, and it currently has zero dedicated measurement.
>
> **6. The business KPI has no defined baseline methodology.** "≥20%
> handle-time reduction" requires knowing the *current* average handle
> time precisely enough to detect a 20% change. The PRD doesn't say how or
> when that baseline is measured, which makes the target currently
> unfalsifiable — you could claim success or failure depending on an
> undocumented baseline choice.
>
> **7. p95 latency is reported without a p50.** A system can have an
> excellent median response time while still having a damaging long tail.
> Consider tracking both so a latency regression doesn't hide in the
> "still under p95" noise.

---

## 3. My Critique of That Response

| Point | Verdict | Reasoning |
|---|---|---|
| 1. No relevance rubric | **Sharp, valid** | This is a real, specific gap — "pass/fail" with no rubric is genuinely unmeasurable as written. Incorporated into the revision. |
| 2. No judge validation step | **Valid but partially generic** | Fair point, but "validate your LLM judge" is fairly standard advice for any LLM-as-judge setup — not a deep insight specific to this PRD. Still worth fixing. |
| 3. Sample size implies false precision | **Sharp, valid** | This is the strongest point in the response. It correctly identifies that the spike's n=10 cannot support the precision implied by stating an exact 80% target. This should be reflected honestly in both the PRD and FINDINGS.md. |
| 4. No citation accuracy metric | **Sharp, valid — best insight** | This is a genuinely new distinction I had not made: groundedness (is the claim true) is different from citation accuracy (does the citation point to the right place). This is worth adding as its own KPI row. |
| 5. No bounded-action error metric | **Sharp, valid** | Correct and important — every existing KPI measures the chat answer, none measure the drafted reply itself, which is the higher-stakes output since it can reach a real customer. |
| 6. No baseline methodology for handle-time | **Valid, but already partly addressed elsewhere** | Fair criticism of the PRD as written. However, this is somewhat mitigated by the North-Star Metrics doc (Step 13), which specifies a rolling 2-week A/B test — the critique doesn't have visibility into that later document. I'll cross-reference it in the revision rather than treat this as a brand-new gap. |
| 7. No p50 alongside p95 | **Generic, lower priority** | Reasonable but standard SRE advice, not specific to this system. Adding it costs nothing, so I'll include it, but it's the weakest point in the response. |

**Overall assessment:** The critique was specific, tied to exact lines in
the document, and surfaced two points (citation accuracy and bounded-action
error rate) that represent genuine gaps not covered anywhere else in the
project. One point (baseline methodology) was valid but didn't have visibility
into work done in a later step. One point (p50/p95) was generically correct
but not particularly incisive. This is a passing-quality critique — useful,
not just flattering or rubber-stamping the original document.

---

## 4. Revised KPI Section

> Replaces PRD.md Section 6. Changes from the original are marked with `[NEW]` or `[REVISED]`.

| KPI | Definition | How Measured | Target | Do-Not-Ship Floor |
|-----|-----------|--------------|--------|-------------------|
| **Groundedness / Faithfulness** | % of answer claims directly supported by a retrieved chunk | LLM-as-judge (gpt-4o-mini, validated against 10 human-labelled samples before trusting the judge at scale) `[REVISED]` on 50 sampled Q&A pairs | ≥ 90% | < 80% |
| **Citation Accuracy** `[NEW]` | % of citations that point to the document actually containing the claim (distinct from groundedness — a claim can be true but mis-cited) | Manual spot-check: for each citation, confirm the cited source contains the claim it's attached to | ≥ 95% | < 85% |
| **Answer Relevance** | % of answers that fully address the user's intent, scored against a defined rubric `[REVISED: rubric added]` — full credit only if the answer addresses the literal question asked, partial credit logged separately and excluded from the pass rate | Two independent human reviewers on 50 labelled test questions; disagreements adjudicated by a third reviewer `[REVISED: inter-rater step added]` | ≥ 85% | < 70% |
| **Retrieval Hit-Rate** | % of queries where the correct source document appears in top-5 results. **Caveat:** spike-phase measurement (n=8–10) has a ±10pp margin of error per query; treat as directional until re-tested at n≥50 on the real corpus `[NEW caveat]` | Manual labelling of spike test queries: hit = correct doc in top-5 | ≥ 80% | < 60% |
| **Bounded Action Error Rate** `[NEW]` | % of drafted ticket replies containing a factual error or recommending an incorrect action | Manual review of 30 sampled draft replies before each release | < 5% | > 15% — block the bounded action feature entirely until fixed |
| **p50 / p95 Latency** `[REVISED: p50 added]` | Median and 95th-percentile end-to-end response time | `time.perf_counter()` instrumented in Python on 100 test queries | p50 < 1.5 sec, p95 < 4 sec | p95 > 8 sec |
| **Cost per Query** | Total LLM + embedding API cost per resolved query | Token counts × current API price, measured on 100 test queries; see Cost Model doc for full derivation `[REVISED: cross-reference added]` | < $0.05 | > $0.15 |
| **Handle-Time Reduction** *(Business KPI)* | % reduction in average agent handle time per ticket. Baseline measured as the trailing 4-week average handle time per agent immediately prior to copilot rollout `[REVISED: baseline methodology defined]` | A/B test: copilot-assisted vs. unaided agents, rolling 2-week window (see North-Star Metrics doc) | ≥ 20% reduction | 0% or negative improvement |

---

*Red-team gate completed by: Vishal Kumar Pagadala | June 2025*