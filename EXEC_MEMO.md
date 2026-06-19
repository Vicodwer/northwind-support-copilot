# Executive Memo: Northwind Support Copilot

**To:** Engineering & Support Leadership
**From:** Vishal Kumar Pagadala
**Date:** June 2025
**Status:** v1 Spec Complete — Spike Validated — Ready for Build

---

## The Problem

Northwind's Tier-1 support agents spend roughly 40% of their handle time manually
searching across five or more scattered sources — help docs, changelogs, policy PDFs,
internal wikis — to answer repetitive product and policy questions. Average handle
time runs ~12 minutes against an 8-minute industry benchmark, answers are inconsistent
across agents, and new hires take 3–4 weeks to ramp. A prior AI demo hallucinated in
front of a customer, so the mandate here is explicit: ship something measurably
trustworthy, not another polished demo that breaks under real questions.

## The System, in Three Sentences

The Support Copilot is a retrieval-augmented pipeline: a question is embedded, matched
against a Chroma vector store of Northwind's documentation, and answered by an LLM that
is instructed to cite its sources or refuse rather than guess. Every component — query
in, chunks retrieved, answer out — is a typed Pydantic contract, so the system fails
loudly and specifically instead of silently drifting. The system performs exactly one
bounded action, drafting a ticket reply for human review, and never sends anything
autonomously.

## The KPIs That Define Success

Six KPIs gate the launch, each with a target and a do-not-ship floor: groundedness
(≥90% / floor 80%), answer relevance (≥85% / floor 70%), retrieval hit-rate (≥80% /
floor 60%), p95 latency (<4s / floor 8s), cost per resolved query (<$0.05 / floor
$0.15), and handle-time reduction (≥20% / floor 0%, the business KPI). These were
red-teamed by an independent LLM reviewer acting as a skeptical staff engineer, which
surfaced real gaps — most notably that the original retrieval hit-rate metric measured
"correct document," not "correct chunk," and that the handle-time KPI had a circular
dependency on shipping before it could be measured. Both have been corrected in the
revised spec.

## The Riskiest Assumption — and the Evidence

The riskiest assumption was whether semantic retrieval would reliably find the right
document given Northwind's scattered, inconsistently formatted documentation. A de-risk
spike tested this on 10 sample documents and 10 real-style support questions: **10 of
10 hit the correct source document (100% hit-rate)**, well above the 80% target. The
honest caveat: each document fit in a single chunk and the corpus was topically
non-overlapping, so this spike validates the retrieval *mechanism* — not the final
hit-rate number on the real, messier 15–30 document corpus. Confidence in the
architecture is high; confidence in the exact number generalizing is moderate until
re-tested on production-representative documents.

## What I Would Build First

If scope had to be cut to ship in half the time, the bounded action (draft ticket
reply) is the first thing to go — it's the part of the system least connected to the
core trust problem. What ships first is the cited, grounded Q&A pipeline itself: embed
→ retrieve → generate-with-citations → fallback-on-low-confidence. That's the piece
that directly answers the question Northwind actually has after the last failed demo —
"can we trust this not to make things up" — and it's the piece the spike has already
provided real evidence for.