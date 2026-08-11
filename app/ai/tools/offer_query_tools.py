# app/ai/tools/offer_query_tools.py
from typing import List
from llama_index.core.tools import FunctionTool
from app.core.factories import get_offer_service, get_application_service, get_branch_service
from fastapi import HTTPException


def build_offer_query_tools(db, application_id) -> List[FunctionTool]:
    application_service = get_application_service(db)
    offer_service = get_offer_service(db, application_service)
    branch_service = get_branch_service(db)

    async def get_my_offers() -> list[dict]:
        """Get all branch/course offers extended to the logged-in student's application."""
        offer_list = await offer_service.list_offers_for_application(application_id)
        results = []
        for offer in offer_list:
            branch = await branch_service.get_branch(offer.branch_id)
            results.append({
                "offer_id": str(offer.id), "status": offer.status,
                "round_number": offer.round_number, "offered_branch": branch.name,
            })
        return results

    async def get_my_branch_preferences() -> list[dict]:
        """Get the logged-in student's ranked branch preferences and whether each was offered."""
        try:
            application = await application_service.get_application_by_id(application_id)
        except HTTPException:
            return [{"error": "No application found."}]
        
        results = []
        for pref in application.preferences:
            branch = await branch_service.get_branch(pref.branch_id)
            was_offered = await offer_service.check_branch_offered_to_student(application_id, pref.branch_id)
            results.append({
                "branch_name": branch.name, "preference_order": pref.preference_order,
                "was_offered": was_offered,
            })
        return results

    async def get_all_branch_details() -> list[dict]:
        """Get general info on all academic branches: names, codes, seats, cutoff marks."""
        branch_list = await branch_service.list_branches()
        return [
            {"branch_name": b.name, "branch_code": b.code, "total_seats": b.total_seats, "cutoff_marks": b.cutoff_marks}
            for b in branch_list
        ]

    return [
        FunctionTool.from_defaults(async_fn=get_my_offers, name="get_student_admission_offers",
            description="Fetches all branch/course offers extended to the logged-in student's application."),
        FunctionTool.from_defaults(async_fn=get_my_branch_preferences, name="get_student_branch_preferences",
            description="Lists the logged-in student's ranked branch preferences and offer status for each."),
        FunctionTool.from_defaults(async_fn=get_all_branch_details, name="get_all_academic_branch_details",
            description="Provides general info on all academic branches — names, codes, seats, cutoffs."),
    ]