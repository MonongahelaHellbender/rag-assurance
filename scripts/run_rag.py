#!/usr/bin/env python3
"""Run the RAG pipeline (the system under validation) and show what it retrieved and answered.

Default uses the deterministic FixtureGenerator (offline, no setup). Pass --ollama to generate
with a local Ollama model instead (requires `ollama serve`).
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ragassurance.generator import FixtureGenerator, OllamaGenerator
from ragassurance.pipeline import RagPipeline

DEMO_ANSWERS = {
    "What must source data be under GCP?": (
        "Under Good Clinical Practice, source data must be attributable, legible, contemporaneous, "
        "original, and accurate."
    ),
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?", default="What must source data be under GCP?")
    ap.add_argument("--ollama", action="store_true", help="generate with a local Ollama model")
    ap.add_argument("--model", default="qwen2.5-coder:7b")
    ap.add_argument("--langchain", action="store_true", help="retrieve with the langchain embedding retriever (needs .venv + an embed model)")
    args = ap.parse_args()

    retriever = None
    if args.langchain:
        from ragassurance.langchain_retriever import LangchainRetriever

        retriever = LangchainRetriever()
    generator = OllamaGenerator(model=args.model) if args.ollama else FixtureGenerator(DEMO_ANSWERS)
    result = RagPipeline(retriever=retriever, generator=generator).answer(args.question)

    print("Q:", result.question)
    print("\nRetrieved:")
    for p in result.retrieved:
        print(f"  - [{p.doc_id}] {p.text[:88]}...")
    print("\nAnswer:\n ", result.answer)
    print("\n-> validate this answer with:  python3 scripts/validate.py")
