"""
Teachers API endpoints.
Handles CRUD operations for teachers and their subject assignments.
"""

from fastapi import APIRouter, Request, status, Query
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID
import uuid
import logging

from app.models.teacher import (
    TeacherCreate,
    TeacherUpdate,
    TeacherResponse
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
    """Ensure user is school admin or system admin."""
    if user.get("role") not in ["admin", "system_admin"]:
        raise AuthorizationError("Insufficient permissions to manage teachers")


def calculate_age(dob: date) -> int:
    """Calculate age from date of birth."""
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def calculate_years_of_service(employment_date: date) -> int:
    """Calculate years of service from employment date."""
    today = date.today()
    years = today.year - employment_date.year - ((today.month, today.day) < (employment_date.month, employment_date.day))
    return max(0, years)


# ============================================
# TEACHER ENDPOINTS
# ============================================

@router.get("", response_model=List[TeacherResponse])
async def list_teachers(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name or staff number")
):
    """List all teachers for the user's organization."""
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
        
        query = supabase.table('teachers').select('*').eq('organization_id', user["school_id"])
        
        # Apply filters
        if status:
            query = query.eq('status', status)
        
        if search:
            # Search in staff_number, first_name, last_name
            query = query.or_(f'staff_number.ilike.%{search}%,first_name.ilike.%{search}%,last_name.ilike.%{search}%')
        
        query = query.order('last_name').order('first_name').range(skip, skip + limit - 1)
        response = query.execute()

        # Count subject assignments for all teachers in one query instead of
        # one round-trip per teacher (was causing N+1 slowdowns on this page).
        teacher_ids = [t['id'] for t in response.data]
        subject_counts: dict = {}
        if teacher_ids:
            assignments = supabase.table('subject_assignments').select('teacher_id').in_(
                'teacher_id', teacher_ids
            ).execute()
            for row in (assignments.data or []):
                subject_counts[row['teacher_id']] = subject_counts.get(row['teacher_id'], 0) + 1

        # Enrich data
        enriched_data = []
        for teacher in response.data:
            # Add full name
            teacher['full_name'] = f"{teacher['first_name']} {teacher.get('middle_name') or ''} {teacher['last_name']}".replace('  ', ' ')

            # Calculate age
            if teacher.get('date_of_birth'):
                dob = datetime.fromisoformat(teacher['date_of_birth']).date()
                teacher['age'] = calculate_age(dob)

            # Calculate years of service
            if teacher.get('employment_date'):
                emp_date = datetime.fromisoformat(teacher['employment_date']).date()
                teacher['years_of_service'] = calculate_years_of_service(emp_date)

            teacher['subject_count'] = subject_counts.get(teacher['id'], 0)

            enriched_data.append(teacher)
        
        logger.info(f"Listed {len(enriched_data)} teachers for org {user['school_id']}")
        return enriched_data
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing teachers: {e}")
        raise DatabaseError(f"Failed to list teachers: {str(e)}")


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(request: Request, data: TeacherCreate):
    """Register a new teacher. Only admins can register teachers."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Check if staff number already exists in this organization (scoped -
        # staff numbers are only meant to be unique within a school, so an
        # unscoped check here could wrongly block a valid registration just
        # because another, unrelated school already used the same number).
        staff_check = supabase.table('teachers').select('id').eq(
            'staff_number', data.staff_number
        ).eq('organization_id', str(user["school_id"])).execute()

        if staff_check.data:
            raise DuplicateRecordError("Teacher", "staff_number", data.staff_number)
        
        # Check if user_id already has a teacher record
        user_check = supabase.table('teachers').select('id').eq(
            'user_id', str(data.user_id)
        ).execute()
        
        if user_check.data:
            raise ValidationError("This user already has a teacher record")
        
        # Verify user exists and belongs to organization
        user_verify = supabase.table('users').select('id, school_id, role').eq(
            'id', str(data.user_id)
        ).execute()

        if not user_verify.data:
            raise ValidationError("Invalid user ID")

        if user_verify.data[0]['school_id'] != str(user["school_id"]):
            raise ValidationError("User must belong to your organization")
        
        # Create teacher
        teacher_data = {
            'id': str(uuid.uuid4()),
            'user_id': str(data.user_id),
            'organization_id': str(user["school_id"]),
            'staff_number': data.staff_number,
            'first_name': data.first_name,
            'middle_name': data.middle_name,
            'last_name': data.last_name,
            'date_of_birth': data.date_of_birth.isoformat() if data.date_of_birth else None,
            'gender': data.gender,
            'email': data.email,
            'phone': data.phone,
            'address': data.address,
            'state_of_origin': data.state_of_origin,
            'lga': data.lga,
            'nationality': data.nationality,
            'qualification': data.qualification,
            'specialization': data.specialization,
            'employment_date': data.employment_date.isoformat(),
            'employment_type': data.employment_type,
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('teachers').insert(teacher_data).execute()
        
        if not result.data:
            raise DatabaseError("Failed to create teacher")
        
        logger.info(f"Created teacher: {data.staff_number} for org {user['school_id']}")
        
        created_teacher = result.data[0]
        created_teacher['full_name'] = f"{data.first_name} {data.middle_name or ''} {data.last_name}".replace('  ', ' ')
        if data.date_of_birth:
            created_teacher['age'] = calculate_age(data.date_of_birth)
        created_teacher['years_of_service'] = calculate_years_of_service(data.employment_date)
        created_teacher['subject_count'] = 0
        
        return created_teacher
        
    except (AuthorizationError, ValidationError, DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"Error creating teacher: {e}")
        raise DatabaseError(f"Failed to create teacher: {str(e)}")


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(request: Request, teacher_id: UUID):
    """Get teacher by ID with full details."""
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
        
        response = supabase.table('teachers').select('*').eq('id', str(teacher_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not response.data:
            raise NotFoundError("Teacher", teacher_id)
        
        teacher = response.data[0]
        
        # Enrich data
        teacher['full_name'] = f"{teacher['first_name']} {teacher.get('middle_name') or ''} {teacher['last_name']}".replace('  ', ' ')
        
        if teacher.get('date_of_birth'):
            dob = datetime.fromisoformat(teacher['date_of_birth']).date()
            teacher['age'] = calculate_age(dob)
        
        if teacher.get('employment_date'):
            emp_date = datetime.fromisoformat(teacher['employment_date']).date()
            teacher['years_of_service'] = calculate_years_of_service(emp_date)
        
        # Count subject assignments
        subject_count = supabase.table('subject_assignments').select('id', count='exact').eq(
            'teacher_id', teacher['id']
        ).execute()
        teacher['subject_count'] = subject_count.count if hasattr(subject_count, 'count') else 0
        
        return teacher
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting teacher: {e}")
        raise DatabaseError(f"Failed to get teacher: {str(e)}")


@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(request: Request, teacher_id: UUID, data: TeacherUpdate):
    """Update teacher details. Only admins can update."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        existing = supabase.table('teachers').select('*').eq('id', str(teacher_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Teacher", teacher_id)
        
        # model_dump(mode="json") already serializes date fields to ISO strings
        update_data = {k: v for k, v in data.model_dump(mode="json", exclude_unset=True).items() if v is not None}
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = supabase.table('teachers').update(update_data).eq('id', str(teacher_id)).execute()
            
            if not result.data:
                raise DatabaseError("Failed to update teacher")
            
            logger.info(f"Updated teacher: {teacher_id}")
            
            updated_teacher = result.data[0]
            updated_teacher['full_name'] = f"{updated_teacher['first_name']} {updated_teacher.get('middle_name') or ''} {updated_teacher['last_name']}".replace('  ', ' ')
            
            return updated_teacher
        
        return existing.data[0]
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating teacher: {e}")
        raise DatabaseError(f"Failed to update teacher: {str(e)}")


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(request: Request, teacher_id: UUID):
    """Delete teacher. Only admins can delete teachers."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        existing = supabase.table('teachers').select('*').eq('id', str(teacher_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Teacher", teacher_id)
        
        # Check for dependencies (subject assignments)
        assignments = supabase.table('subject_assignments').select('id', count='exact').eq(
            'teacher_id', str(teacher_id)
        ).execute()
        
        if assignments.data:
            raise ValidationError(
                f"Cannot delete teacher with {len(assignments.data)} active subject assignments. "
                "Remove assignments first."
            )
        
        supabase.table('teachers').delete().eq('id', str(teacher_id)).execute()
        
        logger.info(f"Deleted teacher: {teacher_id}")
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting teacher: {e}")
        raise DatabaseError(f"Failed to delete teacher: {str(e)}")


@router.get("/{teacher_id}/assignments")
async def get_teacher_assignments(request: Request, teacher_id: UUID):
    """Get all subject assignments for a teacher."""
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
        
        # Verify teacher exists and belongs to user's org
        teacher_check = supabase.table('teachers').select('id').eq('id', str(teacher_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not teacher_check.data:
            raise NotFoundError("Teacher", teacher_id)
        
        # Get assignments
        response = supabase.table('subject_assignments').select('*').eq('teacher_id', str(teacher_id)).execute()

        # Batch subject/class name lookups in two queries total instead of
        # two per assignment.
        subject_ids = list({a['subject_id'] for a in response.data if a.get('subject_id')})
        class_ids = list({a['class_id'] for a in response.data if a.get('class_id')})
        subject_names: dict = {}
        class_names: dict = {}
        if subject_ids:
            subjects_resp = supabase.table('subjects').select('id, name').in_('id', subject_ids).execute()
            subject_names = {row['id']: row['name'] for row in (subjects_resp.data or [])}
        if class_ids:
            classes_resp = supabase.table('classes').select('id, name').in_('id', class_ids).execute()
            class_names = {row['id']: row['name'] for row in (classes_resp.data or [])}

        # Enrich with subject and class names
        enriched_data = []
        for assignment in response.data:
            if assignment.get('subject_id') in subject_names:
                assignment['subject_name'] = subject_names[assignment['subject_id']]
            if assignment.get('class_id') in class_names:
                assignment['class_name'] = class_names[assignment['class_id']]
            enriched_data.append(assignment)
        
        logger.info(f"Retrieved {len(enriched_data)} assignments for teacher {teacher_id}")
        return enriched_data
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting teacher assignments: {e}")
        raise DatabaseError(f"Failed to get teacher assignments: {str(e)}")
