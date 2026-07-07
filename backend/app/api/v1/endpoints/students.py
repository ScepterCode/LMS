"""
Students API endpoints.
Handles CRUD operations for students and their guardians.
"""

from fastapi import APIRouter, Request, status, Query
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID
import uuid
import logging

from app.models.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    GuardianCreate,
    GuardianUpdate,
    GuardianResponse
)
from app.core.database import get_supabase
from app.core.security import get_current_user_from_token, get_token_from_request
from app.core.permissions import PermissionChecker
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    DatabaseError,
    AuthorizationError,
    DuplicateRecordError
)

router = APIRouter()
logger = logging.getLogger(__name__)


def require_school_admin(user: dict):
    """Ensure user is school admin or system admin."""
    if user.get("role") not in ["admin", "system_admin", "teacher"]:
        raise AuthorizationError("Insufficient permissions to manage students")


async def require_teacher_owns_class(user: dict, class_id, supabase):
    """For teacher role, verify they are the form teacher of class_id.

    Admins/system_admins are unrestricted; called only after
    require_school_admin() has already confirmed the role is allowed at
    all. Teachers may only create/edit students (and their guardians) in
    a class they are the form teacher of, same as every other
    class-scoped teacher permission in this app.
    """
    if user.get("role") != "teacher":
        return
    if not class_id:
        raise AuthorizationError("Teachers must assign the student to one of their own classes")
    await PermissionChecker.verify_form_teacher_permission(
        user.get("teacher_id"), str(class_id), supabase
    )


def calculate_age(dob: date) -> int:
    """Calculate age from date of birth."""
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


# ============================================
# STUDENT ENDPOINTS
# ============================================

@router.get("", response_model=List[StudentResponse])
async def list_students(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    class_id: Optional[UUID] = None,
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name or admission number")
):
    """List all students for the user's organization."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        query = supabase.table('students').select('*').eq('organization_id', user["school_id"])
        
        # Apply filters
        if class_id:
            query = query.eq('current_class_id', str(class_id))
        
        if status:
            query = query.eq('status', status)
        
        if search:
            # Search in admission_number, first_name, last_name
            query = query.or_(f'admission_number.ilike.%{search}%,first_name.ilike.%{search}%,last_name.ilike.%{search}%')
        
        query = query.order('last_name').order('first_name').range(skip, skip + limit - 1)
        response = query.execute()
        
        # Enrich data
        enriched_data = []
        for student in response.data:
            # Add full name
            student['full_name'] = f"{student['first_name']} {student.get('middle_name') or ''} {student['last_name']}".replace('  ', ' ')
            
            # Calculate age
            if student.get('date_of_birth'):
                dob = datetime.fromisoformat(student['date_of_birth']).date()
                student['age'] = calculate_age(dob)
            
            # Get class name
            if student.get('current_class_id'):
                class_response = supabase.table('classes').select('name').eq('id', student['current_class_id']).execute()
                if class_response.data:
                    student['class_name'] = class_response.data[0]['name']
            
            enriched_data.append(student)
        
        logger.info(f"Listed {len(enriched_data)} students for org {user['school_id']}")
        return enriched_data
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing students: {e}")
        raise DatabaseError(f"Failed to list students: {str(e)}")


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(request: Request, data: StudentCreate):
    """Register a new student. Only admins and teachers can register students."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Check if admission number already exists
        admission_check = supabase.table('students').select('id').eq(
            'admission_number', data.admission_number
        ).eq('organization_id', user["school_id"]).execute()
        
        if admission_check.data:
            raise DuplicateRecordError("Student", "admission_number", data.admission_number)
        
        # Validate class if provided
        if data.current_class_id:
            class_check = supabase.table('classes').select('id').eq(
                'id', str(data.current_class_id)
            ).eq('organization_id', user["school_id"]).execute()

            if not class_check.data:
                raise ValidationError("Invalid class ID")

        await require_teacher_owns_class(user, data.current_class_id, supabase)

        # Create student
        student_data = {
            'id': str(uuid.uuid4()),
            'organization_id': str(user["school_id"]),
            'admission_number': data.admission_number,
            'first_name': data.first_name,
            'middle_name': data.middle_name,
            'last_name': data.last_name,
            'date_of_birth': data.date_of_birth.isoformat(),
            'gender': data.gender,
            'blood_group': data.blood_group,
            'email': data.email,
            'phone': data.phone,
            'address': data.address,
            'state_of_origin': data.state_of_origin,
            'lga': data.lga,
            'nationality': data.nationality,
            'religion': data.religion,
            'medical_conditions': data.medical_conditions,
            'allergies': data.allergies,
            'current_class_id': str(data.current_class_id) if data.current_class_id else None,
            'admission_date': data.admission_date.isoformat(),
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('students').insert(student_data).execute()
        
        if not result.data:
            raise DatabaseError("Failed to create student")
        
        logger.info(f"Created student: {data.admission_number} for org {user['school_id']}")
        
        created_student = result.data[0]
        created_student['full_name'] = f"{data.first_name} {data.middle_name or ''} {data.last_name}".replace('  ', ' ')
        created_student['age'] = calculate_age(data.date_of_birth)
        
        return created_student
        
    except (AuthorizationError, ValidationError, DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        raise DatabaseError(f"Failed to create student: {str(e)}")


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(request: Request, student_id: UUID):
    """Get student by ID with full details."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        response = supabase.table('students').select('*').eq('id', str(student_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not response.data:
            raise NotFoundError("Student", student_id)
        
        student = response.data[0]
        
        # Enrich data
        student['full_name'] = f"{student['first_name']} {student.get('middle_name') or ''} {student['last_name']}".replace('  ', ' ')
        
        if student.get('date_of_birth'):
            dob = datetime.fromisoformat(student['date_of_birth']).date()
            student['age'] = calculate_age(dob)
        
        if student.get('current_class_id'):
            class_response = supabase.table('classes').select('name').eq('id', student['current_class_id']).execute()
            if class_response.data:
                student['class_name'] = class_response.data[0]['name']
        
        return student
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting student: {e}")
        raise DatabaseError(f"Failed to get student: {str(e)}")


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(request: Request, student_id: UUID, data: StudentUpdate):
    """Update student details. Only admins and teachers can update."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        existing = supabase.table('students').select('*').eq('id', str(student_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Student", student_id)

        # A teacher may only edit students currently in a class they are
        # the form teacher of.
        await require_teacher_owns_class(user, existing.data[0].get('current_class_id'), supabase)

        # Validate class if provided
        if data.current_class_id:
            class_check = supabase.table('classes').select('id').eq(
                'id', str(data.current_class_id)
            ).eq('organization_id', user["school_id"]).execute()

            if not class_check.data:
                raise ValidationError("Invalid class ID")

            # If a teacher is also moving the student to a different
            # class, they must be the form teacher of the destination
            # class too, not just the origin.
            await require_teacher_owns_class(user, data.current_class_id, supabase)

        update_data = {k: v for k, v in data.model_dump(mode="json", exclude_unset=True).items() if v is not None}
        if update_data:
            # model_dump(mode="json") already serializes date/UUID fields to strings
            if 'current_class_id' in update_data:
                update_data['current_class_id'] = str(update_data['current_class_id'])
            
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = supabase.table('students').update(update_data).eq('id', str(student_id)).execute()
            
            if not result.data:
                raise DatabaseError("Failed to update student")
            
            logger.info(f"Updated student: {student_id}")
            return result.data[0]
        
        return existing.data[0]
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating student: {e}")
        raise DatabaseError(f"Failed to update student: {str(e)}")


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(request: Request, student_id: UUID):
    """Delete student. Only admins can delete students."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        if user.get("role") not in ["admin", "system_admin"]:
            raise AuthorizationError("Only administrators can delete students")
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        existing = supabase.table('students').select('*').eq('id', str(student_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Student", student_id)
        
        supabase.table('students').delete().eq('id', str(student_id)).execute()
        
        logger.info(f"Deleted student: {student_id}")
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting student: {e}")
        raise DatabaseError(f"Failed to delete student: {str(e)}")


# ============================================
# GUARDIAN ENDPOINTS
# ============================================

@router.get("/{student_id}/guardians", response_model=List[GuardianResponse])
async def get_student_guardians(request: Request, student_id: UUID):
    """Get all guardians for a student."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify student exists and belongs to user's org
        student_check = supabase.table('students').select('id').eq('id', str(student_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not student_check.data:
            raise NotFoundError("Student", student_id)
        
        response = supabase.table('student_guardians').select('*').eq('student_id', str(student_id)).order('is_primary', desc=True).execute()
        
        # Add full name
        for guardian in response.data:
            guardian['full_name'] = f"{guardian.get('title') or ''} {guardian['first_name']} {guardian['last_name']}".strip()
        
        logger.info(f"Retrieved {len(response.data)} guardians for student {student_id}")
        return response.data
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting guardians: {e}")
        raise DatabaseError(f"Failed to get guardians: {str(e)}")


@router.post("/{student_id}/guardians", response_model=GuardianResponse, status_code=status.HTTP_201_CREATED)
async def add_guardian(request: Request, student_id: UUID, data: GuardianCreate):
    """Add a guardian to a student."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify student exists
        student_check = supabase.table('students').select('id, current_class_id').eq('id', str(student_id)).eq(
            'organization_id', user["school_id"]
        ).execute()

        if not student_check.data:
            raise NotFoundError("Student", student_id)

        await require_teacher_owns_class(user, student_check.data[0].get('current_class_id'), supabase)

        # If setting as primary, unset other primary guardians
        if data.is_primary:
            supabase.table('student_guardians').update({'is_primary': False}).eq(
                'student_id', str(student_id)
            ).execute()
        
        guardian_data = {
            'student_id': str(student_id),
            'guardian_type': data.guardian_type,
            'title': data.title,
            'first_name': data.first_name,
            'last_name': data.last_name,
            'relationship': data.relationship,
            'phone': data.phone,
            'email': data.email,
            'occupation': data.occupation,
            'address': data.address,
            'is_emergency_contact': data.is_emergency_contact,
            'is_primary': data.is_primary,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('student_guardians').insert(guardian_data).execute()
        
        if not result.data:
            raise DatabaseError("Failed to add guardian")
        
        logger.info(f"Added guardian for student {student_id}")
        
        guardian = result.data[0]
        guardian['full_name'] = f"{data.title or ''} {data.first_name} {data.last_name}".strip()
        return guardian
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error adding guardian: {e}")
        raise DatabaseError(f"Failed to add guardian: {str(e)}")


@router.put("/{student_id}/guardians/{guardian_id}", response_model=GuardianResponse)
async def update_guardian(request: Request, student_id: UUID, guardian_id: UUID, data: GuardianUpdate):
    """Update a guardian's information."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        # Verify the student belongs to this organization (guardians have
        # no organization_id of their own) and get their class for the
        # teacher scope check below.
        student_check = supabase.table('students').select('id, current_class_id').eq(
            'id', str(student_id)
        ).eq('organization_id', user["school_id"]).execute()

        if not student_check.data:
            raise NotFoundError("Student", student_id)

        await require_teacher_owns_class(user, student_check.data[0].get('current_class_id'), supabase)

        # Verify guardian exists and belongs to student
        existing = supabase.table('student_guardians').select('*').eq('id', str(guardian_id)).eq(
            'student_id', str(student_id)
        ).execute()

        if not existing.data:
            raise NotFoundError("Guardian", guardian_id)

        # If setting as primary, unset other primary guardians
        if data.is_primary:
            supabase.table('student_guardians').update({'is_primary': False}).eq(
                'student_id', str(student_id)
            ).neq('id', str(guardian_id)).execute()
        
        update_data = {k: v for k, v in data.model_dump(mode="json", exclude_unset=True).items() if v is not None}
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = supabase.table('student_guardians').update(update_data).eq('id', str(guardian_id)).execute()
            
            if not result.data:
                raise DatabaseError("Failed to update guardian")
            
            logger.info(f"Updated guardian: {guardian_id}")
            return result.data[0]
        
        return existing.data[0]
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating guardian: {e}")
        raise DatabaseError(f"Failed to update guardian: {str(e)}")


@router.delete("/{student_id}/guardians/{guardian_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guardian(request: Request, student_id: UUID, guardian_id: UUID):
    """Remove a guardian from a student."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        # Verify the student belongs to this organization and get their
        # class for the teacher scope check below.
        student_check = supabase.table('students').select('id, current_class_id').eq(
            'id', str(student_id)
        ).eq('organization_id', user["school_id"]).execute()

        if not student_check.data:
            raise NotFoundError("Student", student_id)

        await require_teacher_owns_class(user, student_check.data[0].get('current_class_id'), supabase)

        # Verify guardian exists
        existing = supabase.table('student_guardians').select('*').eq('id', str(guardian_id)).eq(
            'student_id', str(student_id)
        ).execute()

        if not existing.data:
            raise NotFoundError("Guardian", guardian_id)

        supabase.table('student_guardians').delete().eq('id', str(guardian_id)).execute()
        
        logger.info(f"Deleted guardian: {guardian_id}")
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting guardian: {e}")
        raise DatabaseError(f"Failed to delete guardian: {str(e)}")
