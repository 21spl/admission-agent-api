import uuid
from typing import Optional
from pydantic import BaseModel, Field

class BranchCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=20)
    total_seats: int = Field(..., gt=0)
    cutoff_marks: Optional[float] = Field(None, ge=0.0, le=100.0)

class BranchUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=20)
    total_seats: Optional[int] = Field(None, gt=0)
    cutoff_marks: Optional[float] = Field(None, ge=0.0, le=100.0)

class BranchResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    total_seats: int
    available_seats: int
    cutoff_marks: Optional[float]

    class Config:
        from_attributes = True