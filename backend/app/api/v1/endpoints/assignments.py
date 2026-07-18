"""
Assignment and Enrollment API endpoints.
Handles subject assignments (teacher-subject-class) and class enrollments (student-class).
"""

from fastapi import APIRouter, Request, status
from typing import List
from datetime import datetime
from uuid import UUID
import uuid
import logging

from app.models.academic import (
    SubjectAssignmentCreate,
    SubjectAssignmentResponse,
    ClassEnrollmentCreate,
    ClassEnrollmentUpdate,
    ClassEnrollmentResponse
)
from app.core.database import get_supabase
from app.core.security import get_current_user_from_token, get_token_from_request
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    DatabaseError,
    AuthorizationError,
    DuplicateRecordError
)

router = APIRouter()
logger = logging.getLogger(__name__)


def require_admin(user: dict):
    """Ensure user is school admin, system admin, dean, or registrar."""
    if user.get("role") not in ["admin", "system_admin", "dean", "registrar"]:
        raise AuthorizationError("Insufficient permissions to manage assignments")


# ============================================
# SUBJECT ASSIGNMENT ENDPOINTS
# ============================================

@router.post("/subject", response_model=SubjectAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_subject_assignment(request: Request, data: SubjectAssignmentCreate):
    """Assign a teacher to teach a subject to a class. Only admins can create assignments.

    Writes to teacher_class_assignments - the table the Teacher Assignments
    page, report cards, and every teacher stat actually read from. This
    endpoint used to write to the older, parallel subject_assignments table,
    which meant an assignment made here would show "successful" but the
    teacher would still show 0 subjects everywhere else in the app.
    """
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)

        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        # Verify teacher exists and belongs to organization
        teacher_check = supabase.table('teachers').select('id').eq('id', str(data.teacher_id)).eq(
            'organization_id', user["school_id"]
        ).execute()

        if not teacher_check.data:
            raise ValidationError("Invalid teacher ID or teacher not in your organization")

        # Verify subject exists and belongs to organization
        subject_check = supabase.table('subjects').select('id').eq('id', str(data.subject_id)).eq(
            'organization_id', user["school_id"]
        ).execute()

        if not subject_check.data:
            raise ValidationError("Invalid subject ID or subject not in your organization")

        # Verify class exists and belongs to organization
        class_check = supabase.table('classes').select('id').eq('id', str(data.class_id)).eq(
            'organization_id', user["school_id"]
        ).execute()

        if not class_check.data:
            raise ValidationError("Invalid class ID or class not in your organization")

        # Verify session exists and belongs to organization
        session_check = supabase.table('academic_sessions').select('id').eq('id', str(data.session_id)).eq(
            'organization_id', user["school_id"]
        ).execute()

        if not session_check.data:
            raise ValidationError("Invalid session ID or session not in your organization")

        # Verify term if provided
        if data.term_id:
            term_check = supabase.table('terms').select('id, session_id').eq('id', str(data.term_id)).execute()

            if not term_check.data:
                raise ValidationError("Invalid term ID")

            if term_check.data[0]['session_id'] != str(data.session_id):
                raise ValidationError("Term does not belong to the specified session")

        # Check for duplicate assignment
        dup_query = supabase.table('teacher_class_assignments').select('id').eq(
            'teacher_id', str(data.teacher_id)
        ).eq('subject_id', str(data.subject_id)).eq('class_id', str(data.class_id))
        if data.term_id:
            dup_query = dup_query.eq('term_id', str(data.term_id))
        else:
            dup_query = dup_query.is_('term_id', 'null')
        dup_check = dup_query.execute()

        if dup_check.data:
            raise DuplicateRecordError("Subject assignment", "teacher-subject-class-term", "this combination")

        # Create assignment
        assignment_data = {
            'id': str(uuid.uuid4()),
            'teacher_id': str(data.teacher_id),
            'subject_id': str(data.subject_id),
            'class_id': str(data.class_id),
            'session_id': str(data.session_id),
            'term_id': str(data.term_id) if data.term_id else None,
            'is_form_teacher': data.is_form_teacher,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
        }

        result = supabase.table('teacher_class_assignments').insert(assignment_data).execute()

        if not result.data:
            raise DatabaseError("Failed to create subject assignment")

        logger.info(f"Created subject assignment for teacher {data.teacher_id}")

        # Enrich response
        assignment = result.data[0]

        # Get teacher name
        teacher = supabase.table('teachers').select('first_name, last_name').eq('id', assignment['teacher_id']).execute()
        if teacher.data:
            assignment['teacher_name'] = f"{teacher.data[0]['first_name']} {teacher.data[0]['last_name']}"

        # Get subject name
        subject = supabase.table('subjects').select('name').eq('id', assignment['subject_id']).execute()
        if subject.data:
            assignment['subject_name'] = subject.data[0]['name']

        # Get class name
        cls = supabase.table('classes').select('name').eq('id', assignment['class_id']).execute()
        if cls.data:
            assignment['class_name'] = cls.data[0]['name']

        return assignment

    except (AuthorizationError, ValidationError, DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"Error creating subject assignment: {e}")
        raise DatabaseError(f"Failed to create subject assignment: {str(e)}")


@router.delete("/subject/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject_assignment(request: Request, assignment_id: UUID):
    """Remove a subject assignment. Only admins can delete assignments."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)

        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        # Get assignment and verify through teacher's organization
        assignment = supabase.table('teacher_class_assignments').select('*, teachers!inner(organization_id)').eq(
            'id', str(assignment_id)
        ).execute()

        if not assignment.data:
            raise NotFoundError("Subject assignment", assignment_id)

        # Verify organization
        if assignment.data[0]['teachers']['organization_id'] != str(user["school_id"]):
            raise NotFoundError("Subject assignment", assignment_id)

        supabase.table('teacher_class_assignments').delete().eq('id', str(assignment_id)).execute()

        logger.info(f"Deleted subject assignment: {assignment_id}")

    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting subject assignment: {e}")
        raise DatabaseError(f"Failed to delete subject assignment: {str(e)}")


# ============================================
# CLASS ENROLLMENT ENDPOINTS
# ============================================

@router.post("/enrollment", response_model=ClassEnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_class_enrollment(request: Request, data: ClassEnrollmentCreate):
    """Enroll a student in a class. Only admins can create enrollments."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify student exists and belongs to organization
        student_check = supabase.table('students').select('id').eq('id', str(data.student_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not student_check.data:
            raise ValidationError("Invalid student ID or student not in your organization")
        
        # Verify class exists and belongs to organization
        class_check = supabase.table('classes').select('id').eq('id', str(data.class_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not class_check.data:
            raise ValidationError("Invalid class ID or class not in your organization")
        
        # Verify session exists and belongs to organization
        session_check = supabase.table('academic_sessions').select('id').eq('id', str(data.session_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not session_check.data:
            raise ValidationError("Invalid session ID or session not in your organization")
        
        # Check for duplicate enrollment (one enrollment per student per session)
        dup_check = supabase.table('class_enrollments').select('id').eq(
            'student_id', str(data.student_id)
        ).eq('session_id', str(data.session_id)).execute()
        
        if dup_check.data:
            raise DuplicateRecordError("Class enrollment", "student-session", "this student in this session")
        
        # Create enrollment
        enrollment_data = {
            'id': str(uuid.uuid4()),
            'student_id': str(data.student_id),
            'class_id': str(data.class_id),
            'session_id': str(data.session_id),
            'enrollment_date': data.enrollment_date.isoformat(),
            'status': data.status,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('class_enrollments').insert(enrollment_data).execute()

        if not result.data:
            raise DatabaseError("Failed to create class enrollment")

        # students.current_class_id (not class_enrollments) is what the rest of
        # the app reads to determine a student's class - keep it in sync here.
        supabase.table('students').update({
            'current_class_id': str(data.class_id),
            'status': 'active',
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', str(data.student_id)).execute()

        logger.info(f"Created class enrollment for student {data.student_id}")
        
        # Enrich response
        enrollment = result.data[0]
        
        # Get student name
        student = supabase.table('students').select('first_name, middle_name, last_name').eq('id', enrollment['student_id']).execute()
        if student.data:
            enrollment['student_name'] = f"{student.data[0]['first_name']} {student.data[0].get('middle_name') or ''} {student.data[0]['last_name']}".replace('  ', ' ')
        
        # Get class name
        cls = supabase.table('classes').select('name').eq('id', enrollment['class_id']).execute()
        if cls.data:
            enrollment['class_name'] = cls.data[0]['name']
        
        return enrollment
        
    except (AuthorizationError, ValidationError, DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"Error creating class enrollment: {e}")
        raise DatabaseError(f"Failed to create class enrollment: {str(e)}")


@router.put("/enrollment/{enrollment_id}", response_model=ClassEnrollmentResponse)
def update_class_enrollment(request: Request, enrollment_id: UUID, data: ClassEnrollmentUpdate):
    """Update class enrollment (e.g., change class or status). Only admins can update."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get enrollment and verify through student's organization
        enrollment = supabase.table('class_enrollments').select('*, students!inner(organization_id)').eq(
            'id', str(enrollment_id)
        ).execute()
        
        if not enrollment.data:
            raise NotFoundError("Class enrollment", enrollment_id)
        
        # Verify organization
        if enrollment.data[0]['students']['organization_id'] != str(user["school_id"]):
            raise NotFoundError("Class enrollment", enrollment_id)
        
        # Verify new class if provided
        if data.class_id:
            class_check = supabase.table('classes').select('id').eq('id', str(data.class_id)).eq(
                'organization_id', user["school_id"]
            ).execute()
            
            if not class_check.data:
                raise ValidationError("Invalid class ID")
        
        # model_dump(mode="json") already serializes date/UUID fields to strings
        update_data = {k: v for k, v in data.model_dump(mode="json", exclude_unset=True).items() if v is not None}
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = supabase.table('class_enrollments').update(update_data).eq('id', str(enrollment_id)).execute()

            if not result.data:
                raise DatabaseError("Failed to update class enrollment")

            if 'class_id' in update_data:
                supabase.table('students').update({
                    'current_class_id': update_data['class_id'],
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', enrollment.data[0]['student_id']).execute()

            logger.info(f"Updated class enrollment: {enrollment_id}")
            return result.data[0]
        
        return enrollment.data[0]
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating class enrollment: {e}")
        raise DatabaseError(f"Failed to update class enrollment: {str(e)}")


@router.delete("/enrollment/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class_enrollment(request: Request, enrollment_id: UUID):
    """Remove a class enrollment. Only admins can delete enrollments."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get enrollment and verify through student's organization
        enrollment = supabase.table('class_enrollments').select('*, students!inner(organization_id)').eq(
            'id', str(enrollment_id)
        ).execute()
        
        if not enrollment.data:
            raise NotFoundError("Class enrollment", enrollment_id)
        
        # Verify organization
        if enrollment.data[0]['students']['organization_id'] != str(user["school_id"]):
            raise NotFoundError("Class enrollment", enrollment_id)
        
        supabase.table('class_enrollments').delete().eq('id', str(enrollment_id)).execute()
        
        logger.info(f"Deleted class enrollment: {enrollment_id}")
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting class enrollment: {e}")
        raise DatabaseError(f"Failed to delete class enrollment: {str(e)}")
