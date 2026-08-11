# scripts/ingest_branch_eligibility_index.py
from app.ai.rag.corpora import BRANCH_ELIGIBILITY_CORPUS
from app.ai.rag.index_builder import build_index

if __name__ == "__main__":
    build_index(BRANCH_ELIGIBILITY_CORPUS)
