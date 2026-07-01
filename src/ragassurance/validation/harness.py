"""The validation harness: run a faithfulness scorer over the labeled cases and report how well
it separates grounded answers from hallucinations — framed as a model-validation summary.

The metrics are chosen for an assurance audience:
  * hallucination catch-rate = recall on unfaithful answers (the safety-critical number),
  * false-flag rate         = grounded answers wrongly rejected (the usability cost),
  * coverage                = fraction the scorer actually adjudicated (not DEFER) — the honest
                              denominator, the same idea as oracle-shield's coverage report.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .faithfulness import DEFER, GROUNDED, PARTIAL, UNSUPPORTED, FaithfulnessResult
from .fixtures import CASES, EvalCase

Scorer = Callable[[str, str], FaithfulnessResult]


@dataclass
class CaseOutcome:
    case: EvalCase
    result: FaithfulnessResult
    correct: bool


@dataclass
class EvalReport:
    outcomes: list[CaseOutcome]

    @property
    def n(self) -> int:
        return len(self.outcomes)

    @property
    def n_correct(self) -> int:
        return sum(o.correct for o in self.outcomes)

    @property
    def accuracy(self) -> float:
        return self.n_correct / self.n if self.n else 0.0

    @property
    def adjudicated(self) -> int:
        return sum(1 for o in self.outcomes if o.result.verdict != DEFER)

    def hallucination_catch(self) -> tuple[int, int]:
        gold_bad = [o for o in self.outcomes if o.case.gold == UNSUPPORTED]
        caught = [o for o in gold_bad if o.result.verdict in (UNSUPPORTED, PARTIAL)]
        return len(caught), len(gold_bad)

    def false_flags(self) -> tuple[int, int]:
        gold_ok = [o for o in self.outcomes if o.case.gold == GROUNDED]
        flagged = [o for o in gold_ok if o.result.verdict != GROUNDED]
        return len(flagged), len(gold_ok)


def run_grounding_eval(scorer: Scorer, cases: list[EvalCase] | None = None) -> EvalReport:
    cases = cases if cases is not None else CASES
    outcomes = []
    for c in cases:
        result = scorer(c.answer, c.retrieved_context)
        outcomes.append(CaseOutcome(c, result, result.verdict == c.gold))
    return EvalReport(outcomes)


def validation_summary(report: EvalReport) -> str:
    catch, n_bad = report.hallucination_catch()
    flags, n_ok = report.false_flags()
    lines = [
        "=== FAITHFULNESS VALIDATION SUMMARY ===",
        "system under validation: the RAG answerer  |  validator: score_faithfulness\n",
    ]
    for o in report.outcomes:
        tag = "PASS" if o.correct else "FAIL"
        lines.append(f"  [{tag}]  scored={o.result.verdict:11} gold={o.case.gold:11} {o.case.id}")
        if not o.correct:
            lines.append(f"          why this case exists: {o.case.why}")
    lines += [
        "",
        f"  accuracy              : {report.n_correct}/{report.n}",
        f"  hallucination catch   : {catch}/{n_bad}   (recall on unfaithful answers — safety-critical)",
        f"  false-flag rate       : {flags}/{n_ok}   (grounded answers wrongly rejected)",
        f"  coverage (adjudicated): {report.adjudicated}/{report.n}   (definite verdicts, not DEFER)",
        "",
        "  Assurance reading: a missed hallucination is a residual risk carried into production;",
        "  the coverage line is the honest denominator — what the validator could NOT adjudicate.",
    ]
    return "\n".join(lines)
