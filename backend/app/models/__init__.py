"""
Pydantic models for request/response validation.
"""

from .academic import *
from .student import *
from .teacher import *
from .parent import *
from .grading import *
from .attendance import *
from .fees import *
from .teacher_management import *

__all__ = [
    # Academic models
    "AcademicSessionCreate",
    "AcademicSessionUpdate", 
    "AcademicSessionResponse",
    "TermCreate",
    "TermUpdate",
    "TermResponse",
    "ClassCreate",
    "ClassUpdate",
    "ClassResponse",
    "ClassDetailedResponse",
    "SubjectCreate",
    "SubjectUpdate",
    "SubjectResponse",
    # Student models
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "GuardianCreate",
    "GuardianUpdate",
    "GuardianResponse",
    # Teacher models
    "TeacherCreate",
    "TeacherUpdate",
    "TeacherResponse",
    # Teacher Management models (form teachers, grading schemes, etc.)
    "GradingSchemeCreate",
    "GradingSchemeUpdate",
    "GradingSchemeResponse",
    "GradingSchemeComponentCreate",
    "GradingSchemeComponentResponse",
    "ClassSubjectCreate",
    "ClassSubjectUpdate",
    "ClassSubjectResponse",
    "TeacherClassAssignmentCreate",
    "TeacherClassAssignmentUpdate",
    "TeacherClassAssignmentResponse",
    "StudentRemarkCreate",
    "StudentRemarkUpdate",
    "StudentRemarkResponse",
    "SchoolReportCreate",
    "SchoolReportUpdate",
    "SchoolReportResponse",
    "SchoolReportRecipientResponse",
    "BulkReportSend",
    # Parent models
    "ParentCreate",
    "ParentUpdate",
    "ParentResponse",
    "ParentStudentLinkCreate",
    "ParentStudentLinkResponse",
    # Grading models
    "AssessmentType",
    "AssessmentTypeCreate",
    "Assessment",
    "AssessmentCreate",
    "Grade",
    "GradeCreate",
    "BulkGradeEntry",
    "ReportCard",
    "ReportCardGenerate",
    # Attendance models
    "AttendanceRecord",
    "AttendanceRecordCreate",
    "BulkAttendanceEntry",
    "AttendanceSummary",
    "LeaveRequest",
    "LeaveRequestCreate",
    "Holiday",
    "HolidayCreate",
    # Fee models
    "FeeCategory",
    "FeeCategoryCreate",
    "FeeStructure",
    "FeeStructureCreate",
    "StudentFee",
    "StudentFeeCreate",
    "Payment",
    "PaymentCreate",
]

