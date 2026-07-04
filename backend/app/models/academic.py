"""
Pydantic models for academic structure (sessions, terms, classes, subjects).
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
from uuid import UUID


# ============================================
# ACADEMIC SESSIONS
# ============================================

class AcademicSessionCreate(BaseModel):
    """Create new academic session."""
    name: str = Field(..., min_length=7, max_length=50, description="Session name (e.g., 2024/2025)")
    start_date: date = Field(..., description="Session start date")
    end_date: date = Field(..., description="Session end date")
    is_current: bool = Field(default=False, description="Is this the current session?")
    
    @field_validator('name')
    @classmethod
    def validate_session_name(cls, v):
        """Validate session name format (YYYY/YYYY)."""
        if '/' not in v or len(v.split('/')) != 2:
            raise ValueError('Session name must be in format YYYY/YYYY (e.g., 2024/2025)')
        return v
    
    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        """Ensure end date is after start date."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v


class AcademicSessionUpdate(BaseModel):
    """Update academic session."""
    name: Optional[str] = Field(None, min_length=7, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None


class AcademicSessionResponse(BaseModel):
    """Academic session response."""
    id: UUID
    organization_id: UUID
    name: str
    start_date: date
    end_date: date
    is_current: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================
# TERMS
# ============================================

class TermCreate(BaseModel):
    """Create new term."""
    session_id: UUID = Field(..., description="Academic session ID")
    name: str = Field(..., min_length=3, max_length=50, description="Term name (e.g., 1st Term)")
    term_number: int = Field(..., ge=1, le=3, description="Term number (1, 2, or 3)")
    start_date: date = Field(..., description="Term start date")
    end_date: date = Field(..., description="Term end date")
    is_current: bool = Field(default=False, description="Is this the current term?")
    
    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        """Ensure end date is after start date."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v


class TermUpdate(BaseModel):
    """Update term."""
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    term_number: Optional[int] = Field(None, ge=1, le=3)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None


class TermResponse(BaseModel):
    """Term response."""
    id: UUID
    session_id: UUID
    name: str
    term_number: int
    start_date: date
    end_date: date
    is_current: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================
# CLASSES
# ============================================

class ClassCreate(BaseModel):
    """Create new class."""
    name: str = Field(..., min_length=3, max_length=100, description="Class name (e.g., JSS 1, SS 2)")
    level: str = Field(..., min_length=3, max_length=50, description="Level (Junior, Senior, Primary)")
    section: Optional[str] = Field(None, max_length=10, description="Section (A, B, C, etc.)")
    capacity: int = Field(default=40, ge=1, le=200, description="Maximum number of students")
    class_teacher_id: Optional[UUID] = Field(None, description="Class teacher user ID")
    session_id: Optional[UUID] = Field(None, description="Academic session ID (required if subject_ids is set)")
    subject_ids: Optional[list[UUID]] = Field(default=None, description="Subjects to add to this class's curriculum")

    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        """Validate level."""
        valid_levels = ['Primary', 'Junior', 'Senior']
        if v not in valid_levels:
            raise ValueError(f'Level must be one of: {", ".join(valid_levels)}')
        return v


class ClassUpdate(BaseModel):
    """Update class."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    level: Optional[str] = Field(None, min_length=3, max_length=50)
    section: Optional[str] = Field(None, max_length=10)
    capacity: Optional[int] = Field(None, ge=1, le=200)
    class_teacher_id: Optional[UUID] = None


class ClassResponse(BaseModel):
    """Class response."""
    id: UUID
    organization_id: UUID
    name: str
    level: str
    section: Optional[str] = None
    capacity: int
    class_teacher_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Additional computed fields
    student_count: Optional[int] = 0
    class_teacher_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# SUBJECTS
# ============================================

class SubjectCreate(BaseModel):
    """Create new subject."""
    name: str = Field(..., min_length=2, max_length=100, description="Subject name")
    code: Optional[str] = Field(None, max_length=20, description="Subject code (e.g., MATH101)")
    subject_type: str = Field(default='core', description="Subject type (core or elective)")
    description: Optional[str] = Field(None, description="Subject description")
    
    @field_validator('subject_type')
    @classmethod
    def validate_subject_type(cls, v):
        """Validate subject type."""
        valid_types = ['core', 'elective']
        if v not in valid_types:
            raise ValueError(f'Subject type must be one of: {", ".join(valid_types)}')
        return v
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """Validate and uppercase subject code."""
        if v:
            return v.upper()
        return v


class SubjectUpdate(BaseModel):
    """Update subject."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    subject_type: Optional[str] = None
    description: Optional[str] = None


class SubjectResponse(BaseModel):
    """Subject response."""
    id: UUID
    organization_id: UUID
    name: str
    code: Optional[str] = None
    subject_type: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Additional computed fields
    teacher_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# ============================================
# SUBJECT ASSIGNMENTS (DEPRECATED - Use teacher_management.TeacherClassAssignment)
# ============================================

class SubjectAssignmentCreate(BaseModel):
    """Assign teacher to subject and class. DEPRECATED: Use TeacherClassAssignment."""
    teacher_id: UUID = Field(..., description="Teacher ID")
    subject_id: UUID = Field(..., description="Subject ID")
    class_id: UUID = Field(..., description="Class ID")
    session_id: UUID = Field(..., description="Academic session ID")
    term_id: Optional[UUID] = Field(None, description="Term ID (optional)")
    is_form_teacher: bool = Field(default=False, description="Is this the form teacher for the class?")


class SubjectAssignmentResponse(BaseModel):
    """Subject assignment response."""
    id: UUID
    teacher_id: UUID
    subject_id: UUID
    class_id: UUID
    session_id: UUID
    term_id: Optional[UUID] = None
    created_at: datetime
    
    # Additional computed fields
    teacher_name: Optional[str] = None
    subject_name: Optional[str] = None
    class_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# CLASS ENROLLMENTS
# ============================================

class ClassEnrollmentCreate(BaseModel):
    """Enroll student in class."""
    student_id: UUID = Field(..., description="Student ID")
    class_id: UUID = Field(..., description="Class ID")
    session_id: UUID = Field(..., description="Academic session ID")
    enrollment_date: date = Field(default_factory=date.today, description="Enrollment date")
    status: str = Field(default='active', description="Enrollment status")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate enrollment status."""
        valid_statuses = ['active', 'promoted', 'repeated', 'withdrawn']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class ClassEnrollmentUpdate(BaseModel):
    """Update enrollment."""
    class_id: Optional[UUID] = None
    status: Optional[str] = None
    enrollment_date: Optional[date] = None


class ClassEnrollmentResponse(BaseModel):
    """Class enrollment response."""
    id: UUID
    student_id: UUID
    class_id: UUID
    session_id: UUID
    enrollment_date: date
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Additional computed fields
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    
    class Config:
        from_attributes = True
