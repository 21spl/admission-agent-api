import uuid
from typing import List
from fastapi import APIRouter, Depends, status

from app.core.factories import get_branch_service
from app.services.branch_service import BranchService
from app.schemas.branch import BranchCreateRequest, BranchUpdateRequest, BranchResponse
from app.core.dependencies import RoleGuard
from app.models.enums import OfficerRole
from app.models.domain import Officer

router = APIRouter(prefix="/branches", tags=["Branch Management"])

# ==============================================================================
# UNPROTECTED PUBLIC ENDPOINTS (No Authentication Required)
# ==============================================================================

@router.get("", response_model=List[BranchResponse], status_code=status.HTTP_200_OK)
async def list_all_branches(
    service: BranchService = Depends(get_branch_service)
):
    """
    Public Endpoint: Retrieves a list of all university branches 
    including total and current available seat metrics.
    """
    return await service.list_branches()


@router.get("/{branch_id}", response_model=BranchResponse, status_code=status.HTTP_200_OK)
async def get_single_branch(
    branch_id: uuid.UUID,
    service: BranchService = Depends(get_branch_service)
):
    """
    Public Endpoint: Fetches detailed structure information 
    for a single branch by its unique UUID.
    """
    return await service.get_branch(branch_id)


# ==============================================================================
# SECURED ADMINISTRATIVE ENDPOINTS (Admin Authorization Required)
# ==============================================================================

@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_new_branch(
    payload: BranchCreateRequest,
    service: BranchService = Depends(get_branch_service),
    current_admin: Officer = Depends(RoleGuard([OfficerRole.ADMIN]))
):
    """
    Secured Endpoint: Restricted strictly to platform Administrators.
    Creates a fresh branch infrastructure track.
    """
    return await service.create_branch(payload)


@router.patch("/{branch_id}", response_model=BranchResponse, status_code=status.HTTP_200_OK)
async def modify_existing_branch(
    branch_id: uuid.UUID,
    payload: BranchUpdateRequest,
    service: BranchService = Depends(get_branch_service),
    current_admin: Officer = Depends(RoleGuard([OfficerRole.ADMIN]))
):
    """
    Secured Endpoint: Restricted strictly to platform Administrators.
    Performs partial data mutations on specific branch capacity configurations.
    """
    return await service.update_branch(branch_id, payload)


