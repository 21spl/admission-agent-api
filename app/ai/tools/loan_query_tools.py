# app/ai/tools/loan_query_tools.py

from llama_index.core.tools import FunctionTool

from app.core.factories import get_loan_service


def build_loan_query_tools(db, application_id) -> list[FunctionTool]:
    loan_service = get_loan_service(db)

    async def get_my_loan_application() -> dict:
        """Get the loan application status for the logged-in student, if one exists."""
        loan = await loan_service.get_loan_application_by_application_id(application_id)
        if loan is None:
            return {"error": "No loan application found."}
        return {"loan_id": str(loan.id), "status": loan.status}

    return [
        FunctionTool.from_defaults(
            async_fn=get_my_loan_application,
            name="get_student_loan_details",
            description="Fetches processing/approval status of the logged-in student's education loan application.",
        ),
    ]
