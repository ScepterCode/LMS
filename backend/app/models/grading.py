"""
Pydantic models for Grading & Assessment System
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from decimal import Decimal


# ============================================
# ASSESSMENT TYPES
# ============================================

class AssessmentTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    max_score: Decimal = Field(default=100.00, ge=0, le=999.99)
    weight_percentage: Decimal = Field(default=0.00, ge=0, le=100)
    is_active: bool = True
    display_order: int = 0


class AssessmentTypeCreate(AssessmentTypeBase):
    pass


class AssessmentTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    max_score: Optional[Decimal] = Field(None, ge=0, le=999.99)
    weight_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class AssessmentType(AssessmentTypeBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# GRADE CONFIGURATION
# ============================================

class GradeConfigBase(BaseModel):
    grade_letter: str = Field(..., max_length=5)
    min_score: Decimal = Field(..., ge=0, le=100)
    max_score: Decimal = Field(..., ge=0, le=100)
    grade_point: Optional[Decimal] = Field(None, ge=0, le=5.0)
    remark: Optional[str] = Field(None, max_length=50)
    color_code: Optional[str] = Field(None, max_length=10)
    is_passing: bool = True
    display_order: int = 0

    @validator('max_score')
    def validate_score_range(cls, v, values):
        if 'min_score' in values and v < values['min_score']:
            raise ValueError('max_score must be greater than or equal to min_score')
        return v


class GradeConfigCreate(GradeConfigBase):
    pass


class GradeConfigUpdate(BaseModel):
    min_score: Optional[Decimal] = Field(None, ge=0, le=100)
    max_score: Optional[Decimal] = Field(None, ge=0, le=100)
    grade_point: Optional[Decimal] = Field(None, ge=0, le=5.0)
    remark: Optional[str] = Field(None, max_length=50)
    color_code: Optional[str] = Field(None, max_length=10)
    is_passing: Optional[bool] = None
    display_order: Optional[int] = None


class GradeConfig(GradeConfigBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# ASSESSMENTS
# ============================================

class AssessmentBase(BaseModel):
    assessment_type_id: str
    subject_id: str
    class_id: str
    session_id: str
    term_id: str
    grading_scheme_component_id: Optional[str] = None  # Link to grading scheme component
    teacher_id: Optional[str] = None
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    assessment_date: Optional[date] = None
    max_score: Decimal = Field(default=100.00, ge=0, le=999.99)


class AssessmentCreate(AssessmentBase):
    pass


class AssessmentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    assessment_date: Optional[date] = None
    max_score: Optional[Decimal] = Field(None, ge=0, le=999.99)
    teacher_id: Optional[str] = None
    grading_scheme_component_id: Optional[str] = None
    status: Optional[str] = None


class Assessment(AssessmentBase):
    id: str
    organization_id: str
    status: str
    published_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    # Enriched fields
    assessment_type_name: Optional[str] = None
    subject_name: Optional[str] = None
    class_name: Optional[str] = None
    teacher_name: Optional[str] = None
    grading_scheme_component_name: Optional[str] = None
    grades_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ============================================
# GRADES
# ============================================

class GradeBase(BaseModel):
    assessment_id: str
    student_id: str
    score: Optional[Decimal] = Field(None, ge=0, le=999.99)
    remark: Optional[str] = None
    is_absent: bool = False
    is_excused: bool = False


class GradeCreate(GradeBase):
    pass


class BulkGradeEntry(BaseModel):
    """For entering multiple grades at once"""
    assessment_id: str
    grades: List[dict]  # [{student_id, score, remark, is_absent}]


class GradeUpdate(BaseModel):
    score: Optional[Decimal] = Field(None, ge=0, le=999.99)
    remark: Optional[str] = None
    is_absent: Optional[bool] = None
    is_excused: Optional[bool] = None


class Grade(GradeBase):
    id: str
    organization_id: str
    grade_letter: Optional[str] = None
    grade_point: Optional[Decimal] = None
    submitted_at: Optional[datetime] = None
    entered_by: Optional[str] = None
    entered_at: datetime
    modified_by: Optional[str] = None
    modified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    student_name: Optional[str] = None
    student_admission_number: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# SUBJECT GRADES (AGGREGATED)
# ============================================

class SubjectGradeBase(BaseModel):
    student_id: str
    subject_id: str
    class_id: str
    session_id: str
    term_id: str
    ca_total: Optional[Decimal] = None
    exam_score: Optional[Decimal] = None
    total_score: Optional[Decimal] = None
    average_score: Optional[Decimal] = None
    grade_letter: Optional[str] = None
    grade_point: Optional[Decimal] = None
    class_position: Optional[int] = None
    class_size: Optional[int] = None
    teacher_remark: Optional[str] = None
    teacher_id: Optional[str] = None


class SubjectGrade(SubjectGradeBase):
    id: str
    organization_id: str
    calculated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    student_name: Optional[str] = None
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# REPORT CARDS
# ============================================

class ReportCardBase(BaseModel):
    student_id: str
    session_id: str
    term_id: str
    class_id: str
    total_score: Optional[Decimal] = None
    average_score: Optional[Decimal] = None
    overall_grade: Optional[str] = None
    overall_position: Optional[int] = None
    class_size: Optional[int] = None
    days_present: int = 0
    days_absent: int = 0
    days_late: int = 0
    total_school_days: int = 0
    class_teacher_remark: Optional[str] = None
    principal_remark: Optional[str] = None
    resumption_date: Optional[date] = None


class ReportCardGenerate(BaseModel):
    """Request to generate report card"""
    student_id: str
    session_id: str
    term_id: str


class ReportCardUpdate(BaseModel):
    class_teacher_remark: Optional[str] = None
    principal_remark: Optional[str] = None
    resumption_date: Optional[date] = None


class ReportCard(ReportCardBase):
    id: str
    organization_id: str
    status: str
    generated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    student_name: Optional[str] = None
    student_admission_number: Optional[str] = None
    class_name: Optional[str] = None
    session_name: Optional[str] = None
    term_name: Optional[str] = None
    subject_grades: Optional[List[SubjectGrade]] = []

    class Config:
        from_attributes = True


# ============================================
# ANALYTICS
# ============================================

class PerformanceAnalytics(BaseModel):
    """Performance statistics for a class/subject"""
    total_students: int
    students_graded: int
    average_score: Optional[Decimal] = None
    highest_score: Optional[Decimal] = None
    lowest_score: Optional[Decimal] = None
    pass_rate: Optional[Decimal] = None
    grade_distribution: dict  # {grade_letter: count}


class StudentPerformanceSummary(BaseModel):
    """Student performance across subjects"""
    student_id: str
    student_name: str
    session_id: str
    term_id: str
    total_subjects: int
    average_score: Optional[Decimal] = None
    overall_position: Optional[int] = None
    class_size: Optional[int] = None
    subject_performances: List[SubjectGrade]
