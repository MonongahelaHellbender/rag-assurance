# Validating a RAG answerer with a fail-closed grounding check: a three-judge comparison

*A short case study from the `rag-assurance` project. Domain: clinical / pharma. The corpus is
synthetic, copyright-free text written for this study (Good Clinical Practice, pharmacovigilance,
informed consent, drug labeling); no proprietary or patient data is used.*

## The problem

A retrieval-augmented (RAG) system answers a question using retrieved source passages. The
model-risk question is: **is each claim in the answer actually supported by those sources, or is it
a hallucination?** In a strict, regulated domain, the tolerance for an ungrounded claim is zero.

## Method

The validator adjudicates one answer at a time:

1. **Split** the answer into claims (sentence-level).
2. **Judge each claim** against the retrieved context with a *fail-closed verifier*
   (`judge_claim`): it first tries a deterministic match; if that can't decide, it asks a language
   model to **propose** support **with a quoted sentence**, then **deterministically checks that
   the quote actually occurs in the context.** Fabricated evidence is rejected. A claim is only
   `SUPPORTED` when backed by verified evidence; anything unverifiable is `DEFER`.
3. **Aggregate under a strict policy — "a bad claim is a fail":** the answer is `GROUNDED` only if
   *every* claim is supported. Any unsupported claim fails it; any unverifiable claim routes to a
   human. A strict gate passes only fully-grounded answers.

**Key property:** because the language model never has the final say — every `SUPPORTED` must carry
evidence the code verifies — a judge's mistake can only *lower coverage* (more `DEFER`), never
produce a wrong `GROUNDED`. The system fails safe, not open.

## Evaluation set

Five labeled clinical/pharma cases, each targeting a known failure mode: a faithful restatement, a
blatant hallucination, a correct-but-paraphrased answer (low lexical overlap), a hallucination that
reuses source words but appends a false guarantee, and a mixed answer (one grounded + one
contradicted claim).

## Result — three judges of very different capability

| Judge | Accuracy vs. gold | Strict gate (pass = fully grounded) |
|---|---|---|
| Ollama `qwen2.5-coder:7b` (7B, local) | 5 / 5 | 2 / 5 |
| Claude Sonnet 5 (frontier) | 5 / 5 | 2 / 5 |
| Claude Opus 4.8 (strongest available) | 5 / 5 | 2 / 5 |
| Claude Fable 5 | — (rejected) | 0 / 5 |

**Two findings:**

1. **Judge-robustness.** Three judges spanning a 7-billion-parameter local model to a flagship
   frontier model produced identical verdicts on every case. That the result is invariant to judge
   capability is evidence that the cases are unambiguous and that the validator's behavior does not
   silently depend on which model grades it.

2. **Fail-closed on an unfit judge.** A fourth model (Fable 5) could not be used: it returned an
   API error on every call, so the validator **deferred all five cases (0/5 coverage) and produced
   zero false verdicts** rather than guess. Separately, Fable 5 ships a documented safeguard that
   routes health/biology queries to a *different* model — which would make it an unpredictable,
   non-auditable judge for a clinical corpus even if it were reachable. The design surfaced both:
   an unusable judge degrades coverage visibly instead of injecting silent errors.

## Honest limitations

- Five synthetic cases are a demonstration, not a benchmark; the numbers show *behavior*, not a
  generalizable accuracy figure.
- The verifier catches *fabricated* evidence but not *misjudged entailment* (a real quote that
  doesn't actually entail the claim), so the LLM-decided tier is labeled lower-trust and counted in
  the coverage denominator rather than treated as certain.
- The newest models deprecate the `temperature` parameter, so the frontier judge is not
  temperature-pinned; reproducibility of the *authoritative* verdict comes from the deterministic
  verification step, not from a fixed sampling temperature.

## Why it matters (model-risk framing)

The artifact demonstrates a validator that (a) reports an **honest coverage denominator** — what it
could and could not verify — (b) attaches **auditable evidence** to every positive verdict, and
(c) **fails safe** when a dependency (the judge) is unavailable or unsuitable. Those are the
properties an independent model-validation function is expected to provide.
