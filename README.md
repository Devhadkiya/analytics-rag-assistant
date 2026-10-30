# Analytics RAG Assistant

A retrieval-augmented generation assistant that answers questions about an
analytics handbook — metric definitions, reporting conventions, metric
ownership — from the handbook itself, with citations, and declines when the
answer isn't there.

The point of the project isn't that an LLM can answer questions. It's the three
things that decide whether a self-service analytics assistant is usable inside
a company: **does retrieval find the right passage, does the model stay inside
it, and does the thing know when to say no.**

---

## Why this exists

"Where does this number come from?" and "how is this metric defined?" are the
two questions an analyst answers most often, and both have the same property:
the answer already exists in writing, and nobody can find it.

That makes it a good RAG problem and a bad chatbot problem. A chatbot that
improvises a metric definition is worse than no chatbot, because a confident
wrong definition gets pasted into a board deck and nobody checks it.

## Architecture

```
data/handbook/*.md
      │
      ├─ split on ## headings
      ├─ chunk to ~220 tokens, 60-token overlap, heading prepended
      │
      ▼
OpenAI text-embedding-3-small  ──►  Chroma (cosine, persistent on disk)
                                           │
question ──► embed ──► top-k search ──► similarity floor ──► context
                                                                │
                                                                ▼
                                            gpt-4o-mini, temperature 0
                                            strict system prompt + citations
```

## What I learned building it

These are the parts that actually took the time, and the reason the
configuration looks the way it does.

**Chunking loses the context a definition depends on.** Split a handbook on a
fixed token window and you get chunks like *"...is not renewed within a 7-day
grace period."* — correct text, orphaned from the word "churn". The embedding
for that chunk is near-useless, because the thing it defines isn't in it.
Fixed by splitting on `##` headings first and prepending the heading to every
chunk, so each chunk is self-describing. Overlap alone did not fix this;
the heading did.

**Retrieval returns plausible but wrong passages.** Ask about "net revenue" and
cosine search happily returns the *gross* MRR paragraph — adjacent vocabulary,
wrong answer. Two mitigations: a similarity floor (`MIN_SIMILARITY`) below
which a hit is discarded rather than passed to the model, and a system prompt
that forces per-claim citations so a wrong passage is visible in the output
instead of being laundered into fluent prose.

**Knowing when to hand back matters more than coverage.** The eval set includes
an out-of-scope question on purpose. An assistant that answers 100% of
questions is not better than one that answers 85% and declines the rest — it's
worse, because you can't tell which 15% to distrust. `answer.py` returns
*"Not covered in the handbook."* rather than reaching for the nearest chunk.

**Temperature 0 and a short prompt beat a clever prompt.** Most of the quality
came from the retrieval side, not from prompt wording.

## Evaluation

`eval/evaluate.py` measures the thing that actually fails — retrieval — rather
than asking a model to grade its own output.

- **hit@k** — did the passage that contains the answer appear in the top *k*?
  The model cannot answer from a passage it never saw, so a retrieval miss is
  an unrecoverable failure and a generation wobble usually isn't.
- **correct decline** — for an out-of-scope question, did retrieval correctly
  return nothing?

Each case in `eval/questions.yaml` names the source file the answer must come
from, so the check is objective.

```
result   expected       question
------------------------------------------------------------------------
HIT      metrics.md     How is an active user defined?
HIT      metrics.md     What counts as churn for a monthly subscription?
...
DECLINE  (none)         What is our Kubernetes cluster autoscaling policy?
------------------------------------------------------------------------
hit@k:          6/6
correct decline: 1/1
```

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your OPENAI_API_KEY

python src/ingest.py                      # index the corpus
python src/answer.py "How is churn defined?"
python eval/evaluate.py                   # measure retrieval
```

Cost to index the sample corpus and run the eval is a fraction of a cent on
`text-embedding-3-small`.

## Using it on your own documents

Drop markdown files into `data/handbook/` (or point `CORPUS_DIR` elsewhere) and
re-run `ingest.py`. If your documents don't use `##` headings, adjust
`split_sections` in `src/ingest.py` — the heading-prepending step is the part
that matters most for retrieval quality, so it's worth adapting rather than
dropping.

## Layout

```
src/config.py     settings, with the reasoning behind each threshold
src/ingest.py     read → split on headings → chunk → embed → store
src/retrieve.py   embed question → top-k → similarity floor
src/answer.py     strict prompt, citations, declines when context is thin
eval/             question set and retrieval scoring
data/handbook/    sample corpus: metrics, revenue, conventions, ownership
```

## Limitations

- Single-turn. No conversation memory or query rewriting, so follow-ups like
  "and for annual?" won't resolve.
- No reranker. A cross-encoder over the top 20 would likely beat the
  similarity floor, and is the next thing I'd add.
- The similarity floor is tuned by hand on a small eval set. On a larger corpus
  it should be chosen from a precision/recall curve rather than by eye.
- Markdown only.
