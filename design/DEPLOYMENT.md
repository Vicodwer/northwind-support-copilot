# Deployment and Re-indexing Strategy
## Northwind Support Copilot — v1

**Author:** Vishal Kumar Pagadala 
**Date:** June 2025  
**Status:** Draft  
**Version:** 1.0

---

## 1. Deployment Model: Cloud, Single-Region (v1)

| Decision | Choice | Why |
|---|---|---|
| Hosting | Cloud (e.g. AWS/GCP/Azure — provider-agnostic in v1) | No existing on-prem infrastructure for AI workloads at Northwind; cloud avoids upfront hardware cost |
| Topology | Single region | Northwind's support team operates in one primary timezone; multi-region adds complexity not yet justified (see Failure Modes doc, Section 5) |
| Compute | Containerized API service (e.g. Docker on a managed container platform) | Stateless query pipeline scales horizontally; no custom infra needed for v1 query volume (~1,500/day) |
| Vector store | Managed or self-hosted Chroma instance, persistent volume (not ephemeral) | v1 spike used `EphemeralClient()` for testing; production requires `PersistentClient()` so the index survives restarts |

---

## 2. Environment Tiers

```
Dev  →  Staging  →  Production
```

| Environment | Purpose | Chroma collection | Document source |
|---|---|---|---|
| **Dev** | Local development, spike testing | Local ephemeral Chroma (as in `spike.py`) | Sample/synthetic docs |
| **Staging** | Pre-release validation, hit-rate regression testing | Persistent Chroma, isolated collection | Mirror of production corpus |
| **Production** | Live agent traffic | Persistent Chroma, versioned collection (see Section 4) | Real Northwind knowledge base |

A change only reaches production after passing the same hit-rate spike test
(Step 5/8) against the staging corpus — re-running the spike script is the
release gate, not just a manual code review.

---

## 3. Re-indexing Strategy

### When re-indexing is triggered
| Trigger | Re-index type |
|---|---|
| New document added to knowledge base | Incremental — embed and add only the new document's chunks |
| Existing document edited | Incremental — delete old chunks for that `source`, re-embed and re-add |
| Document removed | Incremental — delete all chunks matching that `source` |
| Embedding model upgraded (e.g. swapping to a newer model) | **Full re-index** — all existing vectors are incompatible with a new embedding space and must be regenerated |
| Chunking strategy changed (per Step 8 findings) | **Full re-index** — chunk boundaries shift, so partial updates would leave inconsistent chunk sizes |

### Incremental re-index process
```
1. New/changed document detected (manual trigger or scheduled scan)
2. If document existed before: delete all chunks where metadata.source == filename
3. Chunk the new/updated document (per chosen strategy from Step 8)
4. Embed the new chunks
5. Add to the live Chroma collection
6. Log the re-index event (document, chunk count, timestamp)
```

This mirrors the `ingest_documents()` pattern from `spike.py` — the
production ingestion pipeline is the same logic, pointed at a persistent
collection instead of an ephemeral one.

### Full re-index process
```
1. Create a NEW Chroma collection (versioned name, e.g. "northwind_v2")
2. Re-embed the entire corpus into the new collection
3. Run the hit-rate spike test against the new collection
4. If hit-rate meets target (≥80%): switch production traffic to the new
   collection (atomic pointer swap, not a destructive in-place change)
5. Keep the OLD collection for 7 days as a rollback safety net
6. After 7 days with no issues, delete the old collection
```

---

## 4. Version Management

| What's versioned | How |
|---|---|
| Chroma collection | Named with a version suffix (`northwind_v1`, `northwind_v2`) — never edited destructively in place |
| Source documents | Tracked in the GitHub repo (`/spike/docs` in this project; a real CMS or doc-store in production) — every document change is a commit |
| Embedding model version | Pinned and logged per collection (e.g. `northwind_v2` metadata records `embedding_model: text-embedding-3-small`) |
| Chunking config | Pinned per collection (chunk size, overlap, strategy) — stored alongside the collection metadata |

A production system always knows, for any given answer, exactly which
collection version, embedding model, and chunking strategy produced it —
this is essential for debugging a bad answer after the fact.

---

## 5. Rollback Strategy

| Scenario | Rollback action |
|---|---|
| New full re-index causes hit-rate regression | Switch the production pointer back to the previous collection version (kept for 7 days per Section 3) |
| A single bad document causes wrong answers | Incremental rollback — delete just that document's chunks, no full re-index needed |
| A code deployment introduces a bug (not data-related) | Standard application rollback (previous container image / git revert) — independent of the vector store |

Because re-indexing is **cheap** (Step 9's cost model: ~$0.001 to fully
re-embed the corpus), the rollback strategy can favor safety over
efficiency — keeping old collections around for a week costs nothing
meaningful and provides a real safety net.

---

## 6. What's Deliberately Out of Scope for v1

- Real-time/streaming document ingestion (re-indexing is triggered manually
  or on a schedule, not on every document save)
- Multi-region replication of the vector store
- Blue/green deployment automation (the atomic pointer swap in Section 3 is
  done manually in v1; automating this is a natural v2 improvement)

---

*Deployment strategy by: Vishal Kumar Pagadala | June 2025*