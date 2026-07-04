"""
Pydantic models for Attendance Management System
"""

from datetime import date, datetime, time
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from decimal import Decimal


# ============================================
# ATTENDANCE RECORDS
# ============================================

class AttendanceRecordBase(BaseModel):
    student_id: str
    class_id: str
    session_id: str
    term_id: str
    attendance_date: date
    status: str = Field(..., pattern="^(present|absent|late|excused)$")
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    minutes_late: int = Field(default=0, ge=0)
    reason: Optional[str] = None
    notes: Optional[str] = None
    marked_by: Optional[str] = None  # Teacher/Admin ID who marked attendance


class AttendanceRecordCreate(AttendanceRecordBase):
    pass


class BulkAttendanceEntry(BaseModel):
    """For marking attendance for multiple students at once"""
    class_id: str
    session_id: str
    term_id: str
    attendance_date: date
    records: List[dict]  # [{student_id, status, check_in_time, minutes_late, reason}]
    marked_by: Optional[str] = None  # Teacher/Admin ID marking attendance


class AttendanceRecordUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(present|absent|late|excused)$")
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    minutes_late: Optional[int] = Field(None, ge=0)
    reason: Optional[str] = None
    notes: Optional[str] = None


class AttendanceRecord(AttendanceRecordBase):
    id: str
    organization_id: str
    marked_by: Optional[str] = None
    marked_at: datetime
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    student_name: Optional[str] = None
    student_admission_number: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# ATTENDANCE SUMMARIES
# ============================================

class AttendanceSummaryBase(BaseModel):
    student_id: str
    session_id: str
    term_id: str
    days_present: int = 0
    days_absent: int = 0
    days_late: int = 0
    days_excused: int = 0
    total_school_days: int = 0
    attendance_percentage: Optional[Decimal] = None
    punctuality_percentage: Optional[Decimal] = None


class AttendanceSummary(AttendanceSummaryBase):
    id: str
    organization_id: str
    last_updated: datetime
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    student_name: Optional[str] = None
    student_admission_number: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# LEAVE REQUESTS
# ============================================

class LeaveRequestBase(BaseModel):
    student_id: str
    start_date: date
    end_date: date
    leave_type: str = Field(..., pattern="^(sick|family|emergency|other)$")
    reason: str
    attachment_url: Optional[str] = None

    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be greater than or equal to start_date')
        return v


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    leave_type: Optional[str] = Field(None, pattern="^(sick|family|emergency|other)$")
    reason: Optional[str] = None
    attachment_url: Optional[str] = None


class LeaveRequestApproval(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")
    rejection_reason: Optional[str] = None


class LeaveRequest(LeaveRequestBase):
    id: str
    organization_id: str
    status: str  # pending, approved, rejected
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    submitted_by: Optional[str] = None
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    student_name: Optional[str] = None
    submitted_by_name: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# ATTENDANCE SETTINGS
# ============================================

class AttendanceSettingsBase(BaseModel):
    school_start_time: time = Field(default=time(8, 0))
    school_end_time: time = Field(default=time(14, 0))
    late_threshold_minutes: int = Field(default=15, ge=0)
    auto_mark_absent: bool = False
    auto_mark_time: Optional[time] = None
    notify_parents_on_absence: bool = True
    notify_parents_on_late: bool = False
    absence_threshold_notify: int = Field(default=3, ge=1)
    working_days: Optional[List[str]] = Field(
        default=["monday", "tuesday", "wednesday", "thursday", "friday"]
    )


class AttendanceSettingsCreate(AttendanceSettingsBase):
    pass


class AttendanceSettingsUpdate(BaseModel):
    school_start_time: Optional[time] = None
    school_end_time: Optional[time] = None
    late_threshold_minutes: Optional[int] = Field(None, ge=0)
    auto_mark_absent: Optional[bool] = None
    auto_mark_time: Optional[time] = None
    notify_parents_on_absence: Optional[bool] = None
    notify_parents_on_late: Optional[bool] = None
    absence_threshold_notify: Optional[int] = Field(None, ge=1)
    working_days: Optional[List[str]] = None


class AttendanceSettings(AttendanceSettingsBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# HOLIDAYS
# ============================================

class HolidayBase(BaseModel):
    holiday_name: str = Field(..., max_length=200)
    start_date: date
    end_date: date
    holiday_type: str = Field(default="public", pattern="^(public|school|term_break)$")
    description: Optional[str] = None
    session_id: Optional[str] = None

    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be greater than or equal to start_date')
        return v


class HolidayCreate(HolidayBase):
    pass


class HolidayUpdate(BaseModel):
    holiday_name: Optional[str] = Field(None, max_length=200)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    holiday_type: Optional[str] = Field(None, pattern="^(public|school|term_break)$")
    description: Optional[str] = None


class Holiday(HolidayBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# ANALYTICS
# ============================================

class AttendanceAnalytics(BaseModel):
    """Attendance statistics for a class or organization"""
    total_students: int
    average_attendance_rate: Optional[Decimal] = None
    average_punctuality_rate: Optional[Decimal] = None
    total_absences: int
    total_lates: int
    chronic_absentees: int  # Students below threshold
    perfect_attendance: int  # Students with 100% attendance


class ClassAttendanceReport(BaseModel):
    """Daily attendance report for a class"""
    class_id: str
    class_name: str
    attendance_date: date
    total_students: int
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    attendance_rate: Decimal
    records: List[AttendanceRecord]
