"""
Attendance Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from app.core.database import get_supabase
from app.core.security import get_current_user
from app.core.permissions import PermissionChecker
from app.core.exceptions import AuthorizationError
from app.models.attendance import (
    AttendanceRecord, AttendanceRecordCreate, AttendanceRecordUpdate,
    BulkAttendanceEntry,
    AttendanceSummary,
    LeaveRequest, LeaveRequestCreate, LeaveRequestUpdate, LeaveRequestApproval,
    AttendanceSettings, AttendanceSettingsCreate, AttendanceSettingsUpdate,
    Holiday, HolidayCreate, HolidayUpdate,
    AttendanceAnalytics, ClassAttendanceReport
)

router = APIRouter()


# ============================================
# ATTENDANCE MARKING
# ============================================

@router.post("/mark", status_code=status.HTTP_201_CREATED)
def mark_attendance_bulk(
    data: BulkAttendanceEntry,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Mark attendance for multiple students at once (Form Teacher Only)"""
    
    # Verify basic role
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can mark attendance"
        )
    
    # For teachers: verify form teacher permission
    if current_user["role"] == "teacher":
        supabase = get_supabase()
        teacher_id = current_user.get("teacher_id")
        
        try:
            # Check if teacher is form teacher of this class
            PermissionChecker.verify_form_teacher_permission(
                teacher_id, data.class_id, supabase
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Form teacher access required: {str(e)}"
            )
    
    # Prepare attendance records
    records_to_insert = []
    for record in data.records:
        record_data = {
            "organization_id": current_user["school_id"],
            "student_id": record["student_id"],
            "class_id": data.class_id,
            "session_id": data.session_id,
            "term_id": data.term_id,
            "attendance_date": data.attendance_date.isoformat(),
            "status": record["status"],
            "check_in_time": record.get("check_in_time"),
            "minutes_late": record.get("minutes_late", 0),
            "reason": record.get("reason"),
            "notes": record.get("notes"),
            "marked_by": current_user["id"],
            "marked_at": datetime.utcnow().isoformat()
        }
        records_to_insert.append(record_data)
    
    # Use upsert to handle existing records
    response = db.table("attendance_records").upsert(
        records_to_insert,
        on_conflict="student_id,attendance_date"
    ).execute()
    
    # Update attendance summaries
    update_attendance_summaries(
        db,
        current_user["school_id"],
        data.session_id,
        data.term_id,
        [r["student_id"] for r in data.records]
    )
    
    return {
        "message": f"Successfully marked attendance for {len(response.data)} students",
        "records_marked": len(response.data)
    }


@router.get("/class/{class_id}/date/{attendance_date}")
def get_class_attendance(
    class_id: str,
    attendance_date: date,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get attendance records for a class on a specific date (Form Teacher or Admin)"""

    if current_user["role"] == "teacher":
        supabase = get_supabase()
        teacher_id = current_user.get("teacher_id")

        try:
            PermissionChecker.verify_form_teacher_permission(
                teacher_id, class_id, supabase
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Form teacher access required: {str(e)}"
            )
    elif current_user["role"] not in ["admin", "system_admin", "dean"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the form teacher or an admin can view a class's attendance records"
        )

    # Get attendance records
    response = db.table("attendance_records").select(
        "*, students(admission_number, first_name, last_name)"
    ).eq("class_id", class_id).eq(
        "attendance_date", attendance_date.isoformat()
    ).eq("organization_id", current_user["school_id"]).execute()
    
    # Enrich with student names
    enriched_data = []
    for item in response.data:
        enriched_item = {**item}
        if "students" in item and item["students"]:
            student = item["students"]
            enriched_item["student_name"] = f"{student['first_name']} {student['last_name']}"
            enriched_item["student_admission_number"] = student["admission_number"]
        enriched_data.append(enriched_item)
    
    # Calculate statistics
    total_students = len(enriched_data)
    present_count = len([r for r in enriched_data if r["status"] == "present"])
    absent_count = len([r for r in enriched_data if r["status"] == "absent"])
    late_count = len([r for r in enriched_data if r["status"] == "late"])
    excused_count = len([r for r in enriched_data if r["status"] == "excused"])
    
    attendance_rate = (present_count + late_count) / total_students * 100 if total_students > 0 else 0
    
    # Get class name
    class_data = db.table("classes").select("name").eq("id", class_id).execute()
    class_name = class_data.data[0]["name"] if class_data.data else "Unknown"
    
    return {
        "class_id": class_id,
        "class_name": class_name,
        "attendance_date": attendance_date,
        "total_students": total_students,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "excused_count": excused_count,
        "attendance_rate": attendance_rate,
        "records": enriched_data
    }


@router.get("/student/{student_id}")
def get_student_attendance(
    student_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    session_id: Optional[str] = None,
    term_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get attendance history for a student"""

    PermissionChecker.verify_can_view_student(current_user, student_id, db)

    query = db.table("attendance_records").select("*").eq(
        "student_id", student_id
    ).eq("organization_id", current_user["school_id"])
    
    if start_date:
        query = query.gte("attendance_date", start_date.isoformat())
    if end_date:
        query = query.lte("attendance_date", end_date.isoformat())
    if session_id:
        query = query.eq("session_id", session_id)
    if term_id:
        query = query.eq("term_id", term_id)
    
    query = query.order("attendance_date", desc=True)
    response = query.execute()
    
    return response.data


# ============================================
# ATTENDANCE SUMMARIES
# ============================================

@router.get("/summary/student/{student_id}")
def get_student_attendance_summary(
    student_id: str,
    session_id: str,
    term_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get attendance summary for a student"""

    PermissionChecker.verify_can_view_student(current_user, student_id, db)

    response = db.table("attendance_summaries").select(
        "*, students(admission_number, first_name, last_name)"
    ).eq("student_id", student_id).eq(
        "session_id", session_id
    ).eq("term_id", term_id).execute()
    
    if not response.data:
        # Return empty summary
        return {
            "student_id": student_id,
            "session_id": session_id,
            "term_id": term_id,
            "days_present": 0,
            "days_absent": 0,
            "days_late": 0,
            "days_excused": 0,
            "total_school_days": 0,
            "attendance_percentage": 0,
            "punctuality_percentage": 0
        }
    
    return response.data[0]


@router.get("/summary/class/{class_id}")
def get_class_attendance_summaries(
    class_id: str,
    session_id: str,
    term_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get attendance summaries for all students in a class (Form Teacher or Admin)"""

    # For teachers: verify form teacher permission. Every other non-admin
    # role (bursar/parent/student) has no legitimate use for a whole
    # class's attendance and must be rejected explicitly.
    if current_user["role"] == "teacher":
        supabase = get_supabase()
        teacher_id = current_user.get("teacher_id")

        try:
            PermissionChecker.verify_form_teacher_permission(
                teacher_id, class_id, supabase
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Form teacher access required: {str(e)}"
            )
    elif current_user["role"] not in ["admin", "system_admin", "dean"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the form teacher or an admin can view a class's attendance summary"
        )

    # Get students in class (current_class_id is the source of truth used
    # everywhere else - "enrollments" is not a real table)
    enrollments = db.table("students").select("id").eq(
        "current_class_id", class_id
    ).execute()

    if not enrollments.data:
        return []

    student_ids = [e["id"] for e in enrollments.data]
    
    # Get summaries
    response = db.table("attendance_summaries").select(
        "*, students(admission_number, first_name, last_name)"
    ).in_("student_id", student_ids).eq(
        "session_id", session_id
    ).eq("term_id", term_id).execute()
    
    # Enrich with student names
    enriched_data = []
    for item in response.data:
        enriched_item = {**item}
        if "students" in item and item["students"]:
            student = item["students"]
            enriched_item["student_name"] = f"{student['first_name']} {student['last_name']}"
            enriched_item["student_admission_number"] = student["admission_number"]
        enriched_data.append(enriched_item)
    
    return enriched_data


# ============================================
# LEAVE REQUESTS
# ============================================

@router.get("/leave-requests", response_model=List[LeaveRequest])
def get_leave_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    student_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get leave requests"""
    
    query = db.table("leave_requests").select(
        "*, students(admission_number, first_name, last_name)"
    ).eq("organization_id", current_user["school_id"])
    
    if status_filter:
        query = query.eq("status", status_filter)
    if student_id:
        query = query.eq("student_id", student_id)
    
    query = query.order("created_at", desc=True)
    response = query.execute()
    
    # Enrich with student names
    enriched_data = []
    for item in response.data:
        enriched_item = {**item}
        if "students" in item and item["students"]:
            student = item["students"]
            enriched_item["student_name"] = f"{student['first_name']} {student['last_name']}"
        enriched_data.append(enriched_item)
    
    return enriched_data


@router.post("/leave-requests", response_model=LeaveRequest, status_code=status.HTTP_201_CREATED)
def create_leave_request(
    data: LeaveRequestCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Create new leave request"""

    # Verify the submitter actually has a relationship to this student -
    # previously any authenticated user could file a leave request for
    # any student_id in any organization.
    if current_user["role"] in ["admin", "system_admin"]:
        pass  # unrestricted administrative access
    elif current_user["role"] == "teacher":
        student = db.table("students").select("current_class_id").eq(
            "id", data.student_id
        ).eq("organization_id", current_user["school_id"]).execute()

        class_id = student.data[0]["current_class_id"] if student.data else None
        if not class_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student not found or has no assigned class"
            )
        try:
            PermissionChecker.verify_form_teacher_permission(
                current_user.get("teacher_id"), class_id, db
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Form teacher access required: {str(e)}"
            )
    elif current_user["role"] == "parent":
        parent = db.table("parents").select("id").eq(
            "user_id", current_user["id"]
        ).execute()
        parent_id = parent.data[0]["id"] if parent.data else None

        link = (
            db.table("parent_student_links").select("id")
            .eq("parent_id", parent_id).eq("student_id", data.student_id).execute()
            if parent_id else None
        )
        if not parent_id or not link.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only submit leave requests for your own linked children"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to submit a leave request for this student"
        )

    request_data = data.model_dump(mode="json")
    request_data["organization_id"] = current_user["school_id"]
    request_data["status"] = "pending"
    request_data["submitted_by"] = current_user["id"]
    request_data["submitted_at"] = datetime.utcnow().isoformat()
    
    response = db.table("leave_requests").insert(request_data).execute()
    
    return response.data[0]


@router.put("/leave-requests/{request_id}/approve")
def approve_leave_request(
    request_id: str,
    data: LeaveRequestApproval,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Approve or reject leave request"""

    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can approve leave requests"
        )

    # Teachers may only approve/reject leave requests for students in a
    # class they are the form teacher of, not any request org-wide.
    if current_user["role"] == "teacher":
        existing = db.table("leave_requests").select("student_id").eq(
            "id", request_id
        ).eq("organization_id", current_user["school_id"]).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )

        student = db.table("students").select("current_class_id").eq(
            "id", existing.data[0]["student_id"]
        ).execute()

        class_id = student.data[0]["current_class_id"] if student.data else None
        if not class_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student has no assigned class"
            )

        try:
            PermissionChecker.verify_form_teacher_permission(
                current_user.get("teacher_id"), class_id, db
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Form teacher access required: {str(e)}"
            )

    update_data = {
        "status": data.status,
        "approved_by": current_user["id"],
        "approved_at": datetime.utcnow().isoformat()
    }
    
    if data.status == "rejected" and data.rejection_reason:
        update_data["rejection_reason"] = data.rejection_reason
    
    response = db.table("leave_requests").update(update_data).eq(
        "id", request_id
    ).eq("organization_id", current_user["school_id"]).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    return response.data[0]


# ============================================
# ATTENDANCE SETTINGS
# ============================================

@router.get("/settings", response_model=AttendanceSettings)
def get_attendance_settings(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get attendance settings for organization"""
    
    response = db.table("attendance_settings").select("*").eq(
        "organization_id", current_user["school_id"]
    ).execute()

    if not response.data:
        # First access for this organization - create the default row so the
        # response actually satisfies AttendanceSettings (id/timestamps are
        # required fields, not something a hand-built dict can fake).
        created = db.table("attendance_settings").insert({
            "organization_id": current_user["school_id"],
            "school_start_time": "08:00:00",
            "school_end_time": "14:00:00",
            "late_threshold_minutes": 15,
            "auto_mark_absent": False,
            "notify_parents_on_absence": True,
            "notify_parents_on_late": False,
            "absence_threshold_notify": 3,
            "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }).execute()
        return created.data[0]

    return response.data[0]


@router.post("/settings", response_model=AttendanceSettings, status_code=status.HTTP_201_CREATED)
def create_attendance_settings(
    data: AttendanceSettingsCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Create attendance settings (admin only)"""
    
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create attendance settings"
        )
    
    settings_data = data.model_dump(mode="json")
    settings_data["organization_id"] = current_user["school_id"]
    
    response = db.table("attendance_settings").insert(settings_data).execute()
    
    return response.data[0]


@router.put("/settings", response_model=AttendanceSettings)
def update_attendance_settings(
    data: AttendanceSettingsUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Update attendance settings (admin only)"""
    
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update attendance settings"
        )
    
    update_data = data.model_dump(mode="json", exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()

    response = db.table("attendance_settings").update(update_data).eq(
        "organization_id", current_user["school_id"]
    ).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance settings not found"
        )
    
    return response.data[0]


# ============================================
# HOLIDAYS
# ============================================

@router.get("/holidays", response_model=List[Holiday])
def get_holidays(
    session_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get holidays"""
    
    query = db.table("holidays").select("*").eq(
        "organization_id", current_user["school_id"]
    )
    
    if session_id:
        query = query.eq("session_id", session_id)
    
    query = query.order("start_date")
    response = query.execute()
    
    return response.data


@router.post("/holidays", response_model=Holiday, status_code=status.HTTP_201_CREATED)
def create_holiday(
    data: HolidayCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Create new holiday (admin only)"""
    
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create holidays"
        )
    
    holiday_data = data.model_dump(mode="json")
    holiday_data["organization_id"] = current_user["school_id"]
    
    response = db.table("holidays").insert(holiday_data).execute()
    
    return response.data[0]


# ============================================
# HELPER FUNCTIONS
# ============================================

def update_attendance_summaries(
    db,
    organization_id: str,
    session_id: str,
    term_id: str,
    student_ids: List[str]
):
    """Update attendance summaries for students"""
    
    for student_id in student_ids:
        # Get all attendance records for this student in this term
        records = db.table("attendance_records").select("status").eq(
            "student_id", student_id
        ).eq("session_id", session_id).eq(
            "term_id", term_id
        ).execute()
        
        # Calculate statistics
        days_present = len([r for r in records.data if r["status"] == "present"])
        days_absent = len([r for r in records.data if r["status"] == "absent"])
        days_late = len([r for r in records.data if r["status"] == "late"])
        days_excused = len([r for r in records.data if r["status"] == "excused"])
        total_school_days = len(records.data)
        
        attendance_percentage = ((days_present + days_late) / total_school_days * 100) if total_school_days > 0 else 0
        punctuality_percentage = (days_present / (days_present + days_late) * 100) if (days_present + days_late) > 0 else 0
        
        summary_data = {
            "organization_id": organization_id,
            "student_id": student_id,
            "session_id": session_id,
            "term_id": term_id,
            "days_present": days_present,
            "days_absent": days_absent,
            "days_late": days_late,
            "days_excused": days_excused,
            "total_school_days": total_school_days,
            "attendance_percentage": attendance_percentage,
            "punctuality_percentage": punctuality_percentage,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Upsert summary
        db.table("attendance_summaries").upsert(
            summary_data,
            on_conflict="student_id,term_id,session_id"
        ).execute()
