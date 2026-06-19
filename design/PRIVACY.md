# PII and Privacy Protections
## Northwind Support Copilot — v1

**Author:** Vishal Kumar Pagadala
**Date:** June 2025  
**Status:** Draft  
**Version:** 1.0

---

## 1. Where PII Can Enter the System

A Support Copilot touches PII at multiple points in the pipeline, not just
"in the database." Mapping every entry point is the first step — you can't
protect what you haven't identified.

| Entry Point | What PII Might Appear | Risk Level |
|---|---|---|
| **User question (agent input)** | Agent may paste a customer's name, email, order ID, or full ticket text directly into the question | High — most likely PII source |
| **Retrieved document chunks** | Help docs *should* be PII-free, but real exported tickets/changelogs often contain example customer data left in by mistake | Medium |
| **LLM-generated answer** | If a chunk contains PII, the LLM may echo it back in the answer | Medium (inherits from above) |
| **Draft ticket reply (bounded action)** | A drafted reply addressed to a specific customer naturally contains their name/email | High — by design |
| **Audit logs (FR-07)** | Every query + response is logged for auditability — this is a second copy of any PII in the original interaction | High — logs persist longer than the live request |
| **Vector store embeddings** | If a chunk containing PII is embedded, that PII is now baked into a vector representation stored in Chroma | Medium — embeddings are not human-readable but are still considered personal data under GDPR |

---

## 2. PII Inventory

| PII Category | Examples | Where It Could Appear |
|---|---|---|
| Direct identifiers | Full name, email address, phone number | Agent questions, draft replies, audit logs |
| Account identifiers | Customer account ID, subscription ID | Agent questions, retrieved order-lookup results |
| Financial data | Last 4 digits of card, invoice amounts | Refund-related questions, billing FAQ retrieval |
| Behavioral/usage data | Login history, feature usage patterns | Audit logs, retrieved support history |
| Free-text sensitive content | Agent pasting a customer's full complaint verbatim | Agent questions (highest-risk, least controllable) |

> **Note:** Northwind's own documentation (refund policy, billing FAQ, etc.)
> is internal/company-authored and should contain **no real customer PII**
> by design. The actual PII risk is almost entirely in the **live query and
> response path**, not the static knowledge base — this should shape where
> you spend protection effort.

---

## 3. Protections by Pipeline Stage

### Stage 1 — Document Ingestion (offline)
| Protection | Implementation |
|---|---|
| PII scan before ingestion | Run a regex/NER-based PII scanner over every document before chunking and embedding; flag matches for human review before the doc enters Chroma |
| Source document hygiene | Internal policy: support docs must never contain real customer examples — use clearly-fake placeholder data (`customer@example.com`, `Jane Doe`) |

### Stage 2 — Live Query (agent → system)
| Protection | Implementation |
|---|---|
| Input redaction (best-effort) | Before logging or embedding the query, run it through a redaction filter (regex for emails, phone numbers, card-like digit sequences) — replace with `[REDACTED_EMAIL]`, etc. |
| No PII in embeddings | The query embedding is used only for similarity search and discarded after the request — it is never persisted as a standalone artifact |
| Agent training | Agents are instructed not to paste full customer messages verbatim; summarize the question instead (process control, not just a technical one) |

### Stage 3 — LLM Generation
| Protection | Implementation |
|---|---|
| System prompt constraint | Explicit instruction: "Do not include customer names, emails, or account numbers in your answer unless they appear in the retrieved context and are required to answer the question." |
| Output scan | Post-generation, run the same redaction filter on the LLM's answer before it's returned or logged |

### Stage 4 — Bounded Action (draft ticket reply)
| Protection | Implementation |
|---|---|
| Scoped exception | The draft reply is the one place PII (customer name/email) is *expected* — this is logged separately with stricter access controls, not redacted, since the agent needs to see it to send the reply |
| Human-in-the-loop | The draft is never sent automatically — an agent always reviews before it reaches the customer (per Tech Design Doc, Section 4) |

### Stage 5 — Audit Logging
| Protection | Implementation |
|---|---|
| Redacted-by-default logs | Logs store the *redacted* version of queries/answers, not raw text, except in the scoped draft-reply log |
| Retention limit | Audit logs retained 90 days (Pro/Starter) or 12 months (Enterprise) — matching Northwind's existing data retention policy |
| Access control | Audit logs accessible only to Support Managers and IT/AI Engineers — not all agents |

---

## 4. Access Controls

| Role | Can View Live Queries/Answers | Can View Audit Logs | Can View Draft Replies (unredacted) |
|---|---|---|---|
| Support Agent | Own queries only | No | Own drafts only |
| Support Manager | No | Yes (redacted) | No |
| IT / AI Engineer | No (production data) | Yes (full, for debugging) | No (unless investigating an incident) |

> Engineers debugging a production issue should default to using **redacted**
> logs first. Access to unredacted data requires a documented reason
> (e.g. an active incident ticket).

---

## 5. Encryption and Storage

| Layer | Protection |
|---|---|
| Data in transit | TLS 1.2+ for all API calls (Chroma, OpenAI, internal services) |
| Data at rest | Chroma vector store and audit logs encrypted at rest (disk-level encryption, e.g. cloud provider default) |
| API keys / secrets | Stored in environment variables / secrets manager — never committed to source control |
| Backups | Encrypted; retained per Northwind's existing 30-day backup purge policy |

---

## 6. Compliance Alignment

This design aligns with the data retention principles already documented in
Northwind's `data_retention_policy.md`:
- Right to Erasure (GDPR Article 17) requests apply to audit logs containing
  a customer's PII, not just account data — a deletion request must purge
  matching log entries within the same 30-day window.
- No PII is used to fine-tune or retrain any model — the system uses
  retrieval-augmented generation only, so there is no risk of PII leaking
  into model weights.

---

## 7. Known Limitations (Honest Assessment)

- **Regex/NER-based redaction is not perfect.** It will miss PII in
  unusual formats (e.g. a customer ID embedded mid-sentence without
  surrounding context) and may occasionally over-redact non-PII content.
  This is a best-effort control, not a guarantee.
- **Agent-pasted free text is the hardest surface to protect.** Technical
  controls can't fully prevent an agent from pasting a customer's entire
  message into the question field. This is mitigated by training and
  process, not code.
- **v1 has no automated PII audit/compliance report.** A future iteration
  should add periodic automated scans of stored logs to verify redaction
  is working as intended.

---

*Privacy strategy by: Vishal Kumar Pagadala | June 2025*