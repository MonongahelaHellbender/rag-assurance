"""The RAG pipeline = the SYSTEM UNDER VALIDATION.

retrieve -> assemble context -> generate. Deliberately thin: the value of this project is the
VALIDATION of the pipeline's outputs (see ragassurance.eval), not the pipeline itself.
"""
from __future__ import annotations

from dataclasses import dataclass

from .corpus import Passage
from .generator import FixtureGenerator, Generator
from .retriever import TfidfRetriever


@dataclass
class RagResult:
    question: str
    retrieved: list[Passage]
    answer: str

    @property
    def context_text(self) -> str:
        return "\n\n".join(p.text for p in self.retrieved)


class RagPipeline:
    def __init__(
        self,
        retriever: TfidfRetriever | None = None,
        generator: Generator | None = None,
        k: int = 3,
    ) -> None:
        self.retriever = retriever or TfidfRetriever()
        self.generator = generator or FixtureGenerator()
        self.k = k

    def answer(self, question: str) -> RagResult:
        passages = [s.passage for s in self.retriever.retrieve(question, self.k)]
        answer = self.generator.generate(question, passages)
        return RagResult(question=question, retrieved=passages, answer=answer)
