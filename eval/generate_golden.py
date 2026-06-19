# eval/generate_golden.py
import csv
import random
from app.ingest import build_or_get_collection
from app.utils import get_llm

def get_all_chunks():
    """Fetch all chunk texts and their sources from Chroma."""
    collection = build_or_get_collection()
    results = collection.get()
    # results contains: ids, documents, metadatas
    chunks = []
    for doc, meta in zip(results["documents"], results["metadatas"]):
        chunks.append({
            "text": doc,
            "source": meta.get("source", "unknown")
        })
    return chunks

def generate_qa_for_chunk(chunk_text, llm):
    """Use the LLM to produce a question and answer based on the chunk."""
    prompt = f"""Generate a question that can be answered **only** using the following text, and provide the correct answer.
Output format:
Question: <question>
Answer: <answer>

Text:
{chunk_text}
"""
    response = llm(prompt)
    # Parse the response
    q, a = "", ""
    for line in response.strip().split("\n"):
        if line.startswith("Question:"):
            q = line[len("Question:"):].strip()
        elif line.startswith("Answer:"):
            a = line[len("Answer:"):].strip()
    # If parsing failed, use fallback
    if not q or not a:
        # Fallback: ask a simpler prompt
        fallback_prompt = f"Based on this text, what is one question a user might ask and its answer? Answer in format: Q: ... A: ...\nText: {chunk_text[:500]}"
        fallback = llm(fallback_prompt)
        # Try to extract Q and A
        parts = fallback.split("A:")
        if len(parts) >= 2:
            q_part = parts[0].replace("Q:", "").strip()
            a_part = parts[1].strip()
            q, a = q_part, a_part
        else:
            q, a = "Fallback question", "Fallback answer"
    return q, a

def generate_golden_set(num_pairs=35, adversarial_count=5, output_file="eval/golden_set.csv"):
    llm = get_llm()
    chunks = get_all_chunks()
    print(f"Total chunks available: {len(chunks)}")
    if len(chunks) < num_pairs:
        num_pairs = len(chunks)
        print(f"Reducing pairs to {num_pairs} due to limited chunks.")
    # Randomly select chunks for Q&A
    selected = random.sample(chunks, num_pairs)
    pairs = []
    for i, chunk in enumerate(selected):
        print(f"Generating Q&A for chunk {i+1}/{num_pairs}...")
        q, a = generate_qa_for_chunk(chunk["text"], llm)
        pairs.append({
            "question": q,
            "answer": a,
            "context": chunk["text"],
            "source": chunk["source"]
        })
    
    # Add adversarial questions (answers not in corpus)
    adversarial_questions = [
        "What is the CEO's favorite color?",
        "When was the company founded?",
        "How many employees does Northwind have?",
        "What is the stock price of Northwind?",
        "Who is the head of customer support?"
    ]
    for adv_q in adversarial_questions[:adversarial_count]:
        pairs.append({
            "question": adv_q,
            "answer": "I don't know",
            "context": "",  # No context
            "source": "adversarial"
        })
    # Shuffle to mix
    random.shuffle(pairs)
    
    # Write to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["question", "answer", "context", "source"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pairs)
    print(f"✅ Generated {len(pairs)} Q&A pairs saved to {output_file}")
    print("⚠️  MANUAL VERIFICATION REQUIRED: Please open the CSV and check/correct any poor Q&A pairs.")

if __name__ == "__main__":
    generate_golden_set()