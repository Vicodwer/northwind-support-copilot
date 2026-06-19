# app/rag.py
from app.ingest import build_or_get_collection
from app.utils import get_llm
from app.config import TOP_K

collection = None

def get_collection():
    global collection
    if collection is None:
        collection = build_or_get_collection()
    return collection

def retrieve(query, top_k=TOP_K):
    coll = get_collection()
    results = coll.query(query_texts=[query], n_results=top_k)
    if not results["documents"] or not results["documents"][0]:
        return []
    return list(zip(results["documents"][0], results["metadatas"][0]))

def generate_with_context(query, context_docs):
    if not context_docs:
        return "I don't know—no relevant documents were found."

    # Build context with source numbering
    context_parts = []
    for i, (doc_text, meta) in enumerate(context_docs):
        source = meta.get("source", "unknown")
        context_parts.append(f"[Source {i+1}] {doc_text}")
    context_text = "\n\n".join(context_parts)

    # User prompt – just the facts
    prompt = f"""Context:
{context_text}

Question: {query}

Answer:"""

    # System instruction – force abstention
    system = """You are a support copilot. You must answer using only the context provided.
If the answer is not explicitly stated in the context, respond with exactly "I don't know" and nothing else.
Do not add any extra information or elaboration.
If you do use the context, cite the source number like [Source 1]."""

    llm = get_llm()
    response = llm(prompt, system=system)

    # ---- Fallback guardrail ----
    # If context is empty or response still contains extra info, force "I don't know"
    # For adversarial questions (no context), ensure abstention.
    if not context_docs or "I don't know" not in response:
        # If response is not exactly "I don't know", we could override
        # But we only override if context is empty to avoid losing valid answers
        if not context_docs:
            response = "I don't know"
    # Additionally, if response contains "I don't know" but also extra text, we could trim.
    # We'll keep it simple for now.
    return response

def answer(query):
    docs = retrieve(query)
    response = generate_with_context(query, docs)
    return {
        "query": query,
        "answer": response,
        "contexts": [doc[0] for doc in docs],
        "sources": [doc[1].get("source", "unknown") for doc in docs]
    }