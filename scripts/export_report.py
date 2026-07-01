#!/usr/bin/env python3
"""Export the validation report as JSON for the React dashboard (dashboard/public/report.json).

Run once to snapshot the current results:  python3 scripts/export_report.py
Uses whatever judge backend RAGASSURANCE_JUDGE selects (default: local Ollama).
"""
import datetime
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ragassurance.validation.faithfulness import GROUNDED, score_faithfulness
from ragassurance.validation.harness import run_grounding_eval as run_validation

report = run_validation(score_faithfulness)
catch, n_bad = report.hallucination_catch()
flags, n_ok = report.false_flags()
n_pass = sum(1 for o in report.outcomes if o.result.verdict == GROUNDED)

data = {
    "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "backend": os.environ.get("RAGASSURANCE_JUDGE", "ollama"),
    "domain": "clinical / pharma",
    "metrics": {
        "accuracy": [report.n_correct, report.n],
        "hallucination_catch": [catch, n_bad],
        "false_flags": [flags, n_ok],
        "coverage": [report.adjudicated, report.n],
        "gate_pass": [n_pass, report.n],
    },
    "cases": [
        {
            "id": o.case.id,
            "question": o.case.question,
            "verdict": o.result.verdict,
            "gold": o.case.gold,
            "correct": o.correct,
            "gate_pass": o.result.verdict == GROUNDED,
            "score": round(o.result.score, 3),
            "supported": len(o.result.supported_claims),
            "unsupported": len(o.result.unsupported_claims),
            "deferred": len(o.result.deferred_claims),
            "tiers": o.result.tiers,
            "note": o.result.note,
            "why": o.case.why,
        }
        for o in report.outcomes
    ],
}

out = ROOT / "dashboard" / "public" / "report.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, indent=2))
print("wrote", out)
print("metrics:", data["metrics"])
