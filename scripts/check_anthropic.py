#!/usr/bin/env python3
"""Diagnose the Anthropic (frontier) judge connection — prints the REAL reason it fails, and lists
the model IDs your account can actually use.

Run with your personal key:
    export ANTHROPIC_API_KEY=sk-ant-...your-real-key...
    python3 scripts/check_anthropic.py
Optionally override the model:
    ANTHROPIC_MODEL=claude-sonnet-5 python3 scripts/check_anthropic.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.anthropic.com/v1"
HEADERS_BASE = {"anthropic-version": "2023-06-01"}


def _get(path: str, key: str) -> dict:
    req = urllib.request.Request(API + path, headers={**HEADERS_BASE, "x-api-key": key})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


key = os.environ.get("ANTHROPIC_API_KEY")
print("ANTHROPIC_API_KEY present:", bool(key), f"(length {len(key)})" if key else "")
if not key:
    print("  -> not set. Run:  export ANTHROPIC_API_KEY=sk-ant-...   (your real key)")
    sys.exit(1)
if key.endswith("...") or len(key) < 40:
    print("  -> this looks like the PLACEHOLDER, not a real key. Paste your actual key.")
    sys.exit(1)

# 1) list the models this account/key can use
try:
    models = _get("/models", key).get("data", [])
    print("\nModels available to your account:")
    for m in models:
        print("  -", m.get("id"))
except urllib.error.HTTPError as exc:
    print(f"\nCould not list models — HTTP {exc.code} {exc.reason}")
    print(exc.read().decode()[:500])
    print("  401/403 = the key is bad or has no access. 400 = request issue.")
    sys.exit(1)
except Exception as exc:  # noqa: BLE001
    print("\nCould not reach the API:", type(exc).__name__, exc)
    sys.exit(1)

# 2) make one real judge-style call with the chosen model
model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
print(f"\nTesting a call with model: {model}")
body = json.dumps(
    {
        "model": model,
        "max_tokens": 64,
        "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
    }
).encode()
req = urllib.request.Request(
    API + "/messages",
    data=body,
    headers={**HEADERS_BASE, "content-type": "application/json", "x-api-key": key},
)
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    print("SUCCESS — model replied:", repr(text))
    print("\nGood to go. Run:")
    print(f"  RAGASSURANCE_JUDGE=anthropic ANTHROPIC_MODEL={model} python3 scripts/validate.py")
except urllib.error.HTTPError as exc:
    print(f"HTTP {exc.code} {exc.reason}")
    print(exc.read().decode()[:500])
    print("\n  404 = that model id isn't available — pick one from the list above and set ANTHROPIC_MODEL.")
    print("  401/403 = key problem.  400 = request issue.")
except Exception as exc:  # noqa: BLE001
    print("ERROR:", type(exc).__name__, exc)
