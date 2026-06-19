# Bonus: Eraser.io AI Diagram — Generation and Critique
## Northwind Support Copilot

**Author:** Vishal Kumar Pagadala
**Date:** June 2025

---

## 1. The Exercise

Eraser.io's AI Diagram feature can generate a first-draft architecture
diagram directly from a short text description. The point of this bonus
round is **not** to use that output as-is — it's to demonstrate that you can
critically evaluate AI-generated output against your own design decisions,
the same skill the LLM-integrated red-team gate (next step) tests for your
PRD.

---

## 2. Step-by-Step: Generate the First Draft

1. In Eraser.io, open **AI Diagram**
2. Give it a deliberately short, underspecified prompt — this is intentional,
   to see what it assumes by default:
   > *"Create an architecture diagram for an AI support copilot that answers
   > customer questions."*
3. Let it generate without further guidance
4. Export this first draft as `diagrams/ai_generated_v1.png` — **do not edit
   it yet**

---

## 3. The "Before" — What a Short Prompt Typically Produces

A short, underspecified prompt usually produces something close to this:
a generic three-box flow with no system specifics.

> *(See rendered widget above: Support Agent → AI System → Answer)*

This is a realistic illustration of what AI diagram generators default to
when given minimal context — they fill gaps with the most generic possible
interpretation of "AI system."

---

## 4. Critique — What's Missing or Wrong

Compare the naive first draft against your own Tech Design Doc
(`design/TECH_DESIGN.md`) and Step 3 architecture diagram. Document every
gap explicitly:

| # | What the AI draft got wrong or omitted | Why it matters | Source of truth |
|---|---|---|---|
| 1 | No retrieval step (Chroma) shown at all | The entire point of this system is RAG — without retrieval, the diagram describes a generic chatbot, not a grounded copilot | Tech Design Doc, Section 1 |
| 2 | No citations in the output | Citations are a functional requirement (FR-03) — omitting them hides the system's core trust mechanism | PRD FR-03 |
| 3 | No bounded action (draft reply) shown | The one constrained action the agent can take is a defining design decision (Tech Design Doc, Section 4) — a generic diagram erases it entirely | Tech Design Doc, Section 4 |
| 4 | No fallback / "no answer found" path | Without this, the diagram implies the system always produces an answer — which is exactly the failure mode that caused Northwind's prior bad demo | Failure Modes F-03/F-04 |
| 5 | "AI System" is an unlabeled black box | A real architecture diagram should show the chunker, embedder, vector store, and LLM as separate components with distinct responsibilities | Tech Design Doc, Section 1 |
| 6 | No indication of offline vs. online phases | Ingestion (one-time/scheduled) and query handling (per-request) have completely different performance and cost characteristics — collapsing them hides this | Tech Design Doc, Section 1 |

---

## 5. The "After" — Refined Diagram

The corrected diagram is the one already built in **Step 3**
(`diagrams/architecture.png`): two phases (offline ingestion, online query),
explicit Chroma retrieval, citations, and the bounded action shown as a
distinct, optional step.

> Re-use your Step 3 diagram here, or re-generate it in Cloudairy using a
> much more specific prompt:
> *"Create an architecture diagram for a RAG-based support copilot. Show two
> phases: offline ingestion (raw docs → chunker → embedder → Chroma) and
> online query (question → retriever → prompt assembly → LLM → answer with
> citations → optional bounded action: draft ticket reply). Include a
> fallback path for when no relevant documents are retrieved."*

---

## 6. Reflection

**What does this exercise demonstrate?**
AI diagram generation is a fast way to get a starting structure, but it
defaults to the most generic interpretation of any underspecified prompt.
The value isn't in the first draft — it's in knowing your own system well
enough to spot exactly what's missing. This is the same skill tested by the
LLM-integrated red-team gate on your PRD: using an AI tool well requires
being a better critic of its output than a passive consumer of it.

**Prompt specificity matters.** The second, detailed prompt in Section 5
produced a meaningfully better starting point than the first — most of the
"gap-filling" work in Section 4 can be avoided just by writing a more
complete initial prompt. That's a transferable lesson for working with any
AI generation tool, not just diagrams.

---

*Bonus critique by: Vishal Kumar Pagadala | June 2025*