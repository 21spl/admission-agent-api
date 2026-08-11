# tests/test_track_b/test_rag_query_engines.py
"""
These hit the REAL pgvector tables and REAL Gemini API — they cost API
calls and require the four ingest_*.py scripts to have already been run
successfully at least once. Consider marking these to skip in fast/local
runs via a custom marker, e.g. @pytest.mark.integration, and only running
them explicitly or in CI on a schedule rather than every push.
"""
import pytest




pytestmark = [
    pytest.mark.asyncio(loop_scope="session"),
    pytest.mark.integration,
]

async def test_loan_policy_engine_answers_grounded_question():
    from app.ai.rag.query_engines import loan_policy_engine
    response = await loan_policy_engine.aquery("What documents are required for a loan application?")
    assert response is not None
    assert len(str(response)) > 0



async def test_policy_engine_does_not_hallucinate_on_out_of_scope_question():
    """
    Grounding check: a question with no answer in the policy corpus should
    produce a response indicating the info isn't available, not a confident
    fabrication. NOTE: this is a soft/fuzzy assertion — LLM output isn't
    exactly reproducible, so check for absence-signaling language rather
    than an exact string.
    """
    from app.ai.rag.query_engines import loan_policy_engine
    response = await loan_policy_engine.aquery(
        "What is the university's policy on campus parking permits?"
    )
    response_text = str(response).lower()
    assert any(phrase in response_text for phrase in [
        "not available", "does not contain", "contact", "cannot find",
    ])