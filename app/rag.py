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
    context_text = "\n\n".join([doc[0] for doc in context_docs])
    prompt = f"""Answer the question using ONLY the following context. If the answer is not in the context, say "I don't know".
Context:
{context_text}

Question: {query}
Answer:"""
    llm = get_llm()
    return llm(prompt)

def answer(query):
    docs = retrieve(query)
    response = generate_with_context(query, docs)
    return {
        "query": query,
        "answer": response,
        "contexts": [doc[0] for doc in docs],
        "sources": [doc[1].get("source", "unknown") for doc in docs]
    }