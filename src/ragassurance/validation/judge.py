"""judge_claim — UNTRUSTED PROPOSER + DETERMINISTIC VERIFIER for a single claim.

Soundness model (the same one as oracle-shield): the LLM never has the final say. A claim is
returned SUPPORTED only when backed by evidence THIS module can verify deterministically:

    tier 1 "deterministic"  — the claim text (or all its content words) is literally present in
                              the context. No model involved.
    tier 2 "llm-verified"   — the LLM PROPOSES support and quotes a sentence; we then check that
                              the quote actually occurs in the context. Fabricated evidence is
                              rejected.
    otherwise               — DEFER (fail-closed). Unreachable model, unparseable output, an
                              unverifiable quote, or "unsure" all degrade to DEFER, never a guess.

Consequence: an LLM mistake can only lower COVERAGE (more DEFERs). It can never flip SOUNDNESS,
because no path returns SUPPORTED without verified evidence. Reproducibility is pinned with
temperature=0 and a fixed seed; the remaining LLM jitter can only move a verdict to DEFER.

Use it from `score_faithfulness`: split the answer into claims, call `judge_claim` on each, then
apply YOUR aggregation policy (all SUPPORTED -> GROUNDED, none -> UNSUPPORTED, mix -> PARTIAL,
unresolved -> DEFER) and report the per-claim `tier` as the trust basis.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

SUPPORTED = "SUPPORTED"
UNSUPPORTED = "UNSUPPORTED"
DEFER = "DEFER"

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^a-z0-9 ]")


@dataclass
class ClaimJudgment:
    verdict: str            # SUPPORTED | UNSUPPORTED | DEFER
    tier: str               # "deterministic" | "llm-verified" | "llm" | "defer"
    evidence: str = ""      # the verifying context sentence/quote — auditable
    note: str = ""


def _norm(text: str) -> str:
    return _WS.sub(" ", _PUNCT.sub(" ", text.lower())).strip()


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.;])\s+", text) if s.strip()]


def _quote_in_context(quote: str, context: str) -> bool:
    """Deterministic: is the normalized quote actually a substring of the normalized context?"""
    q = _norm(quote)
    return len(q) >= 12 and q in _norm(context)


# ── tier 1: deterministic (no model) ─────────────────────────────────────────────

def _deterministic(claim: str, context: str) -> ClaimJudgment | None:
    nclaim = _norm(claim)
    if len(nclaim) < 8:
        return None
    if nclaim in _norm(context):
        return ClaimJudgment(SUPPORTED, "deterministic", claim, "claim text occurs verbatim in context")
    claim_words = set(nclaim.split())
    for sentence in _sentences(context):
        if claim_words and claim_words <= set(_norm(sentence).split()):
            return ClaimJudgment(SUPPORTED, "deterministic", sentence, "claim's content words are a subset of one context sentence")
    return None


# ── tier 2: LLM proposer, deterministically verified ─────────────────────────────

_JUDGE_PROMPT = (
    "You are a strict grounding checker. Decide whether the CLAIM is fully supported by the CONTEXT.\n"
    'Reply with ONLY a JSON object: {{"supported": true or false, "quote": "<exact sentence copied '
    'from the context that supports the claim, or an empty string>"}}.\n'
    "Do not infer beyond the context. If the context does not clearly support the claim, set "
    "supported to false.\n\nCONTEXT:\n{context}\n\nCLAIM:\n{claim}\n\nJSON:"
)


def _ask_ollama(prompt: str, model: str, host: str, timeout: float) -> str:
    payload = json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0, "seed": 0}}
    ).encode()
    req = urllib.request.Request(
        host + "/api/generate", data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (local, trusted host)
        return json.loads(resp.read())["response"]


def _ask_anthropic(prompt: str, model: str, timeout: float) -> str:
    """Frontier judge via the Anthropic API. Reads ANTHROPIC_API_KEY from the environment — the
    key is never stored in code. Only send the SYNTHETIC / public corpus this way; never confidential
    data (that egresses to the API)."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        data = json.loads(resp.read())
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def _extract_json(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def judge_claim(
    claim: str,
    context: str,
    backend: str | None = None,
    model: str | None = None,
    host: str = "http://localhost:11434",
    timeout: float = 60.0,
) -> ClaimJudgment:
    """Adjudicate one claim against the context — fail-closed, evidence-verified.

    backend: 'ollama' (local default) or 'anthropic' (frontier Claude; needs ANTHROPIC_API_KEY).
    If not passed, reads env var RAGASSURANCE_JUDGE, else 'ollama'. Either way, an unavailable
    backend (no key, network down, bad output) degrades to DEFER — never a guess.
    """
    decided = _deterministic(claim, context)
    if decided is not None:
        return decided

    backend = backend or os.environ.get("RAGASSURANCE_JUDGE", "ollama")
    prompt = _JUDGE_PROMPT.format(context=context, claim=claim)
    try:
        if backend == "anthropic":
            raw = _ask_anthropic(prompt, model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"), timeout)
        else:
            raw = _ask_ollama(prompt, model or "qwen2.5-coder:7b", host, timeout)
    except (urllib.error.URLError, OSError, TimeoutError, RuntimeError) as exc:
        return ClaimJudgment(DEFER, "defer", note=f"{backend} judge unavailable ({type(exc).__name__}) — fail-closed")

    parsed = _extract_json(raw)
    if not parsed or "supported" not in parsed:
        return ClaimJudgment(DEFER, "defer", note="unparseable judge output — fail-closed")

    if parsed.get("supported") is True:
        quote = str(parsed.get("quote", ""))
        if _quote_in_context(quote, context):
            return ClaimJudgment(SUPPORTED, "llm-verified", quote, "LLM-proposed quote verified present in context")
        return ClaimJudgment(DEFER, "defer", note="LLM claimed support but its quote is not in the context — rejected")
    if parsed.get("supported") is False:
        return ClaimJudgment(UNSUPPORTED, "llm", note="LLM judged the claim not supported")
    return ClaimJudgment(DEFER, "defer", note="LLM unsure — fail-closed")
