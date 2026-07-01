#!/usr/bin/env python3
"""Run the strict faithfulness validation over the labeled cases and print the model-validation
summary plus the STRICT GATE (an answer passes only if fully grounded — a bad claim is a fail).

Judge backend is chosen by the RAGASSURANCE_JUDGE env var: 'ollama' (local default) or 'anthropic'
(frontier Claude — set ANTHROPIC_API_KEY). Example:
    python scripts/validate.py
    RAGASSURANCE_JUDGE=anthropic ANTHROPIC_API_KEY=sk-... python scripts/validate.py
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ragassurance.validation.faithfulness import DEFER, GROUNDED, score_faithfulness
from ragassurance.validation.harness import run_grounding_eval as run_validation
from ragassurance.validation.harness import validation_summary

if __name__ == "__main__":
    backend = os.environ.get("RAGASSURANCE_JUDGE", "ollama")
    print(f"judge backend: {backend}\n")

    report = run_validation(score_faithfulness)
    print(validation_summary(report))

    # STRICT GATE (regulated / high-stakes use): pass ONLY if fully grounded — a bad claim is a fail.
    print("\n--- STRICT GATE (pass only if fully GROUNDED) ---")
    passed = 0
    for o in report.outcomes:
        ok = o.result.verdict == GROUNDED
        passed += ok
        print(f"  [{'PASS' if ok else 'FAIL'}]  {o.case.id:22} verdict={o.result.verdict:12} {o.result.note}")
    print(f"  gate pass-rate: {passed}/{report.n}  (only fully-grounded answers may pass in strict industries)")

    if all(o.result.verdict == DEFER for o in report.outcomes):
        print(
            f"\n  note: every case DEFERed — the '{backend}' judge gave nothing usable: either it is "
            f"unreachable OR it isn't returning the strict JSON this judge requires (some models don't)."
            f"\n        see exactly what it returned:  RAGASSURANCE_JUDGE={backend} python3 scripts/debug_judge.py"
        )
