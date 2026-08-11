# app/ai/tools/application_query_tools.py
from typing import List
from llama_index.core.tools import FunctionTool
from app.core.factories import get_application_service, get_application_history_service
from fastapi import HTTPException


def build_application_query_tools(db, application_id) -> List[FunctionTool]:
    application_service = get_application_service(db)
    application_history_service = get_application_history_service(db)

    async def get_my_application_status() -> dict:
        """Get the current status of the logged-in student's application."""
        try:
            app_ = await application_service.get_application_by_id(application_id)
        except HTTPException:
            return {"error": "No application found."}

        return {"application_id": str(app_.id), "status": app_.status}

    async def get_my_application_status_history() -> list[dict]:
        """Get the chronological status-change history for the logged-in student's application."""
        # the naming is get_history_for_officer because this signature requires application_id
        # there was another function called get_history_for_student which required student
        # so we chose to use get_history_for_officer
        history_list = await application_history_service.get_history_for_officer(application_id)
        return [
            {"timestamp": h.changed_at.isoformat(), "old_status": h.old_status, "new_status": h.new_status}
            for h in history_list
        ]

    async def inspect_validation_issue() -> dict:
            """Get validation issues/blockages currently flagged on this application's documents."""
            try:
                application = await application_service.get_application_by_id(application_id)
            except HTTPException:
                return {"error": "No application found."}

            return {"validation_issues": application.validation_issues}

    return [
        FunctionTool.from_defaults(async_fn=inspect_validation_issue, name="inspect_validation_issue",
            description="Get validation issues/blockages currently flagged on this application's documents."),
        FunctionTool.from_defaults(async_fn=get_my_application_status, name="get_student_application_status",
            description="Retrieves the current status of the logged-in student's application."),
        FunctionTool.from_defaults(async_fn=get_my_application_status_history, name="get_student_application_history",
            description="Retrieves the chronological status-change history of the logged-in student's application."),
    ]

