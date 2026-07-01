"""Answer generators for the RAG pipeline.

- FixtureGenerator: deterministic, offline — canned answers keyed by question. Increment 1 uses
  this so the whole pipeline + eval are reproducible with no model and no network.
- OllamaGenerator: optional real generator against a local Ollama server (you have one running).
  This is the increment-2 upgrade and is also the natural backend for an LLM-as-judge scorer.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Protocol

from .corpus import Passage


class Generator(Protocol):
    def generate(self, question: str, context: list[Passage]) -> str: ...


class FixtureGenerator:
    """Returns a canned answer for known questions; otherwise echoes the top passage."""

    def __init__(self, answers: dict[str, str] | None = None) -> None:
        self.answers = answers or {}

    def generate(self, question: str, context: list[Passage]) -> str:
        if question in self.answers:
            return self.answers[question]
        return context[0].text if context else "I don't have information on that."


class OllamaGenerator:
    """Optional: generate with a local Ollama model. Requires `ollama serve` (default port 11434)."""

    def __init__(self, model: str = "qwen2.5-coder:7b", host: str = "http://localhost:11434") -> None:
        self.model = model
        self.host = host

    def generate(self, question: str, context: list[Passage]) -> str:
        ctx = "\n\n".join(p.text for p in context)
        prompt = (
            "Answer the question using ONLY the context below. If the context does not contain the "
            f"answer, say you don't know.\n\nContext:\n{ctx}\n\nQuestion: {question}\nAnswer:"
        )
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request(
            self.host + "/api/generate", data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 (local, trusted host)
            return json.loads(resp.read())["response"].strip()
