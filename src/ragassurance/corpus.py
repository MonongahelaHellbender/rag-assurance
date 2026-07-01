"""Load and chunk the local governance corpus.

The corpus is SYNTHETIC and copyright-free — short, original paraphrases of widely known
AI-governance concepts, authored for this project. Swap in real PUBLIC documents (e.g. the
NIST AI RMF, which is U.S.-government public domain) later; do not bundle copyrighted standards.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parents[2] / "corpus"


@dataclass(frozen=True)
class Passage:
    doc_id: str
    chunk_id: int
    text: str


def load_passages(corpus_dir: Path | None = None) -> list[Passage]:
    """Read every .md in the corpus dir; each non-heading paragraph becomes one passage."""
    directory = corpus_dir or CORPUS_DIR
    passages: list[Passage] = []
    for path in sorted(directory.glob("*.md")):
        blocks = [b.strip() for b in path.read_text(encoding="utf-8").split("\n\n") if b.strip()]
        chunk_id = 0
        for block in blocks:
            if block.startswith("#"):  # markdown heading — skip
                continue
            passages.append(Passage(path.stem, chunk_id, " ".join(block.split())))
            chunk_id += 1
    return passages
