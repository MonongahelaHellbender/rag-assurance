#!/usr/bin/env python3
"""Show EXACTLY what a judge backend returns for one claim — raw output, parsed JSON, final verdict.

Use it to see why a model DEFERs (e.g. it returns prose instead of the strict JSON the judge needs).
    RAGASSURANCE_JUDGE=anthropic ANTHROPIC_MODEL=claude-fable-5 python3 scripts/debug_judge.py
    python3 scripts/debug_judge.py        # local Ollama default
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ragassurance.validation import judge as J

CONTEXT = (
    "A drug's approved label describes the indications for which the drug has been shown to be safe "
    "and effective, the approved dosing, contraindications, warnings and precautions, and known "
    "adverse reactions."
)
CLAIM = "An approved drug label describes the indications, approved dosing, contraindications, and warnings."

backend = os.environ.get("RAGASSURANCE_JUDGE", "ollama")
default_model = "claude-sonnet-5" if backend == "anthropic" else "qwen2.5-coder:7b"
model = os.environ.get("ANTHROPIC_MODEL", default_model)
prompt = J._JUDGE_PROMPT.format(context=CONTEXT, claim=CLAIM)

print(f"backend={backend}  model={model}\n")
print("--- RAW MODEL OUTPUT ---")
try:
    if backend == "anthropic":
        raw = J._ask_anthropic(prompt, model, 60)
    else:
        raw = J._ask_ollama(prompt, model, "http://localhost:11434", 60)
    print(repr(raw))
    print("\n--- JSON the judge could extract ---")
    print(J._extract_json(raw))
except Exception as exc:  # noqa: BLE001
    print("ERROR:", type(exc).__name__, exc)

print("\n--- final judge_claim verdict ---")
result = J.judge_claim(CLAIM, CONTEXT)
print(f"verdict={result.verdict}  tier={result.tier}  note={result.note}")
