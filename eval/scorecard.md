# Baseline Scorecard (Fast LLM-as-Judge)

**Evaluator LLM:** phi3:latest
**Golden set size:** 20 pairs
**Scoring method:** One LLM call per question (all 4 metrics combined)

| Metric | Score | Target | Floor | Pass/Fail |
|---|---|---|---|---|
| faithfulness | 0.796 | 0.90 | 0.70 | FAIL |
| answer_relevancy | 0.845 | 0.80 | 0.70 | PASS |
| context_precision | 0.890 | 0.70 | 0.60 | PASS |
| context_recall | 0.885 | 0.80 | 0.60 | PASS |

## Do-Not-Ship Check
✅ **All metrics above do-not-ship floors.** System is safe.
