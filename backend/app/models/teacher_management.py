"""
Pydantic models for advanced teacher management features.
Includes: teacher-class assignments, form teacher roles, remarks, and reports.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal


# ============================================
# GRADING SCHEMES
# ============================================

class GradingSchemeComponentCreate(BaseModel):
    """Create grading scheme component."""
    component_type: str = Field(..., max_length=50, description="Type: 'test', 'coursework', 'exam', 'assignment'")
    component_name: str = Field(..., min_length=2, max_length=100, description="e.g., 'Test 1', 'Coursework', 'Final Exam'")
    weight_percentage: Decimal = Field(..., gt=0, le=100, description="Weight percentage (0 < x <= 100)")
    max_score: Decimal = Field(default=100, ge=0, description="Maximum possible score")
    required: bool = Field(default=True, description="Is this component mandatory?")
    display_order: int = Field(default=0, description="Display order in UI")
    
    @field_validator('component_type')
    @classmethod
    def validate_component_type(cls, v):
        """Validate component type."""
        valid_types = ['test', 'coursework', 'exam', 'assignment', 'project', 'other']
        if v not in valid_types:
            raise ValueError(f'Component type must be one of: {", ".join(valid_types)}')
        return v


class GradingSchemeComponentResponse(GradingSchemeComponentCreate):
    """Response with grading scheme component details."""
    id: UUID
    grading_scheme_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class GradingSchemeCreate(BaseModel):
    """Create grading scheme."""
    session_id: UUID = Field(..., description="Academic session ID")
    name: str = Field(..., min_length=3, max_length=100, description="e.g., '20-20-60', '20-20-20-40'")
    description: Optional[str] = Field(None, description="Description of the grading scheme")
    is_default: bool = Field(default=False, description="Set as default for school?")
    components: List[GradingSchemeComponentCreate] = Field(..., min_items=1, description="Grading components")
    
    @field_validator('components')
    @classmethod
    def validate_components_sum(cls, v):
        """Ensure components sum to 100% (or close to it)."""
        total = sum(c.weight_percentage for c in v)
        if abs(total - 100) > 0.01:  # Allow small rounding errors
            raise ValueError(f'Component weights must sum to 100%, got {total}%')
        return v


class GradingSchemeUpdate(BaseModel):
    """Update grading scheme."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class GradingSchemeResponse(BaseModel):
    """Response with grading scheme details."""
    id: UUID
    organization_id: UUID
    session_id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    components: Optional[List[GradingSchemeComponentResponse]] = []
    
    class Config:
        from_attributes = True


# ============================================
# CLASS SUBJECTS
# ============================================

class ClassSubjectCreate(BaseModel):
    """Add subject to class."""
    class_id: UUID = Field(..., description="Class ID")
    subject_id: UUID = Field(..., description="Subject ID")
    session_id: UUID = Field(..., description="Academic session ID")
    is_mandatory: bool = Field(default=True, description="Is this a mandatory subject?")
    display_order: int = Field(default=0, description="Display order")


class ClassSubjectUpdate(BaseModel):
    """Update class subject."""
    is_mandatory: Optional[bool] = None
    display_order: Optional[int] = None


class ClassSubjectResponse(BaseModel):
    """Response with class-subject details."""
    id: UUID
    class_id: UUID
    subject_id: UUID
    session_id: UUID
    is_mandatory: bool
    display_order: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    subject_name: Optional[str] = None
    class_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# TEACHER CLASS ASSIGNMENTS
# ============================================

class TeacherClassAssignmentCreate(BaseModel):
    """Assign teacher to class and subject."""
    teacher_id: UUID = Field(..., description="Teacher ID")
    class_id: UUID = Field(..., description="Class ID")
    subject_id: UUID = Field(..., description="Subject ID")
    session_id: UUID = Field(..., description="Academic session ID")
    term_id: Optional[UUID] = Field(None, description="Term ID (optional)")
    is_form_teacher: bool = Field(default=False, description="Is this teacher the form teacher?")


class TeacherClassAssignmentUpdate(BaseModel):
    """Update teacher class assignment."""
    is_form_teacher: Optional[bool] = None
    term_id: Optional[UUID] = None


class TeacherClassAssignmentResponse(BaseModel):
    """Response with teacher class assignment details."""
    id: UUID
    teacher_id: UUID
    class_id: UUID
    subject_id: UUID
    session_id: UUID
    term_id: Optional[UUID] = None
    is_form_teacher: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    teacher_name: Optional[str] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# CLASS WITH SUBJECTS & TEACHERS
# ============================================

class ClassDetailedResponse(BaseModel):
    """Class response with subjects and teachers."""
    id: UUID
    organization_id: UUID
    name: str
    level: str
    section: Optional[str] = None
    capacity: int
    class_teacher_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    student_count: Optional[int] = 0
    class_teacher_name: Optional[str] = None
    subjects: Optional[List[ClassSubjectResponse]] = []
    teachers: Optional[List[TeacherClassAssignmentResponse]] = []
    
    class Config:
        from_attributes = True


# ============================================
# STUDENT REMARKS
# ============================================

class StudentRemarkCreate(BaseModel):
    """Add remark to student report card."""
    student_id: UUID = Field(..., description="Student ID")
    class_id: UUID = Field(..., description="Class ID")
    session_id: UUID = Field(..., description="Academic session ID")
    term_id: UUID = Field(..., description="Term ID")
    remark_text: str = Field(..., min_length=5, max_length=1000, description="Remark text")
    remarks_category: str = Field(default='general', description="Category: 'conduct', 'academic', 'general'")
    
    @field_validator('remarks_category')
    @classmethod
    def validate_category(cls, v):
        """Validate remark category."""
        valid_categories = ['conduct', 'academic', 'general', 'behavioral', 'performance']
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {", ".join(valid_categories)}')
        return v


class StudentRemarkUpdate(BaseModel):
    """Update student remark."""
    remark_text: Optional[str] = Field(None, min_length=5, max_length=1000)
    remarks_category: Optional[str] = None


class StudentRemarkResponse(BaseModel):
    """Response with student remark details."""
    id: UUID
    student_id: UUID
    class_id: UUID
    session_id: UUID
    term_id: UUID
    form_teacher_id: UUID
    remark_text: str
    remarks_category: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    student_name: Optional[str] = None
    form_teacher_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# SCHOOL REPORTS
# ============================================

class SchoolReportCreate(BaseModel):
    """Create school report."""
    class_id: UUID = Field(..., description="Class ID")
    session_id: UUID = Field(..., description="Academic session ID")
    term_id: UUID = Field(..., description="Term ID")
    report_type: str = Field(..., description="Type: 'term_result', 'conduct', 'performance', 'special'")
    parent_ids: List[UUID] = Field(..., min_items=1, description="Parent IDs to send report to")
    
    @field_validator('report_type')
    @classmethod
    def validate_report_type(cls, v):
        """Validate report type."""
        valid_types = ['term_result', 'conduct', 'performance', 'special', 'attendance', 'behavioral']
        if v not in valid_types:
            raise ValueError(f'Report type must be one of: {", ".join(valid_types)}')
        return v


class SchoolReportUpdate(BaseModel):
    """Update school report."""
    report_type: Optional[str] = None


class SchoolReportRecipientResponse(BaseModel):
    """Response with report recipient details."""
    id: UUID
    report_id: UUID
    parent_id: UUID
    student_id: Optional[UUID] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    delivery_status: str
    
    # Computed fields
    parent_name: Optional[str] = None
    student_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class SchoolReportResponse(BaseModel):
    """Response with school report details."""
    id: UUID
    organization_id: UUID
    class_id: UUID
    session_id: UUID
    term_id: UUID
    report_type: str
    form_teacher_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    class_name: Optional[str] = None
    form_teacher_name: Optional[str] = None
    recipients: Optional[List[SchoolReportRecipientResponse]] = []
    
    class Config:
        from_attributes = True


# ============================================
# BULK REPORT SENDING
# ============================================

class BulkReportSend(BaseModel):
    """Send reports to multiple parents at once."""
    class_id: UUID = Field(..., description="Class ID")
    session_id: UUID = Field(..., description="Academic session ID")
    term_id: UUID = Field(..., description="Term ID")
    report_type: str = Field(..., description="Report type")
    include_all_parents: bool = Field(default=False, description="Send to all parents of class students?")
    parent_ids: Optional[List[UUID]] = Field(None, description="Specific parent IDs (if not include_all_parents)")
