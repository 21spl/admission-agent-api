# scripts/ingest_loan_policy_index.py
from app.ai.rag.index_builder import build_index
from app.ai.rag.corpora import LOAN_POLICY_CORPUS

if __name__ == "__main__":
    build_index(LOAN_POLICY_CORPUS)