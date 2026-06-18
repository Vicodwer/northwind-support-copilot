# Technical Design Document
## Northwind Support Copilot — v1

**Author:** [Your Name]  
**Date:** June 2025  
**Status:** Draft  
**Version:** 1.0

---

## 1. System Architecture Overview

The system follows a linear RAG (Retrieval-Augmented Generation) pipeline.
A user query enters, travels through retrieval, then generation, then optionally
triggers one bounded action. Every step has a typed data contract.

```
┌─────────────────────────────────────────────────────────────────┐
│                        INGESTION (offline)                       │
│  Raw Docs (PDF/MD) → Chunker → Embedder → Chroma Vector Store   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        QUERY (online / per request)              │
│                                                                  │
│  User Question                                                   │
│       │                                                          │
│       ▼                                                          │
│  [Embedder] ──── embed query ────▶ [Chroma Retriever]           │
│                                         │ top-5 chunks           │
│                                         ▼                        │
│                                  [Prompt Assembler]              │
│                                  system prompt +                 │
│                                  retrieved chunks +              │
│                                  user question                   │
│                                         │                        │
│                                         ▼                        │
│                                     [LLM]                        │
│                                  GPT-4o-mini                     │
│                                         │                        │
│                                         ▼                        │
│                              [Answer + Citations]                │
│                                         │                        │
│                                         ▼                        │
│                           [Bounded Action: Draft Reply]          │
│                           (only if agent requests it)            │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **Chunker** | Splits raw documents into overlapping fixed-size chunks (512 tokens, 50-token overlap) |
| **Embedder** | Converts chunks and queries to dense vectors using text-embedding-3-small |
| **Chroma Vector Store** | Stores and indexes all chunk embeddings; serves top-k similarity queries |
| **Retriever** | Queries Chroma with embedded user question; returns top-5 chunks with metadata |
| **Prompt Assembler** | Builds the LLM prompt: system instructions + retrieved chunks + user question |
| **LLM** | GPT-4o-mini; generates grounded answer with inline citations |
| **Bounded Action** | Drafts a ticket reply using the LLM answer; single, constrained side-effect |

---

## 2. Data Contracts (Pydantic Models)

> Every component in the pipeline has a typed input and output.
> Engineers reason in contracts, not vibes.

```python
from pydantic import BaseModel, Field
from typing import Optional


# ── Input ────────────────────────────────────────────────────────

class QueryInput(BaseModel):
    """What the agent receives from the support agent."""
    question: str = Field(..., min_length=5, max_length=2000,
                          description="Natural-language question from support agent")
    top_k: int = Field(default=5, ge=1, le=10,
                       description="Number of chunks to retrieve from Chroma")
    draft_reply: bool = Field(default=False,
                              description="If True, trigger the bounded action")


# ── Retrieval ────────────────────────────────────────────────────

class RetrievedChunk(BaseModel):
    """A single chunk returned by Chroma."""
    chunk_id: str = Field(..., description="Unique ID of the chunk in Chroma")
    source_document: str = Field(..., description="Filename of the source document")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    content: str = Field(..., description="Raw text of the retrieved chunk")
    similarity_score: float = Field(..., ge=0.0, le=1.0,
                                    description="Cosine similarity score")


class RetrievalResult(BaseModel):
    """Output of the Retriever component."""
    query: str
    chunks: list[RetrievedChunk]
    retrieval_latency_ms: float


# ── Generation ───────────────────────────────────────────────────

class Citation(BaseModel):
    """A single source citation attached to the answer."""
    source_document: str
    chunk_id: str
    relevance_note: Optional[str] = None


class CopilotAnswer(BaseModel):
    """The LLM-generated answer with citations."""
    answer_text: str = Field(..., description="Grounded answer in plain English")
    citations: list[Citation] = Field(...,
                                      description="Sources used to generate the answer")
    is_grounded: bool = Field(...,
                              description="True if answer is supported by retrieved chunks")
    confidence: str = Field(...,
                            pattern="^(high|medium|low|fallback)$",
                            description="Confidence level of the answer")


# ── Bounded Action ───────────────────────────────────────────────

class TicketDraft(BaseModel):
    """Output of the bounded action: a draft ticket reply."""
    subject_line: str = Field(..., max_length=100)
    body: str = Field(..., max_length=1500,
                      description="Draft reply for the support agent to review and send")
    based_on_sources: list[str] = Field(...,
                                        description="Source docs used to draft this reply")


# ── Final Response ───────────────────────────────────────────────

class CopilotResponse(BaseModel):
    """The complete response returned to the caller."""
    query: str
    answer: CopilotAnswer
    retrieved_chunks: list[RetrievedChunk]
    ticket_draft: Optional[TicketDraft] = None   # populated only if draft_reply=True
    total_latency_ms: float
    cost_usd: float = Field(..., description="Estimated API cost for this query")
```

---

## 3. Model and Embedding Choices

| Component | Choice | Justification |
|-----------|--------|---------------|
| **Embedding model** | `text-embedding-3-small` (OpenAI) | Best cost/performance ratio for semantic search; 1536 dimensions; $0.02 per 1M tokens — default specified in project spec |
| **LLM** | `gpt-4o-mini` (OpenAI) | Strong instruction-following at low cost (~$0.15 per 1M input tokens); sufficient for citation-grounded Q&A without needing GPT-4o |
| **Vector store** | `Chroma` (local) | Zero infrastructure overhead for v1; familiar from RAG module; easy to swap for Pinecone/Weaviate later |
| **Chunking** | Fixed-size, 512 tokens, 50-token overlap | Predictable chunk sizes keep embedding costs stable; overlap prevents answers from being split across chunk boundaries |
| **Reranker** | None in v1 | Adds latency and cost; revisit if hit-rate falls below 80% floor |

---

## 4. The One Bounded Action

### What it is
The agent can perform exactly **one action**: draft a ticket reply.

When `draft_reply=True` in `QueryInput`, the system passes the generated answer
and citations to a second LLM call that produces a `TicketDraft` — a subject
line and body text the agent can review and send.

### Why only one action
The spec says: *"one bounded action."* Limiting to one action means:
- The failure surface is small and testable
- There is no ambiguity about what the agent can and cannot do autonomously
- The agent **never sends** a reply — it only drafts it; a human always approves

### Constraints on the action
| Constraint | Value |
|------------|-------|
| Max reply length | 1,500 characters |
| Tone instruction | Professional, concise, cite at least one source |
| Cannot do | Send email, update ticket status, access external APIs |
| Fallback | If no grounded answer exists, draft says: "I need to escalate this to a specialist" |

### Pseudocode flow

```python
def run_copilot(input: QueryInput) -> CopilotResponse:
    # Step 1: Embed the question
    query_vector = embed(input.question)

    # Step 2: Retrieve top-k chunks from Chroma
    retrieval = retrieve(query_vector, top_k=input.top_k)

    # Step 3: Assemble prompt and call LLM
    answer = generate_answer(input.question, retrieval.chunks)

    # Step 4: Trigger bounded action only if requested
    draft = None
    if input.draft_reply and answer.is_grounded:
        draft = draft_ticket_reply(answer)

    # Step 5: Return typed response
    return CopilotResponse(
        query=input.question,
        answer=answer,
        retrieved_chunks=retrieval.chunks,
        ticket_draft=draft,
        total_latency_ms=measure_latency(),
        cost_usd=estimate_cost()
    )
```

---

## 5. Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Strict grounding | LLM instructed to cite or refuse | Prevents hallucination; directly addresses Northwind's prior bad experience |
| Sync pipeline | Single request/response, no async streaming in v1 | Simpler to instrument latency and debug; streaming is a v2 enhancement |
| Local Chroma | No cloud vector DB in v1 | Reduces moving parts during spike; easy to swap later |
| No memory | Each query is stateless | Avoids compounding errors across turns; scope decision from PRD |

---

*End of Technical Design Document — v1.0*