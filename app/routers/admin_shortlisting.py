from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_officer  # adjust name if different
from app.core.factories import get_shortlisting_service
from app.models.domain import Officer
from app.services.shortlisting.shortlisting_service import ShortlistingService


router = APIRouter(prefix="/admin", tags=["admin"])



#========================================= TRIGGER SHORTLISTING ROUND ===============================================

@router.post("/rounds/{round_number}/shortlist")
async def trigger_shortlisting_round(
    round_number: int,
    db: AsyncSession = Depends(get_db),
    current_officer: Officer=Depends(get_current_officer),
    shortlisting_service: ShortlistingService = Depends(get_shortlisting_service),
):
    try:
        result = await shortlisting_service.run_shortlisting_round(round_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result

