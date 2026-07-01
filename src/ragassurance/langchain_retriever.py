"""A langchain-based retriever — real embeddings + a vector store — behind the SAME interface as
`TfidfRetriever`, so `RagPipeline` and the strict validator are unchanged.

This is the "production RAG" path (increment 2): documents are split, embedded, and stored in a
vector store; retrieval is embedding similarity rather than lexical overlap. It uses local Ollama
embeddings (free, no egress). Requires the langchain stack — install into the project venv:

    python3 -m venv .venv
    ./.venv/bin/pip install langchain-core langchain-ollama langchain-text-splitters
    ollama pull nomic-embed-text        # recommended embedder (or set RAGASSURANCE_EMBED_MODEL)
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from .corpus import Passage, load_passages


@dataclass
class Scored:
    passage: Passage
    score: float


class LangchainRetriever:
    def __init__(
        self,
        passages: list[Passage] | None = None,
        embed_model: str | None = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        from langchain_core.documents import Document
        from langchain_core.vectorstores import InMemoryVectorStore
        from langchain_ollama import OllamaEmbeddings
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        self.passages = passages if passages is not None else load_passages()
        model = embed_model or os.environ.get("RAGASSURANCE_EMBED_MODEL", "nomic-embed-text")
        embeddings = OllamaEmbeddings(model=model)
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        docs = []
        for p in self.passages:
            for chunk in splitter.split_text(p.text):
                docs.append(Document(page_content=chunk, metadata={"doc_id": p.doc_id}))
        self.store = InMemoryVectorStore.from_documents(docs, embeddings)

    def retrieve(self, query: str, k: int = 3) -> list[Scored]:
        hits = self.store.similarity_search_with_score(query, k=k)
        return [Scored(Passage(doc.metadata.get("doc_id", "?"), 0, doc.page_content), float(score)) for doc, score in hits]
