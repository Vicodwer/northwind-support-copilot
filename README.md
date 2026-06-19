# Northwind Support Copilot

A retrieval-augmented support copilot for Northwind, a mid-size B2B SaaS company.
Tier-1 support agents currently spend ~40% of handle time searching across scattered
help docs, changelogs, and policy PDFs. This system retrieves the right document,
answers with citations, and can draft one bounded action (a ticket reply) — without
hallucinating, which is the exact failure mode a prior demo suffered from.

This repo is the spec-and-derisk phase: a PRD, a technical design doc, an architecture
diagram, a risk register, and a de-risk spike proving the riskiest assumption holds.

---

## Start Here (read in this order)

1. **[`prd/`](./prd)** — Problem statement, users, scope, functional/non-functional
   requirements, and the KPI table that defines "done."
2. **[`design/`](./design)** — Architecture, Pydantic data contracts for every
   pipeline stage, model/embedding choices, and the one bounded action.
3. **[`diagrams/`](./diagrams)** — Architecture diagram and request sequence diagram
   (Cloudairy, exported as PNG).
4. **[`RISK_REGISTER.md`](./RISK_REGISTER.md)** — Top 5 risks scored by likelihood ×
   impact, risk matrix, and the riskiest assumption the spike tests.
5. **[`PRIVACY.md`](./PRIVACY.md)** · **[`FAILURE_MODES.md`](./FAILURE_MODES.md)** ·
   **[`DEPLOYMENT.md`](./DEPLOYMENT.md)** · **[`COST_MODEL.md`](./COST_MODEL.md)** ·
   **[`NORTH_STAR_METRICS.md`](./NORTH_STAR_METRICS.md)** — Tier A non-functional plan.
4. **[`spike/`](./spike)** — The de-risk spike script and its real document corpus
   (`spike/docs/`), testing whether retrieval finds the correct source document.
5. **[`FINDINGS.md`](./FINDINGS.md)** — Spike results, hit-rate table, and an honest
   read of what the result does and doesn't prove.
6. **[`CHUNKING_FINDINGS.md`](./CHUNKING_FINDINGS.md)** — Tier B stretch: fixed-size vs.
   recursive/semantic chunking, head-to-head, with a reasoned verdict.
7. **[`LLM_REDTEAM.md`](./LLM_REDTEAM.md)** — The pass/fail gate: an LLM red-teams the
   KPI section as a skeptical staff engineer, plus my critique of that critique and a
   revised KPI table.
8. **[`EXEC_MEMO.md`](./EXEC_MEMO.md)** — One-page, interview-ready summary of the
   whole project.

---

## The Riskiest Assumption

> Semantic retrieval (Chroma + embeddings) will return the correct source document
> in the top-5 results for real, messy support questions — not just clean synthetic
> ones.

This is tested directly in `spike/spike.py` against the real 15–30 document corpus in
`spike/docs/`. Results and the honest caveats are in `FINDINGS.md`.

---

## System Overview

```
Raw Docs → Chunker → Embedder → Chroma → Retriever → Prompt Assembler
→ LLM (grounded answer + citations) → [optional] Draft Ticket Reply
```

- **Embedding model:** `text-embedding-3-small`
- **LLM:** `gpt-4o-mini`
- **Vector store:** Chroma (local)
- **Bounded action:** draft a ticket reply for human review — the system never sends
  anything autonomously.

Full architecture, component responsibilities, and typed data contracts are in
[`design/`](./design).

---

## KPIs (do-not-ship floors in parentheses)

| KPI | Target | Floor |
|---|---|---|
| Groundedness / Faithfulness | ≥ 90% | < 80% |
| Answer Relevance | ≥ 85% | < 70% |
| Retrieval Hit-Rate | ≥ 80% | < 60% |
| p95 Latency | < 4 sec | > 8 sec |
| Cost per Resolved Query | < $0.05 | > $0.15 |
| Handle-Time Reduction (business KPI) | ≥ 20% | 0% or negative |

These were red-teamed by an independent LLM reviewer — see `LLM_REDTEAM.md` for the
gaps that were found (statistical weakness on small sample sizes, a doc-level vs.
chunk-level mismatch in the hit-rate metric, and a circular dependency in the
handle-time KPI) and the revised definitions.

---

## Tier B Stretch: Chunking Strategy Comparison

The main spike used a 512-token chunk size with documents short enough that each
collapsed into a single chunk — so chunking strategy never actually got tested. A
second spike (`spike/chunking_comparison.py`) closes that gap by forcing a smaller
120-token chunk size so documents split into multiple chunks, then compares fixed-size
vs. recursive/semantic chunking head-to-head.

| Metric | Fixed-size | Recursive/semantic |
|---|---|---|
| Hit-rate | 100.0% (10/10) | 100.0% (10/10) |
| Total chunks | 41 | 40 |
| Avg tokens/chunk | 99.2 | 86.0 |
| Ingest time | 857.4 ms | 478.4 ms |
| Avg query latency | 12.3 ms | 8.9 ms |

**Verdict:** Tied on hit-rate, so the tie-breaker is efficiency. Recursive chunking
ingests ~44% faster and queries ~28% faster, with slightly fewer/leaner chunks, while
never splitting a sentence mid-way. **Recommendation: use recursive/semantic chunking
for the full build.**

Same caveat as the main spike applies — this still ran on synthetic, topically-distinct
documents; the comparison should be re-run on the real 15–30 document corpus before
locking this in for production. Full write-up: [`CHUNKING_FINDINGS.md`](./CHUNKING_FINDINGS.md).

---

## Tier A Advanced: Risk Register, Privacy, Failure Modes, Deployment, Cost, North-Star

### Risk Register & Riskiest Assumption

Five risks scored on likelihood × impact. **R-01 (semantic retrieval failing on
real questions)** is the only Critical (High × High) risk and is the one the spike
directly tests.

![Risk Matrix](./risk_matrix.png)

| ID | Risk | Score | Mitigation |
|---|---|---|---|
| R-01 ⚠️ | Retrieval fails on loosely-formatted docs | **Critical** | De-risk spike — do not proceed if hit-rate < 60% |
| R-02 | LLM hallucinates beyond retrieved context | High | Strict "cite or refuse" prompt + groundedness eval gate |
| R-03 | Corpus too inconsistent for one chunking strategy | Medium | Tier B chunking comparison spike |
| R-04 | Agents over-trust answers without checking citations | High | Citations always visible; soft launch to 3 agents first |
| R-05 | API cost exceeds ceiling at scale | Low | Cost model (below) + gpt-4o-mini default |

Full breakdown, failure-mode causes, and pass/investigate/do-not-proceed thresholds:
[`RISK_REGISTER.md`](./RISK_REGISTER.md).

### Privacy & PII Handling

PII risk is concentrated almost entirely in the **live query/response path**
(agent-pasted questions, draft replies, audit logs) — not the static knowledge base,
which is internal and should contain no real customer data by design. Protections by
stage: pre-ingestion PII scanning, input/output redaction filters, scoped (unredacted)
logging only for the draft-reply bounded action, 90-day/12-month log retention matching
existing policy, and role-based access control. Known limitation: regex/NER redaction
is best-effort, not a guarantee — see [`PRIVACY.md`](./PRIVACY.md) for the full
stage-by-stage breakdown and honest gaps.

### Failure Modes

10 failure modes (`F-01`–`F-10`) covering API/vector-store outages, retrieval misses,
out-of-scope questions, bounded-action failures, hallucination despite good retrieval,
rate limits, malformed input, silent redaction failures, and embedding-version
mismatches. Core design principle: **the system should say "I don't know" or escalate
— never guess.** Degrades through a 5-level ladder, and always fails *open*: agents
keep their pre-copilot manual workflow at every level. Full table:
[`FAILURE_MODES.md`](./FAILURE_MODES.md).

### Deployment & Re-indexing

Single-region cloud deployment, three environment tiers (dev → staging → production),
with a persistent (not ephemeral) Chroma collection in production. Re-indexing is
incremental for single document add/edit/remove, and a **full re-index with an atomic
collection-version swap** (`northwind_v1` → `northwind_v2`) when the embedding model or
chunking strategy changes — old collections kept 7 days as a rollback safety net. A
release only reaches production after re-passing the same hit-rate spike test against
the staging corpus. Full strategy: [`DEPLOYMENT.md`](./DEPLOYMENT.md).

### Cost Model

At projected volume (1,500 queries/day, 30 agents), estimated cost is **~$0.59/day
(~$13/month)** on gpt-4o-mini — roughly 60–150x under the PRD's $0.05/query ceiling.
One-time corpus embedding costs ~$0.0012. Recommendation: tighten the operational
alert threshold to **$0.01/query** (vs. the PRD's looser $0.15 do-not-ship floor),
since approaching that level would signal a structural bug, not normal load. Full
breakdown and optimization levers (batch API, prompt caching, lower top-k): 
[`COST_MODEL.md`](./COST_MODEL.md).

### North-Star & Guardrail Metrics

**North-star:** handle-time reduction (≥20% vs. control) — the one metric that only
improves when accuracy, speed, and agent trust are all working together. It is
**only valid if every guardrail holds**: groundedness ≥80%, retrieval hit-rate ≥60%,
p95 latency <8s, cost/query <$0.01, zero PII leakage, fallback rate <30%/hour. A
handle-time win achieved by violating a guardrail (e.g. agents trusting fast-but-wrong
answers) doesn't count as a real win. Full metric tree:
[`NORTH_STAR_METRICS.md`](./NORTH_STAR_METRICS.md).

---

## Running the Spike

```bash
cd spike
python -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt
python spike.py
```

Add your `.env` with the relevant API key before running (see `.env.example` if
present). Output: a question → retrieved-source → hit/miss table, written to
`results.json`, summarized in `../FINDINGS.md`.

---

## Reflection

See the [Reflection](#reflection-1) section below for answers on the hardest KPI to
measure, the riskiest assumption, and what gets cut first under a tighter timeline.

### Reflection

**Which KPI was hardest to make measurable, and why?**
Handle-Time Reduction — it can only be measured via a live multi-week agent pilot,
which creates a circular dependency with a pre-launch "do-not-ship" gate. Resolved by
splitting it into a pre-launch shadow-mode proxy and a post-launch live A/B test.

**What is your riskiest assumption, and did the spike raise or lower your confidence?**
That semantic retrieval reliably surfaces the correct document on Northwind's
scattered, inconsistently formatted docs. The spike raised confidence in the
retrieval *mechanism* (embed → store → query → match) — full results and caveats are
in `FINDINGS.md`.

**If you had to cut scope to ship in half the time, what's the first thing that goes?**
The bounded action (draft ticket reply). It's a second LLM call layered on top of the
core trust problem this project exists to solve. Cutting it still ships a cited,
grounded Q&A system — the part that actually proves the system won't hallucinate.

---

## Repo Structure

```
northwind-support-copilot/
├── prd/                  # Product requirements doc
├── design/               # Technical design doc + Pydantic contracts
├── diagrams/             # Architecture + sequence diagrams (PNG)
├── spike/
│   ├── docs/                          # Real 15–30 document corpus used for the spike
│   ├── spike.py                       # De-risk spike script (retrieval hit-rate)
│   ├── results.json                   # Raw spike output
│   ├── chunking_comparison.py         # Tier B: fixed vs. recursive chunking spike
│   └── results_chunking_comparison.json
├── FINDINGS.md           # Spike results + honest analysis
├── CHUNKING_FINDINGS.md  # Tier B chunking strategy comparison + verdict
├── RISK_REGISTER.md      # Tier A: risk table + riskiest assumption breakdown
├── risk_matrix.png       # Risk matrix visual (likelihood × impact)
├── PRIVACY.md            # Tier A: PII handling by pipeline stage
├── FAILURE_MODES.md      # Tier A: 10 failure modes + degradation ladder
├── DEPLOYMENT.md         # Tier A: deployment + re-indexing strategy
├── COST_MODEL.md         # Tier A: per-query and volume cost projections
├── NORTH_STAR_METRICS.md # Tier A: north-star metric + guardrails
├── LLM_REDTEAM.md        # Pass/fail gate: LLM red-team of the KPI section
├── EXEC_MEMO.md          # One-page interview-ready summary
└── README.md             # This file
```

---

## Status

Spec & de-risk phase complete. Riskiest assumption tested in `spike/`. Next: build the
slice specced here and measure it against these exact targets.