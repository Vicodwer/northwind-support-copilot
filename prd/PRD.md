# Product Requirements Document
## Northwind Support Copilot — v1

**Author:** Vishal Kumar Pagadala 
**Date:** June 2025  
**Status:** Draft  
**Version:** 1.0

---

## 1. Problem Statement

Northwind's Tier-1 support agents spend approximately 40% of their handle time
manually searching across 5+ scattered knowledge sources — help docs, changelogs,
policy PDFs, and internal wikis — to answer repetitive product and policy questions.

This creates three measurable problems:

- **High handle time:** Average ticket handle time is ~12 minutes, well above the
  8-minute industry benchmark for B2B SaaS support.
- **Inconsistent answers:** Different agents retrieve different documents and phrase
  answers differently, eroding customer trust.
- **Slow agent ramp:** New agents take 3–4 weeks to reach proficient answer quality
  because the knowledge base is undiscoverable.

Leadership wants a Support Copilot that retrieves the right document, answers with
citations, and can draft a ticket reply — without hallucinating. A prior demo
hallucinated in front of a customer; the mandate is measurable trustworthiness,
not polish.

---

## 2. Target Users

| User | Role | Frequency |
|------|------|-----------|
| Tier-1 Support Agent | Primary — asks questions, uses drafted replies | Daily, ~50 queries/day |
| Support Team Manager | Secondary — monitors quality metrics and hit-rate | Weekly |
| IT / AI Engineer | Operator — maintains knowledge base, re-indexes docs | As needed |

### Top Three User Stories

**US-01:** As a support agent, I want to type a customer question and receive a
cited answer from the knowledge base in under 4 seconds, so that I don't have to
manually search across 5 different tools during a live customer interaction.

**US-02:** As a support agent, I want the copilot to draft a ticket reply based
on retrieved information, so that I can respond to customers faster and more
consistently without starting from a blank page.

**US-03:** As a support manager, I want to see retrieval hit-rate and answer
groundedness scores on a simple dashboard, so that I can verify the system is
trustworthy before rolling it out to all 30 agents.

---

## 3. Scope

### In Scope — v1
- Natural-language Q&A over a fixed knowledge base of 15–30 documents
- Answers with inline source citations (document name + chunk reference)
- One bounded action: **draft a ticket reply** based on the retrieved answer
- Semantic retrieval via Chroma vector store
- Latency and cost instrumented from day one
- Graceful fallback when the question is outside the knowledge base

### Out of Scope — v1
- Multi-turn conversation memory or session history
- Real-time integration with ticketing systems (Zendesk, Jira, Salesforce)
- Agent authentication or role-based access control
- Fine-tuning or retraining any model
- Support for non-English queries
- Real-time ingestion of new documents (re-indexing is manual in v1)
- Voice or chat widget UI (backend API only in v1)

---

## 4. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-01 | The system SHALL accept a natural-language question (string, max 500 tokens) as input. |
| FR-02 | The system SHALL retrieve the top-5 most relevant document chunks from Chroma using cosine similarity on text-embedding-3-small embeddings. |
| FR-03 | The system SHALL generate an answer grounded strictly in retrieved chunks, with inline citations to source document names. |
| FR-04 | The system SHALL expose one bounded action: generate a draft ticket reply from the retrieved answer, returned as a separate field in the response. |
| FR-05 | The system SHALL return a structured JSON response containing: answer text, source citations, retrieved chunk IDs, and draft reply (if action triggered). |
| FR-06 | The system SHALL return a graceful fallback message ("I could not find a reliable answer in the knowledge base") when no relevant chunk is retrieved above a confidence threshold. |
| FR-07 | The system SHALL log every query, retrieved sources, and response to a structured audit log. |

---

## 5. Non-Functional Requirements

| ID | Requirement | Target | Hard Limit |
|----|-------------|--------|------------|
| NFR-01 | **Latency** — p95 end-to-end response time | < 4 seconds | > 8 seconds is a blocker |
| NFR-02 | **Cost** — LLM + embedding API cost per resolved query | < $0.05 | > $0.15 triggers redesign |
| NFR-03 | **Availability** — uptime during business hours (9am–6pm) | 99% | < 95% is unacceptable |
| NFR-04 | **Privacy** — no PII stored in embeddings or vector store | All docs de-identified before ingestion | Any PII in Chroma = do not ship |
| NFR-05 | **Auditability** — every query/response pair logged with timestamp and source IDs | 100% of queries logged | Missing logs = compliance risk |

---

## 6. Success Metrics / KPIs

> These are the "done" criteria. Each KPI has a definition, measurement method,
> target, and a do-not-ship floor — the number below which v1 does not go to agents.

| KPI | Definition | How Measured | Target | Do-Not-Ship Floor |
|-----|-----------|--------------|--------|-------------------|
| **Groundedness / Faithfulness** | % of answer claims directly supported by a retrieved chunk | LLM-as-judge: for each claim, ask GPT-4o "Is this supported by the source?" on 50 sampled Q&A pairs | ≥ 90% | < 80% |
| **Answer Relevance** | % of answers that fully address the user's intent | Human eval on 50 labelled test questions (pass/fail) | ≥ 85% | < 70% |
| **Retrieval Hit-Rate** | % of queries where the correct source document appears in top-5 results | Manual labelling of 8–10 spike test queries: hit = correct doc in top-5 | ≥ 80% | < 60% |
| **p95 Latency** | 95th-percentile end-to-end response time (query in → answer out) | `time.perf_counter()` instrumented in Python on 100 test queries | < 4 sec | > 8 sec |
| **Cost per Query** | Total OpenAI API cost (embedding + LLM completion) per resolved query | Token counts × current API price, measured on 100 test queries | < $0.05 | > $0.15 |
| **Handle-Time Reduction** *(Business KPI)* | % reduction in average agent handle time per ticket after copilot deployment | A/B test: copilot-assisted agents vs. control group over 2-week pilot | ≥ 20% reduction | 0% or negative improvement |

---

## 7. Risks and Assumptions

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R-01 | Retrieval quality is poor on loosely-formatted help docs (PDFs, changelogs) | High | High | **← Riskiest assumption. Tested in de-risk spike.** |
| R-02 | LLM generates answers not grounded in retrieved context (hallucination) | Medium | High | Strict "cite or refuse" system prompt; groundedness eval gate |
| R-03 | Documents are too inconsistently formatted for a single chunking strategy | Medium | Medium | Compare fixed vs. recursive chunking in Tier B spike |
| R-04 | Agents over-trust copilot answers without verifying citations | Medium | High | UI always surfaces source documents; training note in rollout |
| R-05 | API costs exceed budget at scale (>1,000 queries/day) | Low | Medium | Cost model built in Tier A; use GPT-4o-mini as default LLM |

---

*End of PRD — v1.0*