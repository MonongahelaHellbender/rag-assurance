"""Offline tests for the STRICT aggregation policy ('a bad claim is a fail').

The scorer's per-claim judgment is injected (a fake judge), so these test the AGGREGATION logic
deterministically without any live model. The live judge is covered separately by test_judge.py.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ragassurance.validation import faithfulness as F
from ragassurance.validation import judge as J
from ragassurance.validation.fixtures import CASES
from ragassurance.validation.harness import run_grounding_eval as run_checks
from ragassurance.validation.harness import validation_summary
from ragassurance.validation.judge import ClaimJudgment


def fake_judge(claim, context):
    """Marker-driven stand-in: 'BAD' -> unsupported, 'UNSURE' -> defer, else supported."""
    if "UNSURE" in claim:
        return ClaimJudgment(J.DEFER, "test")
    if "BAD" in claim:
        return ClaimJudgment(J.UNSUPPORTED, "test")
    return ClaimJudgment(J.SUPPORTED, "test")


def test_split_into_claims():
    assert F.split_into_claims("One thing. Two things.") == ["One thing.", "Two things."]


def test_all_supported_is_grounded():
    r = F.score_faithfulness("All fine. Also fine.", "ctx", judge=fake_judge)
    assert r.verdict == F.GROUNDED
    assert r.score == 1.0


def test_one_bad_claim_fails():
    r = F.score_faithfulness("All fine. This is BAD.", "ctx", judge=fake_judge)
    assert r.verdict == F.PARTIAL          # a bad claim fails the answer (mixed -> PARTIAL, still a fail)
    assert r.unsupported_claims


def test_all_bad_is_unsupported():
    r = F.score_faithfulness("This BAD. Also BAD.", "ctx", judge=fake_judge)
    assert r.verdict == F.UNSUPPORTED


def test_unverifiable_defers():
    r = F.score_faithfulness("All fine. This is UNSURE.", "ctx", judge=fake_judge)
    assert r.verdict == F.DEFER            # nothing bad, but can't certify -> human review


def test_fixtures_unique_ids():
    ids = [c.id for c in CASES]
    assert len(ids) == len(set(ids))


def test_harness_plumbing_offline():
    report = run_checks(lambda a, c: F.score_faithfulness(a, c, judge=fake_judge))
    assert report.n == len(CASES)
    text = validation_summary(report)
    assert "VALIDATION SUMMARY" in text
    assert "coverage" in text
