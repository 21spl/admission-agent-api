#query_engine.py

from llama_index.core import VectorStoreIndex
from llama_index.core.prompts import PromptTemplate

from app.ai.config import get_vector_store_instance, get_embedding_model
from app.ai.rag.corpora import (
    OFFER_POLICY_CORPUS,
    BRANCH_ELIGIBILITY_CORPUS,
    DOCUMENT_VALIDATION_POLICY_CORPUS,
    LOAN_POLICY_CORPUS,
)


def create_domain_prompt(domain_label: str) -> PromptTemplate:
    """
    One shared template, parameterized by domain, so all four engines
    enforce the same non-hallucination discipline instead of drifting
    if each were hand-written separately.
    """
    return PromptTemplate(
        "You are a specialist assistant for a university admissions helpdesk, "
        f"answering questions about {domain_label} using ONLY the official "
        "policy context below.\n\n"
        "Rules:\n"
        "- If the context does not contain the answer, say so explicitly and "
        "advise the student to contact the admissions office. Do NOT invent "
        "numbers, dates, deadlines, or rules not present in the context.\n"
        "- When you state a number (fee, deadline, seat count, interest "
        "rate, round number), quote it exactly as it appears in the context.\n"
        "- Be concise and structured. Use bullet points for multi-part answers.\n\n"
        "Context:\n{context_str}\n\n"
        "Student Question: {query_str}\n\n"
        "Answer:"
    )


def _load_query_engine(corpus, domain_label: str):
    """
    Loads the ALREADY-PERSISTED pgvector index for this corpus.
    Does NOT call build_index() — that only runs manually via scripts/ingest_*.py
    when the source PDF changes. Calling build_index() here would re-fetch
    from S3 and re-embed on every import, which is what caused the earlier bugs.
    """
    embed_model = get_embedding_model()
    vector_store = get_vector_store_instance(corpus.table_name)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

    return index.as_query_engine(
        text_qa_template=create_domain_prompt(domain_label),
        similarity_top_k=4,
    )


#========== Loan Policy Engine ==========================
loan_policy_engine = _load_query_engine(LOAN_POLICY_CORPUS, "student loan policy")

#========== Offer Policy Engine ==========================
offer_policy_engine = _load_query_engine(OFFER_POLICY_CORPUS, "offer and shortlisting policy")

#========== Document Validation Policy Engine ==========================
document_validation_policy_engine = _load_query_engine(DOCUMENT_VALIDATION_POLICY_CORPUS, "document and application validation policy")

#========== Branch Eligibility Engine ==========================
branch_eligibility_engine = _load_query_engine(BRANCH_ELIGIBILITY_CORPUS, "branch and eligibility")