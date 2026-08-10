# scripts/ingest_document_validation_index.py
from app.ai.rag.index_builder import build_index
from app.ai.rag.corpora import DOCUMENT_VALIDATION_POLICY_CORPUS

if __name__ == "__main__":
    build_index(DOCUMENT_VALIDATION_POLICY_CORPUS)