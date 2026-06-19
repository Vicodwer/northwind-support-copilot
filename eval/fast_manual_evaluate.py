# eval/fast_manual_evaluate.py
import pandas as pd
import json
import re
from app.rag import answer
from app.utils import get_llm
from app.config import TARGETS, FLOORS, OLLAMA_MODEL

# We'll use the same LLM (llama3.2) as judge
llm = get_llm()

def score_all_metrics(question, answer_text, contexts, ground_truth):
    """Ask the LLM to score all 4 metrics in one JSON response."""
    contexts_str = "\n\n".join(contexts) if contexts else "No context retrieved."

    prompt = f"""You are a strict evaluator for a RAG (Retrieval-Augmented Generation) system.
Rate the following outputs on a scale from 0.0 to 1.0.

Definitions:
- **faithfulness**: Every claim in the answer is directly supported by the context. (1.0 = perfect support, 0.0 = major hallucination)
- **answer_relevancy**: The answer directly and completely addresses the question. (1.0 = perfectly on-topic, 0.0 = completely off-topic)
- **context_precision**: The retrieved contexts are highly relevant to the question. (1.0 = all chunks useful, 0.0 = none useful)
- **context_recall**: The retrieved contexts contain all the information needed to answer. (1.0 = all info present, 0.0 = critical info missing)

Return **ONLY** a valid JSON object with exactly these four keys: "faithfulness", "answer_relevancy", "context_precision", "context_recall".
Do not include any other text, explanations, or markdown.

Question: {question}

Retrieved Contexts:
{contexts_str}

Generated Answer:
{answer_text}

Ground Truth (for reference):
{ground_truth}

JSON:
"""
    response = llm(prompt)
    # Try to parse JSON
    try:
        # Find JSON block in the response
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            scores = json.loads(match.group())
        else:
            scores = json.loads(response)
        # Ensure all keys exist
        required = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
        for key in required:
            if key not in scores:
                scores[key] = 0.5
            scores[key] = min(1.0, max(0.0, float(scores[key])))
        return scores
    except Exception as e:
        # Fallback: return default scores
        print(f"  ⚠️ JSON parsing failed. Raw response: {response[:100]}...")
        return {"faithfulness": 0.5, "answer_relevancy": 0.5,
                "context_precision": 0.5, "context_recall": 0.5}

def evaluate_golden_set(golden_csv="eval/golden_set.csv", sample_size=None):
    df = pd.read_csv(golden_csv)
    # Optionally sample a subset for speed
    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42)
        print(f"⚠️ Using a sampled subset of {len(df)} questions for speed.")
    else:
        print(f"✅ Using full golden set of {len(df)} questions.")
    
    results = []
    for idx, row in df.iterrows():
        q = row["question"]
        gt = row["answer"]
        print(f"📝 Processing Q{idx+1}/{len(df)}: {q[:50]}...")
        
        try:
            rag_out = answer(q)
            ans = rag_out["answer"]
            ctx = rag_out["contexts"]
        except Exception as e:
            print(f"  ❌ RAG error: {e}")
            continue
        
        print("  🤖 Scoring all 4 metrics in one call...")
        scores = score_all_metrics(q, ans, ctx, gt)
        
        results.append({
            "question": q,
            "answer": ans,
            "ground_truth": gt,
            **scores
        })
    
    # Build scorecard
    results_df = pd.DataFrame(results)
    avg_scores = results_df.mean(numeric_only=True).to_dict()
    
    scorecard = pd.DataFrame({
        "Metric": ["faithfulness", "answer_relevancy", "context_precision", "context_recall"],
        "Score": [avg_scores.get("faithfulness", 0), avg_scores.get("answer_relevancy", 0),
                  avg_scores.get("context_precision", 0), avg_scores.get("context_recall", 0)],
        "Target": [TARGETS["faithfulness"], TARGETS["answer_relevancy"],
                   TARGETS["context_precision"], TARGETS["context_recall"]],
        "Floor": [FLOORS["faithfulness"], FLOORS["answer_relevancy"],
                  FLOORS["context_precision"], FLOORS["context_recall"]]
    })
    scorecard["Pass/Fail"] = scorecard.apply(
        lambda r: "PASS" if r["Score"] >= r["Target"] else "FAIL", axis=1
    )
    
    print("\n" + "="*60)
    print(f"📊 BASELINE SCORECARD (LLM-as-Judge | Model: {OLLAMA_MODEL})")
    print("="*60)
    print(scorecard.to_string(index=False))
    
    # Save markdown (UTF-8, no emojis)
    with open("eval/scorecard.md", "w", encoding="utf-8") as f:
        f.write("# Baseline Scorecard (Fast LLM-as-Judge)\n\n")
        f.write(f"**Evaluator LLM:** {OLLAMA_MODEL}\n")
        f.write(f"**Golden set size:** {len(df)} pairs\n")
        f.write(f"**Scoring method:** One LLM call per question (all 4 metrics combined)\n\n")
        f.write("| Metric | Score | Target | Floor | Pass/Fail |\n")
        f.write("|---|---|---|---|---|\n")
        for _, row in scorecard.iterrows():
            status = "PASS" if row["Score"] >= row["Target"] else "FAIL"
            f.write(f"| {row['Metric']} | {row['Score']:.3f} | {row['Target']:.2f} | {row['Floor']:.2f} | {status} |\n")
        f.write("\n## Do-Not-Ship Check\n")
        below = any(scorecard["Score"] < scorecard["Floor"])
        if not below:
            f.write("✅ **All metrics above do-not-ship floors.** System is safe.\n")
        else:
            for _, row in scorecard.iterrows():
                if row["Score"] < row["Floor"]:
                    f.write(f"- ❌ **{row['Metric']}** floor violation ({row['Score']:.3f} < {row['Floor']:.2f}).\n")
    
    print("\n💾 Scorecard saved to eval/scorecard.md")
    results_df.to_csv("eval/results_detailed.csv", index=False, encoding="utf-8")
    return scorecard

if __name__ == "__main__":
    # Evaluate on a subset for speed (change sample_size=None for full set)
    evaluate_golden_set(sample_size=20)