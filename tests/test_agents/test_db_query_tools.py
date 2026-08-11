# tests/test_track_b/test_query_tools.py
import pytest


@pytest.mark.asyncio
async def test_application_query_tools_status_tool_returns_error_dict_for_missing(
    db_session,
):
    import uuid

    from app.ai.tools.application_query_tools import build_application_query_tools

    tools = build_application_query_tools(db_session, uuid.uuid4())
    status_tool = next(
        t for t in tools if t.metadata.name == "get_student_application_status"
    )
    result = await status_tool.async_fn()
    assert result == {"error": "No application found."}


@pytest.mark.asyncio
async def test_application_query_tools_status_tool_returns_real_data(
    db_session, test_application
):
    from app.ai.tools.application_query_tools import build_application_query_tools

    tools = build_application_query_tools(db_session, test_application.id)
    status_tool = next(
        t for t in tools if t.metadata.name == "get_student_application_status"
    )
    result = await status_tool.async_fn()
    assert result["application_id"] == str(test_application.id)


@pytest.mark.asyncio
async def test_document_query_tools_pending_documents_lists_all_required_when_none_uploaded(
    db_session, test_application
):
    from app.ai.tools.document_query_tools import build_document_query_tools

    tools = build_document_query_tools(db_session, test_application.id)
    pending_tool = next(
        t for t in tools if t.metadata.name == "get_pending_or_missing_documents"
    )
    result = await pending_tool.async_fn()
    assert "CLASS12_MARKSHEET" in result
    assert "ID_CARD" in result


@pytest.mark.asyncio
async def test_offer_query_tools_no_offers_returns_empty_list(
    db_session, test_application
):
    from app.ai.tools.offer_query_tools import build_offer_query_tools

    tools = build_offer_query_tools(db_session, test_application.id)
    offers_tool = next(
        t for t in tools if t.metadata.name == "get_student_admission_offers"
    )
    result = await offers_tool.async_fn()
    assert result == []


@pytest.mark.asyncio
async def test_loan_query_tools_no_loan_returns_error_dict(
    db_session, test_application
):
    from app.ai.tools.loan_query_tools import build_loan_query_tools

    tools = build_loan_query_tools(db_session, test_application.id)
    loan_tool = next(t for t in tools if t.metadata.name == "get_student_loan_details")
    result = await loan_tool.async_fn()
    assert result == {"error": "No loan application found."}
