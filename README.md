# rag-assurance

**Build a small RAG system, then independently validate it.** The flagship pattern of an AI
*model validator*: a GenAI app is the **system under validation**; an assurance harness adjudicates
whether its answers are **grounded in the retrieved sources or hallucinated**, and reports an honest
coverage denominator.

This repo is built in increments so the *assurance core* is real and runnable before any plumbing.

## Why this exists (the lane)

This is a portfolio piece for **AI model risk / AI governance / model validation**. It demonstrates
the validator's actual job — take a model's outputs and decide, with a defensible method, what is
supported and what is not — and frames the result in model-risk terms (ongoing monitoring + outcomes
analysis, with an explicit "what we could not check" denominator).

**Built for strict, high-stakes domains** — regulated industries (clinical, pharma, aviation,
financial compliance, legal) where an ungrounded claim is unacceptable. The policy is **a bad claim
is a fail**: an answer passes only if *every* claim is verified against the sources; one unsupported
claim fails it, and anything unverifiable routes to a human. The demo corpus is **synthetic,
copyright-free** compliance text written for this project; point it at real **public** documents from
your target domain (e.g. the NIST AI RMF, U.S.-government public domain) later.

## Roadmap (one project, three skills, built in increments)

| # | Increment | Skill it earns | Status |
|---|-----------|----------------|--------|
| 1 | Offline **validation core** — RAG pipeline + faithfulness harness, stdlib-only | the assurance spine | **done** |
| 2 | Real **RAG** path: langchain embedding retriever (Ollama embeddings + vector store) | RAG + langchain | **done** |
| 3 | **React** dashboard over the validation report (per-case verdicts, drift, coverage) | React front end | next |
| 4 | **AWS** deploy of the live demo + dashboard | cloud deployment | later |

The point is the spine: even if you stop after increment 1, you have a real model-validation artifact.

## Run it (no installs needed)

```bash
# the assurance deliverable — strict validation + the pass/fail gate:
python scripts/validate.py                              # judge = local Ollama (default)

# test on a FRONTIER model (key stays in your env; only send the synthetic/public corpus):
RAGASSURANCE_JUDGE=anthropic ANTHROPIC_API_KEY=sk-... python scripts/validate.py

# see the RAG pipeline (system under validation) retrieve + answer:
python scripts/run_rag.py "What does a monitoring signal tell you?"

# tests (offline — strict aggregation + fail-closed judge):
PYTHONPATH=src python -m pytest -q
```

## How the strict scorer + fail-closed judge work

`validation/faithfulness.py → score_faithfulness` is **strict**: it splits an answer into claims,
judges each, and an answer is **GROUNDED only if every claim is verified supported**. Any unsupported
claim fails it; any unverifiable claim DEFERs to a human. The strict gate passes only fully-grounded
answers.

Per-claim adjudication lives in `validation/judge.py → judge_claim`, the **fail-closed verifier**: it
tries a deterministic match first, then asks an LLM to PROPOSE support *with a quoted sentence*, and
**deterministically checks the quote really occurs in the context** (fabricated evidence is rejected
to DEFER). So the LLM can never produce a wrong GROUNDED — a model mistake only lowers coverage. Runs
on a local Ollama model or a frontier model (`RAGASSURANCE_JUDGE=anthropic`).

## Increment 2 — langchain embedding retrieval

The default retriever is a stdlib TF-IDF (lexical). The **langchain** path swaps in real embedding
retrieval (Ollama embeddings + a vector store) behind the same `.retrieve(query, k)` interface, so
the strict validator is unchanged. Set it up in an isolated venv:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
ollama pull nomic-embed-text          # chat models can't embed; this is the dedicated embedder
./.venv/bin/python scripts/run_rag.py --langchain "Who can consent for a participant who cannot consent themselves?"
```

`RAGASSURANCE_EMBED_MODEL` overrides the embedder. Note: the langchain stack installs on Python
3.14 only in the pure-Python configuration used here (no faiss) — retrieval uses langchain's
`InMemoryVectorStore`.

## Layout

```
corpus/                         synthetic, copyright-free compliance docs
src/ragassurance/
  corpus.py  retriever.py  generator.py  pipeline.py    the RAG system under validation
  validation/
    faithfulness.py             strict claim-split + aggregation ("a bad claim is a fail")
    judge.py                    judge_claim — deterministic-first, LLM cite-and-verify, fail-closed
    fixtures.py                 labeled grounded / hallucinated / partial cases
    harness.py                  runs the scorer, reports the validation summary + strict gate
scripts/  validate.py  run_rag.py
tests/    test_harness.py  test_judge.py
```
