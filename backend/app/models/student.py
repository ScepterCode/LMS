"""
Pydantic models for student management.
"""

from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
from datetime import date, datetime
from uuid import UUID


# ============================================
# STUDENTS
# ============================================

class StudentCreate(BaseModel):
    """Create new student."""
    admission_number: str = Field(..., min_length=3, max_length=50, description="Unique admission number")
    first_name: str = Field(..., min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date = Field(..., description="Student's date of birth")
    gender: str = Field(..., description="Student's gender")
    blood_group: Optional[str] = Field(None, max_length=5)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    state_of_origin: Optional[str] = Field(None, max_length=100)
    lga: Optional[str] = Field(None, max_length=100, description="Local Government Area")
    nationality: str = Field(default="Nigerian", max_length=100)
    religion: Optional[str] = Field(None, max_length=50)
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    current_class_id: Optional[UUID] = Field(None, description="Current class ID")
    admission_date: date = Field(default_factory=date.today)
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        """Validate gender."""
        valid_genders = ['Male', 'Female', 'Other']
        if v not in valid_genders:
            raise ValueError(f'Gender must be one of: {", ".join(valid_genders)}')
        return v
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v):
        """Ensure student is not too young or too old."""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 2 or age > 25:
            raise ValueError('Student age must be between 2 and 25 years')
        return v


class StudentUpdate(BaseModel):
    """Update student."""
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = Field(None, max_length=5)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    state_of_origin: Optional[str] = Field(None, max_length=100)
    lga: Optional[str] = Field(None, max_length=100)
    nationality: Optional[str] = Field(None, max_length=100)
    religion: Optional[str] = Field(None, max_length=50)
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    current_class_id: Optional[UUID] = None
    status: Optional[str] = None


class StudentResponse(BaseModel):
    """Student response."""
    id: UUID
    organization_id: UUID
    admission_number: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: date
    gender: str
    blood_group: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    state_of_origin: Optional[str] = None
    lga: Optional[str] = None
    nationality: str
    religion: Optional[str] = None
    photo_url: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    current_class_id: Optional[UUID] = None
    admission_date: date
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    full_name: Optional[str] = None
    age: Optional[int] = None
    class_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# STUDENT GUARDIANS
# ============================================

class GuardianCreate(BaseModel):
    """Create guardian for student."""
    guardian_type: str = Field(..., description="Type of guardian")
    title: Optional[str] = Field(None, max_length=10)
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    relationship: str = Field(..., min_length=2, max_length=50)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    occupation: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    is_emergency_contact: bool = Field(default=True)
    is_primary: bool = Field(default=False)
    
    @field_validator('guardian_type')
    @classmethod
    def validate_guardian_type(cls, v):
        """Validate guardian type."""
        valid_types = ['father', 'mother', 'guardian', 'other']
        if v not in valid_types:
            raise ValueError(f'Guardian type must be one of: {", ".join(valid_types)}')
        return v


class GuardianUpdate(BaseModel):
    """Update guardian."""
    title: Optional[str] = Field(None, max_length=10)
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    relationship: Optional[str] = Field(None, min_length=2, max_length=50)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    occupation: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    is_emergency_contact: Optional[bool] = None
    is_primary: Optional[bool] = None


class GuardianResponse(BaseModel):
    """Guardian response."""
    id: UUID
    student_id: UUID
    guardian_type: str
    title: Optional[str] = None
    first_name: str
    last_name: str
    relationship: str
    phone: str
    email: Optional[str] = None
    occupation: Optional[str] = None
    address: Optional[str] = None
    is_emergency_contact: bool
    is_primary: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True
