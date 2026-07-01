"""Offline tests for judge_claim — the deterministic tier and the fail-closed guarantee.

The live LLM (tier 2) path needs a running model, so it isn't unit-tested here; these tests prove
the parts that must hold regardless: deterministic support is real, and anything unverifiable
DEFERs instead of guessing.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ragassurance.validation.judge import DEFER, SUPPORTED, _quote_in_context, judge_claim


def test_quote_verification_is_deterministic():
    ctx = "A monitoring signal is an early warning. A flagged result triggers human investigation."
    assert _quote_in_context("A monitoring signal is an early warning", ctx)
    assert not _quote_in_context("the model retrains automatically", ctx)


def test_deterministic_support_when_claim_in_context():
    ctx = "Validation rests on three pillars: conceptual soundness, ongoing monitoring, and outcomes analysis."
    j = judge_claim("Validation rests on three pillars", ctx)
    assert j.verdict == SUPPORTED
    assert j.tier == "deterministic"
    assert j.evidence  # carries the verifying evidence


def test_fail_closed_when_llm_unreachable():
    # the deterministic tier can't resolve this; point at a dead host -> DEFER, never a guess
    j = judge_claim(
        "Independent assessors may reject the model.",
        "Effective challenge lets reviewers turn down a model.",
        host="http://localhost:1",
        timeout=1.0,
    )
    assert j.verdict == DEFER
    assert j.tier == "defer"
