"""
Pydantic models for parent management.
"""

from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class ParentCreate(BaseModel):
    """Create new parent account."""
    user_id: UUID = Field(..., description="User account ID")
    title: Optional[str] = Field(None, max_length=20, description="Title (Mr, Mrs, Dr, etc.)")
    first_name: str = Field(..., min_length=2, max_length=100, description="First name")
    last_name: str = Field(..., min_length=2, max_length=100, description="Last name")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    email: EmailStr = Field(..., description="Email address")
    occupation: Optional[str] = Field(None, max_length=200, description="Occupation")
    address: Optional[str] = Field(None, description="Residential address")


class ParentUpdate(BaseModel):
    """Update parent information."""
    title: Optional[str] = Field(None, max_length=20)
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    occupation: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None


class ParentResponse(BaseModel):
    """Parent response with computed fields."""
    id: UUID
    user_id: UUID
    organization_id: UUID
    title: Optional[str] = None
    first_name: str
    last_name: str
    phone: str
    email: str
    occupation: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    full_name: Optional[str] = None
    children_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ParentStudentLinkCreate(BaseModel):
    """Link parent to student."""
    student_id: UUID = Field(..., description="Student ID")
    relationship: str = Field(..., min_length=3, max_length=50, description="Relationship (Father, Mother, Guardian)")
    is_primary: bool = Field(default=False, description="Is this the primary parent/guardian?")
    
    @field_validator('relationship')
    @classmethod
    def validate_relationship(cls, v):
        """Validate relationship."""
        valid_relationships = ['Father', 'Mother', 'Guardian', 'Uncle', 'Aunt', 'Grandfather', 'Grandmother', 'Other']
        if v not in valid_relationships:
            raise ValueError(f'Relationship must be one of: {", ".join(valid_relationships)}')
        return v


class ParentStudentLinkResponse(BaseModel):
    """Parent-student link response."""
    id: UUID
    parent_id: UUID
    student_id: UUID
    relationship: str
    is_primary: bool
    created_at: datetime
    
    # Computed fields
    student_name: Optional[str] = None
    parent_name: Optional[str] = None
    
    class Config:
        from_attributes = True
