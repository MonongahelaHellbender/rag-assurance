"""FAITHFULNESS SCORING — strict, claim-level, fail-closed.

Policy (Melissa's call, for high-stakes / regulated use): **A BAD CLAIM IS A FAIL.** An answer is
GROUNDED only if EVERY claim is verified supported. Any unsupported claim fails the answer; any
claim that cannot be verified (DEFER) routes to a human — it does not pass the gate.

Per-claim adjudication is delegated to `judge.judge_claim` (deterministic-first, then an LLM that
must cite verifiable evidence, fail-closed; local Ollama or a frontier model). This module owns the
two assurance decisions: how to SPLIT the answer into claims, and how to AGGREGATE per-claim
verdicts under the strict policy.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .judge import DEFER as _CLAIM_DEFER
from .judge import SUPPORTED as _CLAIM_SUPPORTED
from .judge import UNSUPPORTED as _CLAIM_UNSUPPORTED
from .judge import judge_claim

GROUNDED = "GROUNDED"        # every claim verified supported — the ONLY pass
UNSUPPORTED = "UNSUPPORTED"  # no claim supported
PARTIAL = "PARTIAL"          # some supported, some not — still a FAIL under the strict gate
DEFER = "DEFER"              # nothing unsupported, but something unverifiable — route to a human

_SENTENCE = re.compile(r"(?<=[.;])\s+")


@dataclass
class FaithfulnessResult:
    verdict: str
    score: float                                          # fraction of claims verified supported
    supported_claims: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    deferred_claims: list[str] = field(default_factory=list)
    tiers: list[str] = field(default_factory=list)        # trust bases used (deterministic/llm-verified/…)
    note: str = ""


def split_into_claims(answer: str) -> list[str]:
    """Split an answer into claim-sized units. Sentence boundaries are a sound first cut."""
    return [s.strip() for s in _SENTENCE.split(answer.strip()) if s.strip()]


def score_faithfulness(answer: str, retrieved_context: str, judge=judge_claim) -> FaithfulnessResult:
    """Strict faithfulness verdict for one answer — 'a bad claim is a fail'.

    GROUNDED  iff every claim is verified supported   (the only PASS)
    UNSUPPORTED  if no claim is supported
    PARTIAL      if some claims supported and some unsupported  (FAILS the strict gate)
    DEFER        if nothing is unsupported but something can't be verified (human review)

    `judge` is injectable so the aggregation can be unit-tested without a live model.
    """
    claims = split_into_claims(answer)
    if not claims:
        return FaithfulnessResult(DEFER, 0.0, note="empty answer")

    judgments = [judge(c, retrieved_context) for c in claims]
    supported = [c for c, j in zip(claims, judgments) if j.verdict == _CLAIM_SUPPORTED]
    unsupported = [c for c, j in zip(claims, judgments) if j.verdict == _CLAIM_UNSUPPORTED]
    deferred = [c for c, j in zip(claims, judgments) if j.verdict == _CLAIM_DEFER]
    tiers = sorted({j.tier for j in judgments})

    if unsupported:
        verdict = PARTIAL if supported else UNSUPPORTED   # any bad claim -> fail
    elif deferred:
        verdict = DEFER                                   # can't certify -> human review (not a pass)
    else:
        verdict = GROUNDED                                # every claim verified

    note = (
        f"{len(supported)} supported / {len(unsupported)} unsupported / "
        f"{len(deferred)} unverifiable across {len(claims)} claim(s)"
    )
    return FaithfulnessResult(
        verdict,
        len(supported) / len(claims),
        supported_claims=supported,
        unsupported_claims=unsupported,
        deferred_claims=deferred,
        tiers=tiers,
        note=note,
    )
