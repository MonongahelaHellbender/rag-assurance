"""rag-assurance — build a small RAG system, then independently validate it.

The flagship pattern: a GenAI app is the SYSTEM UNDER VALIDATION; the eval harness
adjudicates whether its answers are grounded in the retrieved sources or hallucinated.
Increment 1 (this) = the offline validation core. See README.md for the roadmap.
"""
__version__ = "0.1.0"
