import uuid
from typing import List
from fastapi import HTTPException, status
from app.repositories.branch_repository import BranchRepository
from app.schemas.branch import BranchCreateRequest, BranchUpdateRequest
from app.models.domain import Branch

class BranchService:
    def __init__(self, repository: BranchRepository):
        self.repository = repository

    async def create_branch(self, data: BranchCreateRequest) -> Branch:
        existing = await self.repository.get_by_code(data.code.upper())
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Branch code '{data.code}' already exists."
            )
        
        new_branch = Branch(
            name=data.name,
            code=data.code.upper(),
            total_seats=data.total_seats,
            available_seats=data.total_seats,  # Set equal to total capacity on boot
            cutoff_marks=data.cutoff_marks
        )
        return await self.repository.create(new_branch)

    async def get_branch(self, branch_id: uuid.UUID) -> Branch:
        branch = await self.repository.get_by_id(branch_id)
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found."
            )
        return branch

    async def list_branches(self) -> List[Branch]:
        return await self.repository.get_all()

    async def update_branch(self, branch_id: uuid.UUID, data: BranchUpdateRequest) -> Branch:
        branch = await self.get_branch(branch_id)
        
        if data.total_seats is not None:
            occupied_seats = branch.total_seats - branch.available_seats
            if data.total_seats < occupied_seats:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Cannot reduce capacity below occupied seats ({occupied_seats})."
                )
            # Implied balance calculation logic mapping
            branch.available_seats = data.total_seats - occupied_seats
            branch.total_seats = data.total_seats

        if data.name is not None:
            branch.name = data.name
        if data.cutoff_marks is not None:
            branch.cutoff_marks = data.cutoff_marks
        if data.code is not None:
            updated_code = data.code.upper()
            if updated_code != branch.code:
                existing = await self.repository.get_by_code(updated_code)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="New code value matches a duplicate entry profile."
                    )
                branch.code = updated_code

        return await self.repository.update(branch)


