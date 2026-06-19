# Reflection

### Which KPI was hardest to make measurable, and why?

Handle-Time Reduction was the hardest by far. Every other KPI (groundedness, relevance,
hit-rate, latency, cost) can be measured offline, before a single real agent touches the
system. Handle-time reduction can only be measured by actually deploying the copilot to
live agents and comparing them against a control group over a multi-week pilot — which
creates a circular dependency with my own "do-not-ship floor" framing: I wrote a floor
for a metric that, by definition, can't exist until after I've already shipped. The
red-team exercise surfaced this directly, and the fix was to split it into a pre-launch
shadow-mode proxy (agents see the answer, it doesn't count) and a post-launch live
A/B test that's the real gate for full rollout. It's still imperfect — shadow mode
measures whether the answer was useful, not whether handle time actually dropped — but
it at least breaks the chicken-and-egg problem.

### What is your riskiest assumption, and did the spike raise or lower your confidence?

The riskiest assumption was that semantic retrieval (Chroma + embeddings) would
reliably surface the correct source document for real support questions, given that
Northwind's documentation is scattered and inconsistently formatted. The spike tested
this on 10 synthetic documents and returned a 100% hit-rate (10/10), which on its face
raises confidence a lot. But the result needs to be read carefully: each document fit
in exactly one chunk, so the spike never actually tested chunk-boundary behavior, and
the corpus was topically non-overlapping by construction, which is easier than real
Northwind docs will be. Net effect: my confidence in the retrieval *mechanism* (embed
→ store → query → match) is now high — the plumbing works. My confidence in the 100%
number generalizing to a real 15–30 doc corpus with overlapping topics and multi-chunk
documents is only moderate, and the spike's own FINDINGS.md says this explicitly. The
honest takeaway is that the spike de-risked the architecture choice, not the final
hit-rate target.

### If you had to cut scope to ship in half the time, what is the first thing that goes, and why?

The bounded action (draft ticket reply) goes first. It's the second LLM call in the
pipeline, it's not what makes the system trustworthy, and it's the easiest piece to
bolt back on later without touching the core architecture. Citations and groundedness
are the entire point of this project — Northwind was burned by a hallucinating demo,
so cutting the grounding/citation work to hit a deadline would directly undermine the
reason this project exists. Cutting the draft-reply feature instead means agents get a
cited, trustworthy answer and write the reply themselves — slower than v1's full
vision, but it ships the part that actually proves the system is safe to use, and it
keeps the riskiest-assumption story (retrieval quality) front and center instead of
diluting review time across two LLM calls instead of one.