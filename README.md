# rag-assurance

**Build a small RAG system, then independently validate it.** A GenAI app is the *system under
validation*; a fail-closed assurance harness adjudicates whether each of its answers is **grounded in
the retrieved sources or hallucinated**, and reports an honest coverage denominator.

**▶ Live dashboard:** https://monongahelahellbender.github.io/rag-assurance/

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

## Roadmap — one project, four skills, all shipped

| # | Increment | Skill it earns | Status |
|---|-----------|----------------|--------|
| 1 | Offline **validation core** — RAG pipeline + faithfulness harness, stdlib-only | the assurance spine | ✅ done |
| 2 | Real **RAG** path — langchain embedding retriever (Ollama embeddings + vector store) | RAG + langchain | ✅ done |
| 3 | **React** dashboard over the validation report (per-case verdicts, strict gate, coverage) | React front end | ✅ done |
| 4 | **Cloud deploy** — GitHub Actions CI/CD → GitHub Pages (an AWS S3 script is in `deploy/` too) | cloud deployment | ✅ done |

## Run it (no installs needed)

```bash
# the assurance deliverable — strict validation + the pass/fail gate:
python3 scripts/validate.py                             # judge = local Ollama (default)

# test on a FRONTIER model (key stays in your env; only send the synthetic/public corpus):
RAGASSURANCE_JUDGE=anthropic ANTHROPIC_API_KEY=sk-... python3 scripts/validate.py

# see the RAG pipeline (system under validation) retrieve + answer:
python3 scripts/run_rag.py "What must source data be under GCP?"

# tests (offline — strict aggregation + fail-closed judge):
PYTHONPATH=src python3 -m pytest -q
```

## The dashboard

The React dashboard (`dashboard/`) renders the validation report — metric cards (accuracy,
hallucination catch, false-flags, coverage, strict-gate pass) plus a per-case table with
color-coded verdicts and the pass/fail gate. `.github/workflows/deploy.yml` builds it and publishes
to GitHub Pages on every push. Run it locally:

```bash
cd dashboard && npm install && npm run dev
```

The dashboard reads `dashboard/public/report.json`; regenerate that snapshot with
`python3 scripts/export_report.py`.

## How the strict scorer + fail-closed judge work

`validation/faithfulness.py → score_faithfulness` is **strict**: it splits an answer into claims,
judges each, and an answer is **GROUNDED only if every claim is verified supported**. Any unsupported
claim fails it; any unverifiable claim DEFERs to a human. The strict gate passes only fully-grounded
answers.

Per-claim adjudication lives in `validation/judge.py → judge_claim`, the **fail-closed verifier**: it
tries a deterministic match first, then asks an LLM to PROPOSE support *with a quoted sentence*, and
**deterministically checks the quote really occurs in the context** (fabricated evidence is rejected
to DEFER). So the LLM can never produce a wrong GROUNDED — a model mistake only lowers coverage. Runs
on a local Ollama model or a frontier model (`RAGASSURANCE_JUDGE=anthropic`). See
[`docs/three_judge_comparison.md`](docs/three_judge_comparison.md) for a three-judge study.

## langchain embedding retrieval

The default retriever is a stdlib TF-IDF (lexical). The **langchain** path swaps in real embedding
retrieval (Ollama embeddings + a vector store) behind the same `.retrieve(query, k)` interface, so
the strict validator is unchanged. Set it up in an isolated venv:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
ollama pull nomic-embed-text          # chat models can't embed; this is the dedicated embedder
./.venv/bin/python scripts/run_rag.py --langchain "Who can consent for a participant who cannot consent themselves?"
```

`RAGASSURANCE_EMBED_MODEL` overrides the embedder. The langchain stack installs on Python 3.14 in the
pure-Python configuration used here (no faiss) — retrieval uses langchain's `InMemoryVectorStore`.

## Layout

```
corpus/                         synthetic, copyright-free clinical/pharma docs
src/ragassurance/
  corpus.py  retriever.py  langchain_retriever.py  generator.py  pipeline.py   the system under validation
  validation/
    faithfulness.py             strict claim-split + aggregation ("a bad claim is a fail")
    judge.py                    judge_claim — deterministic-first, LLM cite-and-verify, fail-closed
    fixtures.py                 labeled grounded / hallucinated / partial cases
    harness.py                  runs the scorer, reports the validation summary + strict gate
dashboard/                      React (Vite) dashboard over the validation report
scripts/  validate.py  run_rag.py  export_report.py  check_anthropic.py  debug_judge.py
deploy/   deploy_s3.sh + runbook (AWS S3 alternative to GitHub Pages)
docs/     three_judge_comparison.md
tests/    test_harness.py  test_judge.py
```

---

## Prior art (no novelty claimed)

This is an implementation, not a new mechanism. Cite-and-verify grounding, fail-closed refusal, and
a coverage denominator are established practice:

- **Necula, Proof-Carrying Code** (POPL 1997) — the artifact carries what makes it checkable.
- **Rashkin et al., Attributable to Identified Sources (AIS)** — the attribution framework for
  judging whether a generated statement is supported by its cited source.
- **Chow (1970)**, *On optimum recognition error and reject tradeoff* — the reject option and the
  error-versus-coverage tradeoff.
- **AWS Bedrock Guardrails** (contextual grounding, 2024) and comparable production filters — these
  already *block* sub-threshold responses rather than warning. Blocking is not a differentiator.
- **Anthropic Citations API** and the attributed-QA line (Bohnet et al. 2022; ALCE; FActScore) —
  verifying generated claims against retrieved sources at scale.
- **SR 11-7** (Fed/OCC model risk guidance) — ongoing monitoring and outcomes analysis, the
  model-risk framing this repo adopts.

A 2026-07-19 problem-shaped prior-art audit alleged this README claimed to differ from permissive
validators by blocking rather than warning. **That claim was not present** in the live README and
this file does not concede it; the audit's quote could not be verified against the artifact. This
section is added because the repo had no prior-art section at all, which is a real gap regardless.

---

*Part of a portfolio of refusal-first AI-assurance & verification tools — [github.com/MonongahelaHellbender](https://github.com/MonongahelaHellbender). Related: [rag-triad](https://github.com/MonongahelaHellbender/rag-triad) · [honesty-atlas](https://github.com/MonongahelaHellbender/honesty-atlas) · [assurance-compiler](https://github.com/MonongahelaHellbender/assurance-compiler) · [gradeability-audit](https://github.com/MonongahelaHellbender/gradeability-audit) · [oracle-shield](https://github.com/MonongahelaHellbender/oracle-shield) · [rag-assurance](https://github.com/MonongahelaHellbender/rag-assurance).*
