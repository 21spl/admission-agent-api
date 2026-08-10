# scripts/ingest_offer_policy_index.py
"""Run: python -m scripts.ingest_offer_policy_index
Re-run whenever Offer and Shortlisting Policy.pdf changes."""
from app.ai.rag.index_builder import build_index
from app.ai.rag.corpora import OFFER_POLICY_CORPUS

if __name__ == "__main__":
    build_index(OFFER_POLICY_CORPUS)