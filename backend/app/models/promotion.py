"""
Pydantic models for end-of-session promotion / graduation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class PromotionPreviewRow(BaseModel):
    """One student's computed promotion outcome, before anything is saved."""
    student_id: UUID
    student_name: str
    admission_number: str
    from_class_id: UUID
    from_class_name: str
    basis_score: Optional[float] = None
    pass_mark: float
    has_data: bool = Field(..., description="False if there's no report card to compute a score from")
    decision: str = Field(..., description="'promoted', 'repeated', or 'graduated' - the computed default")
    to_class_id: Optional[UUID] = None
    to_class_name: Optional[str] = None
    is_graduating_class: bool = False


class PromotionPreviewResponse(BaseModel):
    session_id: UUID
    promotion_basis: str
    default_pass_mark: float
    rows: List[PromotionPreviewRow]


class PromotionDecisionInput(BaseModel):
    """One row of the admin's final, possibly-overridden decision."""
    student_id: UUID
    decision: str = Field(..., description="'promoted', 'repeated', or 'graduated'")
    to_class_id: Optional[UUID] = Field(None, description="Required for 'promoted'; ignored otherwise")
    basis_score: Optional[float] = None
    override_reason: Optional[str] = Field(None, max_length=500)


class PromotionCommitRequest(BaseModel):
    session_id: UUID
    decisions: List[PromotionDecisionInput] = Field(..., min_length=1)


class PromotionCommitResultRow(BaseModel):
    student_id: UUID
    decision: str
    success: bool
    error: Optional[str] = None


class PromotionCommitResponse(BaseModel):
    session_id: UUID
    promoted: int
    repeated: int
    graduated: int
    failed: int
    results: List[PromotionCommitResultRow]


class PromotionRecordResponse(BaseModel):
    id: UUID
    organization_id: UUID
    session_id: UUID
    student_id: UUID
    from_class_id: Optional[UUID] = None
    to_class_id: Optional[UUID] = None
    decision: str
    basis_score: Optional[float] = None
    pass_mark_used: Optional[float] = None
    overridden: bool = False
    override_reason: Optional[str] = None
    decided_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True
