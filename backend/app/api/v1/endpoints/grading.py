"""
Grading & Assessment API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.core.database import get_supabase
from app.core.security import get_current_user
from app.core.permissions import PermissionChecker
from app.core.exceptions import AuthorizationError
from app.models.grading import (
    AssessmentType, AssessmentTypeCreate, AssessmentTypeUpdate,
    Assessment, AssessmentCreate, AssessmentUpdate,
    Grade, GradeCreate, GradeUpdate, BulkGradeEntry,
    SubjectGrade, ReportCard, ReportCardGenerate, ReportCardUpdate,
    PerformanceAnalytics,
    GradeConfig, GradeConfigCreate, GradeConfigUpdate,
)

router = APIRouter()


# ============================================
# ASSESSMENT TYPES
# ============================================

@router.get("/assessment-types", response_model=List[AssessmentType])
async def get_assessment_types(
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get all assessment types for organization"""
    
    query = db.table("assessment_types").select("*").eq(
        "organization_id", current_user["school_id"]
    )
    
    if is_active is not None:
        query = query.eq("is_active", is_active)
    
    query = query.order("display_order")
    response = query.execute()
    
    return response.data


@router.post("/assessment-types", response_model=AssessmentType, status_code=status.HTTP_201_CREATED)
async def create_assessment_type(
    data: AssessmentTypeCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Create new assessment type (admin only)"""
    
    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create assessment types"
        )
    
    # Check for duplicate code
    existing = db.table("assessment_types").select("id").eq(
        "organization_id", current_user["school_id"]
    ).eq("code", data.code).execute()
    
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Assessment type with code '{data.code}' already exists"
        )
    
    assessment_type_data = data.model_dump(mode="json")
    assessment_type_data["organization_id"] = current_user["school_id"]
    
    response = db.table("assessment_types").insert(assessment_type_data).execute()

    return response.data[0]


# ============================================
# GRADE CONFIGS (grade letter bands, e.g. A=70-100)
# ============================================

@router.get("/grade-configs", response_model=List[GradeConfig])
async def get_grade_configs(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get all grade bands for organization"""

    response = db.table("grade_configs").select("*").eq(
        "organization_id", current_user["school_id"]
    ).order("display_order").execute()

    return response.data


@router.post("/grade-configs", response_model=GradeConfig, status_code=status.HTTP_201_CREATED)
async def create_grade_config(
    data: GradeConfigCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Create a grade band (admin only)"""

    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can configure grade bands"
        )

    existing = db.table("grade_configs").select("id").eq(
        "organization_id", current_user["school_id"]
    ).eq("grade_letter", data.grade_letter).execute()

    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Grade band '{data.grade_letter}' already exists"
        )

    grade_config_data = data.model_dump(mode="json")
    grade_config_data["organization_id"] = current_user["school_id"]

    response = db.table("grade_configs").insert(grade_config_data).execute()

    return response.data[0]


@router.put("/grade-configs/{grade_config_id}", response_model=GradeConfig)
async def update_grade_config(
    grade_config_id: str,
    data: GradeConfigUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Update a grade band (admin only)"""

    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can configure grade bands"
        )

    update_data = data.model_dump(mode="json", exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()

    response = db.table("grade_configs").update(update_data).eq(
        "id", grade_config_id
    ).eq("organization_id", current_user["school_id"]).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade band not found"
        )

    return response.data[0]


@router.delete("/grade-configs/{grade_config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grade_config(
    grade_config_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Delete a grade band (admin only)"""

    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete grade bands"
        )

    response = db.table("grade_configs").delete().eq(
        "id", grade_config_id
    ).eq("organization_id", current_user["school_id"]).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade band not found"
        )


# ============================================
# ASSESSMENTS
# ============================================

@router.get("/assessments", response_model=List[Assessment])
async def get_assessments(
    subject_id: Optional[str] = None,
    class_id: Optional[str] = None,
    session_id: Optional[str] = None,
    term_id: Optional[str] = None,
    teacher_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get assessments with optional filters"""
    
    query = db.table("assessments").select(
        "*, "
        "assessment_types(name), "
        "subjects(name), "
        "classes(name), "
        "teachers(first_name, last_name)"
    ).eq("organization_id", current_user["school_id"])
    
    if subject_id:
        query = query.eq("subject_id", subject_id)
    if class_id:
        query = query.eq("class_id", class_id)
    if session_id:
        query = query.eq("session_id", session_id)
    if term_id:
        query = query.eq("term_id", term_id)
    if teacher_id:
        query = query.eq("teacher_id", teacher_id)
    if status_filter:
        query = query.eq("status", status_filter)
    
    query = query.order("created_at", desc=True)
    response = query.execute()
    
    # Enrich data
    enriched_data = []
    for item in response.data:
        enriched_item = {**item}
        if "assessment_types" in item and item["assessment_types"]:
            enriched_item["assessment_type_name"] = item["assessment_types"]["name"]
        if "subjects" in item and item["subjects"]:
            enriched_item["subject_name"] = item["subjects"]["name"]
        if "classes" in item and item["classes"]:
            enriched_item["class_name"] = item["classes"]["name"]
        if "teachers" in item and item["teachers"]:
            teacher = item["teachers"]
            enriched_item["teacher_name"] = f"{teacher['first_name']} {teacher['last_name']}"
        
        # Get grades count
        grades_count = db.table("grades").select("id", count="exact").eq(
            "assessment_id", item["id"]
        ).execute()
        enriched_item["grades_count"] = grades_count.count if grades_count.count else 0
        
        enriched_data.append(enriched_item)
    
    return enriched_data


@router.get("/assessments/{assessment_id}", response_model=Assessment)
async def get_assessment(
    assessment_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get specific assessment"""
    
    response = db.table("assessments").select(
        "*, "
        "assessment_types(name), "
        "subjects(name), "
        "classes(name)"
    ).eq("id", assessment_id).eq(
        "organization_id", current_user["school_id"]
    ).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    return response.data[0]


@router.post("/assessments", response_model=Assessment, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    data: AssessmentCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Create new assessment (Subject Teacher Only)"""
    
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can create assessments"
        )
    
    # For teachers: verify subject teacher permission
    if current_user["role"] == "teacher":
        supabase = get_supabase()
        teacher_id = current_user.get("teacher_id")
        
        try:
            await PermissionChecker.verify_subject_teacher_permission(
                teacher_id, data.subject_id, data.class_id, supabase
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subject teacher access required: {str(e)}"
            )
    
    # grading_scheme_component_id has no backing column in the live
    # assessments table (Phase 4 field never migrated) - drop it rather
    # than let PostgREST reject the whole insert over an unknown column.
    assessment_data = data.model_dump(mode="json", exclude={"grading_scheme_component_id"})
    assessment_data["organization_id"] = current_user["school_id"]
    assessment_data["status"] = "draft"
    assessment_data["created_by"] = current_user["id"]
    
    response = db.table("assessments").insert(assessment_data).execute()
    
    return response.data[0]


@router.put("/assessments/{assessment_id}", response_model=Assessment)
async def update_assessment(
    assessment_id: str,
    data: AssessmentUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Update assessment"""

    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can update assessments"
        )

    # Check assessment exists and belongs to organization
    existing = db.table("assessments").select("*").eq(
        "id", assessment_id
    ).eq("organization_id", current_user["school_id"]).execute()

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    assessment = existing.data[0]

    # For teachers: verify subject teacher permission on the assessment's
    # own subject/class, same check create_assessment uses.
    if current_user["role"] == "teacher":
        supabase = get_supabase()
        teacher_id = current_user.get("teacher_id")
        try:
            await PermissionChecker.verify_subject_teacher_permission(
                teacher_id, assessment["subject_id"], assessment["class_id"], supabase
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subject teacher access required: {str(e)}"
            )

    # Only allow updates if not locked
    if assessment["status"] == "locked":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update locked assessment"
        )
    
    update_data = data.model_dump(mode="json", exclude_unset=True, exclude={"grading_scheme_component_id"})
    update_data["updated_at"] = datetime.utcnow().isoformat()

    response = db.table("assessments").update(update_data).eq(
        "id", assessment_id
    ).execute()
    
    return response.data[0]


@router.post("/assessments/{assessment_id}/publish")
async def publish_assessment(
    assessment_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Publish assessment (make it available for grading)"""

    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can publish assessments"
        )

    existing = db.table("assessments").select("*").eq(
        "id", assessment_id
    ).eq("organization_id", current_user["school_id"]).execute()

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    assessment = existing.data[0]

    if current_user["role"] == "teacher":
        supabase = get_supabase()
        teacher_id = current_user.get("teacher_id")
        try:
            await PermissionChecker.verify_subject_teacher_permission(
                teacher_id, assessment["subject_id"], assessment["class_id"], supabase
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subject teacher access required: {str(e)}"
            )

    response = db.table("assessments").update({
        "status": "published",
        "published_at": datetime.utcnow().isoformat()
    }).eq("id", assessment_id).eq(
        "organization_id", current_user["school_id"]
    ).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    return {"message": "Assessment published successfully"}


@router.delete("/assessments/{assessment_id}")
async def delete_assessment(
    assessment_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Delete assessment (admin only, only if no grades entered)"""
    
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete assessments"
        )
    
    # Check if grades exist
    grades = db.table("grades").select("id").eq(
        "assessment_id", assessment_id
    ).execute()
    
    if grades.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete assessment with existing grades"
        )
    
    response = db.table("assessments").delete().eq(
        "id", assessment_id
    ).eq("organization_id", current_user["school_id"]).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    return {"message": "Assessment deleted successfully"}


# ============================================
# GRADES
# ============================================

@router.get("/assessments/{assessment_id}/grades", response_model=List[Grade])
async def get_assessment_grades(
    assessment_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get all grades for an assessment"""

    assessment = db.table("assessments").select("subject_id, class_id").eq(
        "id", assessment_id
    ).eq("organization_id", current_user["school_id"]).execute()

    if not assessment.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    if current_user["role"] == "teacher":
        try:
            await PermissionChecker.verify_subject_teacher_permission(
                current_user.get("teacher_id"), assessment.data[0]["subject_id"],
                assessment.data[0]["class_id"], db
            )
        except AuthorizationError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    elif current_user["role"] not in ["admin", "system_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the subject teacher or an admin can view a whole assessment's grades"
        )

    response = db.table("grades").select(
        "*, students(admission_number, first_name, last_name)"
    ).eq("assessment_id", assessment_id).eq(
        "organization_id", current_user["school_id"]
    ).order("students(last_name)").execute()
    
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


@router.post("/grades/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_grade_entry(
    data: BulkGradeEntry,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Enter grades for multiple students at once (Subject Teacher Only)"""
    
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can enter grades"
        )
    
    # Get assessment details for max score, subject_id, class_id, and grade calculation
    assessment = db.table("assessments").select("max_score, subject_id, class_id").eq(
        "id", data.assessment_id
    ).execute()
    
    if not assessment.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    assessment_data = assessment.data[0]
    max_score = float(assessment_data["max_score"])
    subject_id = assessment_data["subject_id"]
    class_id = assessment_data["class_id"]
    
    # For teachers: verify subject teacher permission
    if current_user["role"] == "teacher":
        supabase = get_supabase()
        teacher_id = current_user.get("teacher_id")
        
        try:
            await PermissionChecker.verify_subject_teacher_permission(
                teacher_id, subject_id, class_id, supabase
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subject teacher access required: {str(e)}"
            )
    
    # Get grade configs
    grade_configs = db.table("grade_configs").select("*").eq(
        "organization_id", current_user["school_id"]
    ).order("min_score", desc=True).execute()
    
    def calculate_grade(score: float):
        """Calculate grade letter and points from score"""
        if score is None:
            return None, None
        
        for config in grade_configs.data:
            if float(config["min_score"]) <= score <= float(config["max_score"]):
                return config["grade_letter"], config["grade_point"]
        return "F", 0.0
    
    # Prepare grade entries
    grades_to_insert = []
    for grade_entry in data.grades:
        score = grade_entry.get("score")
        
        # Validate score
        if score is not None and score > max_score:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Score {score} exceeds maximum {max_score}"
            )
        
        grade_letter, grade_point = calculate_grade(score) if score is not None else (None, None)
        
        grade_data = {
            "organization_id": current_user["school_id"],
            "assessment_id": data.assessment_id,
            "student_id": grade_entry["student_id"],
            "score": score,
            "grade_letter": grade_letter,
            "grade_point": grade_point,
            "remark": grade_entry.get("remark"),
            "is_absent": grade_entry.get("is_absent", False),
            "is_excused": grade_entry.get("is_excused", False),
            "entered_by": current_user["id"],
            "entered_at": datetime.utcnow().isoformat()
        }
        
        grades_to_insert.append(grade_data)
    
    # Use upsert to handle existing grades
    response = db.table("grades").upsert(
        grades_to_insert,
        on_conflict="assessment_id,student_id"
    ).execute()
    
    return {
        "message": f"Successfully entered {len(response.data)} grades",
        "grades_entered": len(response.data)
    }


@router.get("/students/{student_id}/grades")
async def get_student_grades(
    student_id: str,
    session_id: Optional[str] = None,
    term_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get all grades for a student"""

    await PermissionChecker.verify_can_view_student(current_user, student_id, db)

    query = db.table("grades").select(
        "*, assessments(title, max_score, assessment_date, subjects(name))"
    ).eq("student_id", student_id).eq(
        "organization_id", current_user["school_id"]
    )
    
    # Apply filters through assessments join if needed
    response = query.execute()
    
    return response.data


# ============================================
# REPORT CARDS
# ============================================

def _lookup_grade_letter(grade_configs: list, score: float) -> Optional[str]:
    """Match a score against an organization's configured grade bands."""
    for config in grade_configs:
        if float(config["min_score"]) <= score <= float(config["max_score"]):
            return config["grade_letter"]
    return None


def _compute_subject_grades_for_student(
    db, organization_id: str, student_id: str, class_id: str, session_id: str, term_id: str
) -> List[dict]:
    """
    Aggregate a student's per-assessment scores (grades table) into one
    weighted total per subject (subject_grades table), using each
    assessment_type's weight_percentage. This is the computation report
    cards depend on - nothing else in the app ever populates subject_grades.
    """
    assessments = db.table("assessments").select(
        "id, subject_id, max_score, assessment_types(weight_percentage)"
    ).eq("class_id", class_id).eq("session_id", session_id).eq(
        "term_id", term_id
    ).neq("status", "draft").execute()

    if not assessments.data:
        return []

    by_subject: dict = {}
    for a in assessments.data:
        by_subject.setdefault(a["subject_id"], []).append(a)

    grade_configs = db.table("grade_configs").select("*").eq(
        "organization_id", organization_id
    ).order("min_score", desc=True).execute().data

    computed = []
    for subject_id, subject_assessments in by_subject.items():
        assessment_ids = [a["id"] for a in subject_assessments]
        grades = db.table("grades").select("assessment_id, score").eq(
            "student_id", student_id
        ).in_("assessment_id", assessment_ids).execute()

        grades_by_assessment = {g["assessment_id"]: g["score"] for g in grades.data if g["score"] is not None}
        if not grades_by_assessment:
            continue

        weighted_total = 0.0
        for a in subject_assessments:
            score = grades_by_assessment.get(a["id"])
            if score is None:
                continue
            max_score = float(a["max_score"]) or 100.0
            weight = float((a.get("assessment_types") or {}).get("weight_percentage") or 0)
            weighted_total += (float(score) / max_score) * weight

        grade_letter = _lookup_grade_letter(grade_configs, weighted_total)

        subject_grade_data = {
            "organization_id": organization_id,
            "student_id": student_id,
            "subject_id": subject_id,
            "class_id": class_id,
            "session_id": session_id,
            "term_id": term_id,
            "total_score": round(weighted_total, 2),
            "average_score": round(weighted_total, 2),
            "grade_letter": grade_letter,
            "calculated_at": datetime.utcnow().isoformat(),
        }
        db.table("subject_grades").upsert(
            subject_grade_data, on_conflict="student_id,subject_id,term_id,session_id"
        ).execute()
        computed.append(subject_grade_data)

    return computed


@router.post("/report-cards/generate", status_code=status.HTTP_201_CREATED)
async def generate_report_card(
    data: ReportCardGenerate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Generate report card for a student (Form Teacher or Admin)"""
    
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can generate report cards"
        )
    
    # Get student details to find class_id
    student = db.table("students").select("current_class_id").eq(
        "id", data.student_id
    ).execute()

    if not student.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    student_data = student.data[0]
    class_id = student_data["current_class_id"]
    
    # For teachers: verify form teacher permission
    if current_user["role"] == "teacher":
        supabase = get_supabase()
        teacher_id = current_user.get("teacher_id")
        
        try:
            await PermissionChecker.verify_form_teacher_permission(
                teacher_id, class_id, supabase
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Form teacher access required: {str(e)}"
            )
    
    # Check if report card already exists
    existing = db.table("report_cards").select("id").eq(
        "student_id", data.student_id
    ).eq("session_id", data.session_id).eq(
        "term_id", data.term_id
    ).execute()
    
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report card already exists for this term"
        )
    
    # student_data and class_id already extracted above
    organization_id = current_user["school_id"]

    # Compute this student's subject grades from raw assessment scores
    subject_grades_data = _compute_subject_grades_for_student(
        db, organization_id, data.student_id, class_id, data.session_id, data.term_id
    )

    total_score = sum(sg["total_score"] for sg in subject_grades_data)
    num_subjects = len(subject_grades_data)
    average_score = total_score / num_subjects if num_subjects > 0 else 0

    # Rank against the rest of the class (also computes their subject grades,
    # since nothing else populates subject_grades either)
    classmates = db.table("students").select("id").eq("current_class_id", class_id).execute()
    class_size = len(classmates.data)

    class_averages = []
    for classmate in classmates.data:
        if classmate["id"] == data.student_id:
            class_averages.append((data.student_id, average_score))
            continue
        mate_grades = _compute_subject_grades_for_student(
            db, organization_id, classmate["id"], class_id, data.session_id, data.term_id
        )
        if mate_grades:
            mate_total = sum(sg["total_score"] for sg in mate_grades)
            class_averages.append((classmate["id"], mate_total / len(mate_grades)))

    overall_position = None
    if num_subjects > 0:
        class_averages.sort(key=lambda pair: pair[1], reverse=True)
        for idx, (sid, _) in enumerate(class_averages, start=1):
            if sid == data.student_id:
                overall_position = idx
                break

    grade_configs = db.table("grade_configs").select("*").eq(
        "organization_id", organization_id
    ).order("min_score", desc=True).execute().data
    overall_grade = _lookup_grade_letter(grade_configs, average_score) if num_subjects > 0 else None

    # Get attendance summary
    attendance = db.table("attendance_summaries").select("*").eq(
        "student_id", data.student_id
    ).eq("session_id", data.session_id).eq(
        "term_id", data.term_id
    ).execute()
    
    attendance_data = attendance.data[0] if attendance.data else {
        "days_present": 0,
        "days_absent": 0,
        "days_late": 0,
        "days_excused": 0,
        "total_school_days": 0,
        "attendance_percentage": None,
        "punctuality_percentage": None
    }

    # Create report card
    report_card_data = {
        "organization_id": current_user["school_id"],
        "student_id": data.student_id,
        "session_id": data.session_id,
        "term_id": data.term_id,
        "class_id": class_id,
        "total_score": total_score,
        "average_score": average_score,
        "overall_grade": overall_grade,
        "overall_position": overall_position,
        "class_size": class_size,
        "days_present": attendance_data["days_present"],
        "days_absent": attendance_data["days_absent"],
        "days_late": attendance_data["days_late"],
        "days_excused": attendance_data.get("days_excused", 0),
        "total_school_days": attendance_data["total_school_days"],
        "attendance_percentage": attendance_data.get("attendance_percentage"),
        "punctuality_percentage": attendance_data.get("punctuality_percentage"),
        "status": "generated",
        "generated_at": datetime.utcnow().isoformat()
    }
    
    response = db.table("report_cards").insert(report_card_data).execute()
    
    return response.data[0]


@router.get("/report-cards/{report_card_id}", response_model=ReportCard)
async def get_report_card(
    report_card_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get specific report card with subject grades"""
    
    response = db.table("report_cards").select(
        "*, "
        "students(admission_number, first_name, last_name), "
        "classes(name), "
        "academic_sessions(name), "
        "terms(name)"
    ).eq("id", report_card_id).eq(
        "organization_id", current_user["school_id"]
    ).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report card not found"
        )
    
    report_card = response.data[0]

    await PermissionChecker.verify_can_view_student(current_user, report_card["student_id"], db)

    if report_card.get("students"):
        student = report_card["students"]
        report_card["student_name"] = f"{student['first_name']} {student['last_name']}"
        report_card["student_admission_number"] = student.get("admission_number")
    if report_card.get("classes"):
        report_card["class_name"] = report_card["classes"]["name"]
    if report_card.get("academic_sessions"):
        report_card["session_name"] = report_card["academic_sessions"]["name"]
    if report_card.get("terms"):
        report_card["term_name"] = report_card["terms"]["name"]

    # Get subject grades
    subject_grades = db.table("subject_grades").select(
        "*, subjects(name)"
    ).eq("student_id", report_card["student_id"]).eq(
        "session_id", report_card["session_id"]
    ).eq("term_id", report_card["term_id"]).execute()

    enriched_subject_grades = []
    for grade in subject_grades.data:
        enriched_grade = {**grade}
        if grade.get("subjects"):
            enriched_grade["subject_name"] = grade["subjects"]["name"]
        enriched_subject_grades.append(enriched_grade)

    report_card["subject_grades"] = enriched_subject_grades

    # class_teacher_remark has no writer of its own - form teachers add
    # remarks via the separate student_remarks table (Class Remarks
    # feature). Surface their latest remark here rather than leaving it
    # permanently null.
    if not report_card.get("class_teacher_remark"):
        remarks = db.table("student_remarks").select("remark_text").eq(
            "student_id", report_card["student_id"]
        ).eq("class_id", report_card["class_id"]).eq(
            "session_id", report_card["session_id"]
        ).eq("term_id", report_card["term_id"]).order(
            "created_at", desc=True
        ).limit(1).execute()

        if remarks.data:
            report_card["class_teacher_remark"] = remarks.data[0]["remark_text"]

    # Get skill ratings (psychomotor/affective domain traits, admin-configurable)
    skill_ratings = db.table("student_skill_ratings").select(
        "rating, skill_categories(name, domain)"
    ).eq("student_id", report_card["student_id"]).eq(
        "session_id", report_card["session_id"]
    ).eq("term_id", report_card["term_id"]).execute()

    report_card["skill_ratings"] = [
        {
            "category_name": r["skill_categories"]["name"],
            "domain": r["skill_categories"]["domain"],
            "rating": r["rating"],
        }
        for r in (skill_ratings.data or []) if r.get("skill_categories")
    ]

    return report_card


@router.get("/students/{student_id}/report-cards")
async def get_student_report_cards(
    student_id: str,
    session_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get all report cards for a student"""

    await PermissionChecker.verify_can_view_student(current_user, student_id, db)

    query = db.table("report_cards").select(
        "*, "
        "academic_sessions(name), "
        "terms(name)"
    ).eq("student_id", student_id).eq(
        "organization_id", current_user["school_id"]
    )
    
    if session_id:
        query = query.eq("session_id", session_id)
    
    query = query.order("created_at", desc=True)
    response = query.execute()

    enriched_data = []
    for item in response.data:
        enriched_item = {**item}
        if item.get("academic_sessions"):
            enriched_item["session_name"] = item["academic_sessions"]["name"]
        if item.get("terms"):
            enriched_item["term_name"] = item["terms"]["name"]
        enriched_data.append(enriched_item)

    return enriched_data


@router.put("/report-cards/{report_card_id}")
async def update_report_card(
    report_card_id: str,
    data: ReportCardUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Update report card remarks (Form Teacher or Admin)"""
    
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can update report cards"
        )
    
    # Get report card to find class_id
    report_card = db.table("report_cards").select("class_id").eq(
        "id", report_card_id
    ).eq("organization_id", current_user["school_id"]).execute()
    
    if not report_card.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report card not found"
        )
    
    class_id = report_card.data[0]["class_id"]
    
    # For teachers: verify form teacher permission
    if current_user["role"] == "teacher":
        supabase = get_supabase()
        teacher_id = current_user.get("teacher_id")
        
        try:
            await PermissionChecker.verify_form_teacher_permission(
                teacher_id, class_id, supabase
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Form teacher access required: {str(e)}"
            )
    
    update_data = data.model_dump(mode="json", exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()

    response = db.table("report_cards").update(update_data).eq(
        "id", report_card_id
    ).eq("organization_id", current_user["school_id"]).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report card not found"
        )
    
    return response.data[0]


@router.post("/report-cards/{report_card_id}/publish")
async def publish_report_card(
    report_card_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Publish report card (make visible to parents)"""
    
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can publish report cards"
        )
    
    response = db.table("report_cards").update({
        "status": "published",
        "published_at": datetime.utcnow().isoformat()
    }).eq("id", report_card_id).eq(
        "organization_id", current_user["school_id"]
    ).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report card not found"
        )
    
    return {"message": "Report card published successfully"}


# ============================================
# ANALYTICS
# ============================================

@router.get("/analytics/class-performance")
async def get_class_performance(
    class_id: str,
    subject_id: str,
    session_id: str,
    term_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get performance analytics for a class in a subject (Form Teacher or Subject Teacher)"""
    
    # For teachers: verify form teacher OR subject teacher permission
    if current_user["role"] == "teacher":
        supabase = get_supabase()
        teacher_id = current_user.get("teacher_id")
        
        # Check if form teacher OR subject teacher
        is_form_teacher = await PermissionChecker.can_view_class_grades(
            teacher_id, class_id, supabase
        )
        is_subject_teacher = await PermissionChecker.can_enter_grades(
            teacher_id, subject_id, class_id, supabase
        )
        
        if not (is_form_teacher or is_subject_teacher):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be either the form teacher or teach this subject in this class"
            )
    elif current_user["role"] not in ["admin", "system_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a teacher of this class/subject or an admin can view this analytics"
        )

    # Get all subject grades for this class/subject/term
    grades = db.table("subject_grades").select(
        "total_score, grade_letter"
    ).eq("class_id", class_id).eq(
        "subject_id", subject_id
    ).eq("session_id", session_id).eq(
        "term_id", term_id
    ).execute()
    
    if not grades.data:
        return {
            "total_students": 0,
            "students_graded": 0,
            "average_score": None,
            "highest_score": None,
            "lowest_score": None,
            "pass_rate": None,
            "grade_distribution": {}
        }
    
    scores = [float(g["total_score"]) for g in grades.data if g["total_score"]]
    
    # Calculate statistics
    total_students = len(grades.data)
    students_graded = len(scores)
    average_score = sum(scores) / students_graded if students_graded > 0 else None
    highest_score = max(scores) if scores else None
    lowest_score = min(scores) if scores else None
    
    # Pass rate (assuming 40% is passing)
    passing_scores = [s for s in scores if s >= 40]
    pass_rate = (len(passing_scores) / students_graded * 100) if students_graded > 0 else None
    
    # Grade distribution
    grade_distribution = {}
    for grade in grades.data:
        letter = grade["grade_letter"]
        if letter:
            grade_distribution[letter] = grade_distribution.get(letter, 0) + 1
    
    return {
        "total_students": total_students,
        "students_graded": students_graded,
        "average_score": average_score,
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "pass_rate": pass_rate,
        "grade_distribution": grade_distribution
    }


@router.get("/analytics/student-performance/{student_id}")
async def get_student_performance(
    student_id: str,
    session_id: str,
    term_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get performance summary for a student across all subjects"""

    await PermissionChecker.verify_can_view_student(current_user, student_id, db)

    # Get student details
    student = db.table("students").select(
        "first_name, last_name"
    ).eq("id", student_id).execute()
    
    if not student.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    student_data = student.data[0]
    student_name = f"{student_data['first_name']} {student_data['last_name']}"
    
    # Get all subject grades
    subject_grades = db.table("subject_grades").select(
        "*, subjects(name)"
    ).eq("student_id", student_id).eq(
        "session_id", session_id
    ).eq("term_id", term_id).execute()
    
    if not subject_grades.data:
        return {
            "student_id": student_id,
            "student_name": student_name,
            "session_id": session_id,
            "term_id": term_id,
            "total_subjects": 0,
            "average_score": None,
            "overall_position": None,
            "class_size": None,
            "subject_performances": []
        }
    
    total_subjects = len(subject_grades.data)
    scores = [float(sg["total_score"]) for sg in subject_grades.data if sg["total_score"]]
    average_score = sum(scores) / len(scores) if scores else None
    
    # Get position from report card
    report_card = db.table("report_cards").select(
        "overall_position, class_size"
    ).eq("student_id", student_id).eq(
        "session_id", session_id
    ).eq("term_id", term_id).execute()
    
    overall_position = None
    class_size = None
    if report_card.data:
        overall_position = report_card.data[0]["overall_position"]
        class_size = report_card.data[0]["class_size"]
    
    return {
        "student_id": student_id,
        "student_name": student_name,
        "session_id": session_id,
        "term_id": term_id,
        "total_subjects": total_subjects,
        "average_score": average_score,
        "overall_position": overall_position,
        "class_size": class_size,
        "subject_performances": subject_grades.data
    }
