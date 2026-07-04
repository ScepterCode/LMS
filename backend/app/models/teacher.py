"""
Pydantic models for teacher management.
"""

from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class TeacherCreate(BaseModel):
    """Create new teacher."""
    user_id: UUID = Field(..., description="User account ID")
    staff_number: str = Field(..., min_length=3, max_length=50, description="Staff number")
    first_name: str = Field(..., min_length=2, max_length=100, description="First name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")
    last_name: str = Field(..., min_length=2, max_length=100, description="Last name")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: str = Field(..., description="Gender (Male, Female, Other)")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, description="Residential address")
    state_of_origin: Optional[str] = Field(None, max_length=100, description="State of origin")
    lga: Optional[str] = Field(None, max_length=100, description="Local Government Area")
    nationality: str = Field(default='Nigerian', max_length=100, description="Nationality")
    qualification: Optional[str] = Field(None, max_length=200, description="Highest qualification")
    specialization: Optional[str] = Field(None, max_length=200, description="Subject specialization")
    employment_date: date = Field(default_factory=date.today, description="Employment start date")
    employment_type: str = Field(default='full-time', description="Employment type")
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        """Validate gender."""
        valid_genders = ['Male', 'Female', 'Other']
        if v not in valid_genders:
            raise ValueError(f'Gender must be one of: {", ".join(valid_genders)}')
        return v
    
    @field_validator('employment_type')
    @classmethod
    def validate_employment_type(cls, v):
        """Validate employment type."""
        valid_types = ['full-time', 'part-time', 'contract']
        if v not in valid_types:
            raise ValueError(f'Employment type must be one of: {", ".join(valid_types)}')
        return v
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_age(cls, v):
        """Validate teacher is at least 18 years old."""
        if v:
            today = date.today()
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if age < 18:
                raise ValueError('Teacher must be at least 18 years old')
            if age > 100:
                raise ValueError('Invalid date of birth')
        return v


class TeacherUpdate(BaseModel):
    """Update teacher information."""
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    address: Optional[str] = None
    state_of_origin: Optional[str] = Field(None, max_length=100)
    lga: Optional[str] = Field(None, max_length=100)
    nationality: Optional[str] = Field(None, max_length=100)
    qualification: Optional[str] = Field(None, max_length=200)
    specialization: Optional[str] = Field(None, max_length=200)
    employment_date: Optional[date] = None
    employment_type: Optional[str] = None
    status: Optional[str] = None
    photo_url: Optional[str] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status."""
        if v:
            valid_statuses = ['active', 'on-leave', 'terminated', 'retired']
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class TeacherResponse(BaseModel):
    """Teacher response with computed fields."""
    id: UUID
    user_id: UUID
    organization_id: UUID
    staff_number: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: Optional[date] = None
    gender: str
    email: str
    phone: str
    address: Optional[str] = None
    state_of_origin: Optional[str] = None
    lga: Optional[str] = None
    nationality: str
    photo_url: Optional[str] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    employment_date: date
    employment_type: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    full_name: Optional[str] = None
    age: Optional[int] = None
    years_of_service: Optional[int] = None
    subject_count: Optional[int] = 0
    assigned_classes: Optional[list] = []
    form_teacher_for: Optional[UUID] = None  # Class ID if form teacher, else None
    
    class Config:
        from_attributes = True

