"""A small, dependency-free TF-IDF retriever over the governance corpus.

Pure stdlib so increment 1 runs with zero installs. In increment 2 this is the natural
swap point for a langchain vector-store retriever (embeddings) — the RagPipeline only needs
something with a `.retrieve(query, k)` method, so the interface stays put.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .corpus import Passage, load_passages

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


@dataclass
class Scored:
    passage: Passage
    score: float


class TfidfRetriever:
    def __init__(self, passages: list[Passage] | None = None) -> None:
        self.passages = passages if passages is not None else load_passages()
        self._toks = [_tokens(p.text) for p in self.passages]
        df: Counter[str] = Counter()
        for ts in self._toks:
            df.update(set(ts))
        n = len(self.passages)
        self.idf = {t: math.log((1 + n) / (1 + d)) + 1.0 for t, d in df.items()}

    def retrieve(self, query: str, k: int = 3) -> list[Scored]:
        q = _tokens(query)
        scored: list[Scored] = []
        for passage, ts in zip(self.passages, self._toks):
            tf = Counter(ts)
            score = sum(tf[t] * self.idf.get(t, 0.0) for t in q)
            scored.append(Scored(passage, score))
        scored.sort(key=lambda s: s.score, reverse=True)
        hits = [s for s in scored[:k] if s.score > 0]
        return hits or scored[:1]  # always return at least one passage
