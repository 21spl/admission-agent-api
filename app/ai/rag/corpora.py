from dataclasses import dataclass


@dataclass(frozen=True)
class CorpusConfig:
    storage_key: str
    table_name: str


# offer policy corpus
OFFER_POLICY_CORPUS = CorpusConfig(
    storage_key="admin-docs/offer-policy-docs/Offer and Shortlisting Policy.pdf",
    table_name="offer_policy_embeddings",
)

# branch eligibility corpus
BRANCH_ELIGIBILITY_CORPUS = CorpusConfig(
    storage_key="admin-docs/branch-eligibility-policy-docs/Branch-Eligibility policy.pdf",
    table_name="branch_eligibility_embeddings",
)

# document validation corpus
DOCUMENT_VALIDATION_POLICY_CORPUS = CorpusConfig(
    storage_key="admin-docs/document-policy-docs/Document_Submission_Verification_Policy.pdf",
    table_name="document_policy_embeddings",
)

# loan policy corpus
LOAN_POLICY_CORPUS = CorpusConfig(
    storage_key="admin-docs/loan-policy-docs/Student_Education_Loan_Policy.pdf",
    table_name="loan_policy_embeddings",
)
