"""
Classes API endpoints.
Handles CRUD operations for classes (grade levels with sections).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import logging

from app.models.academic import ClassCreate, ClassUpdate, ClassResponse
from app.core.database import get_supabase
from app.core.security import get_current_user_from_token, get_token_from_request
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    DatabaseError,
    AuthorizationError
)

router = APIRouter()
logger = logging.getLogger(__name__)


def require_school_admin(user: dict):
    """Ensure user is school admin, system admin, or dean."""
    if user.get("role") not in ["admin", "system_admin", "dean"]:
        raise AuthorizationError("Only school administrators can manage classes")


@router.get("", response_model=List[ClassResponse])
def list_classes(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    level: Optional[str] = None
):
    """List all classes for the user's organization."""
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
        
        query = supabase.table('classes').select('*').eq('organization_id', user["school_id"])
        
        if level:
            query = query.eq('level', level)
        
        query = query.order('name').range(skip, skip + limit - 1)
        response = query.execute()

        # Batch student counts and class teacher names in two queries total
        # instead of two per class (was causing N+1 slowdowns on this page).
        class_ids = [cls['id'] for cls in response.data]
        student_counts: dict = {}
        if class_ids:
            students_resp = supabase.table('students').select('current_class_id').in_(
                'current_class_id', class_ids
            ).execute()
            for row in (students_resp.data or []):
                cid = row['current_class_id']
                student_counts[cid] = student_counts.get(cid, 0) + 1

        teacher_ids = list({cls['class_teacher_id'] for cls in response.data if cls.get('class_teacher_id')})
        teacher_names: dict = {}
        if teacher_ids:
            teachers_resp = supabase.table('users').select('id, full_name').in_('id', teacher_ids).execute()
            for row in (teachers_resp.data or []):
                teacher_names[row['id']] = row['full_name']

        # Enrich with student count
        enriched_data = []
        for cls in response.data:
            cls['student_count'] = student_counts.get(cls['id'], 0)

            # Get class teacher name if assigned
            if cls.get('class_teacher_id') and cls['class_teacher_id'] in teacher_names:
                cls['class_teacher_name'] = teacher_names[cls['class_teacher_id']]

            enriched_data.append(cls)
        
        logger.info(f"Listed {len(enriched_data)} classes for org {user['school_id']}")
        return enriched_data
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing classes: {e}")
        raise DatabaseError(f"Failed to list classes: {str(e)}")


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(request: Request, data: ClassCreate):
    """Create a new class. Only school admins can create classes."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Validate class teacher if provided
        if data.class_teacher_id:
            teacher_check = supabase.table('users').select('id').eq(
                'id', str(data.class_teacher_id)
            ).eq('school_id', user["school_id"]).eq('role', 'teacher').execute()
            
            if not teacher_check.data:
                raise ValidationError("Class teacher must be a teacher in your school")
        
        # Validate session is provided if subjects are specified
        if data.subject_ids and not data.session_id:
            raise ValidationError("session_id is required when specifying subjects")
        
        # Verify session exists if provided
        if data.session_id:
            session_check = supabase.table('academic_sessions').select('id').eq(
                'id', str(data.session_id)
            ).eq('organization_id', user["school_id"]).execute()
            
            if not session_check.data:
                raise ValidationError(f"Academic session {data.session_id} not found")
        
        class_data = {
            'organization_id': str(user["school_id"]),
            'name': data.name,
            'level': data.level,
            'section': data.section,
            'capacity': data.capacity,
            'class_teacher_id': str(data.class_teacher_id) if data.class_teacher_id else None,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('classes').insert(class_data).execute()
        
        if not result.data:
            raise DatabaseError("Failed to create class")
        
        created_class = result.data[0]
        class_id = created_class['id']
        
        # Add subjects to class if provided
        if data.subject_ids and data.session_id:
            for idx, subject_id in enumerate(data.subject_ids):
                subject_data = {
                    'class_id': class_id,
                    'subject_id': str(subject_id),
                    'session_id': str(data.session_id),
                    'is_mandatory': True,
                    'display_order': idx,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                try:
                    supabase.table('class_subjects').insert(subject_data).execute()
                except Exception as e:
                    logger.warning(f"Failed to add subject {subject_id} to class: {e}")
        
        subject_count = len(data.subject_ids) if data.subject_ids else 0
        logger.info(f"Created class: {data.name} with {subject_count} subjects for org {user['school_id']}")
        
        created_class['student_count'] = 0
        return created_class
        
    except (AuthorizationError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error creating class: {e}")
        raise DatabaseError(f"Failed to create class: {str(e)}")


@router.get("/{class_id}", response_model=ClassResponse)
def get_class(request: Request, class_id: UUID):
    """Get class by ID."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        response = supabase.table('classes').select('*').eq('id', str(class_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not response.data:
            raise NotFoundError("Class", class_id)
        
        cls = response.data[0]
        
        # Get student count
        student_count_response = supabase.table('students').select('id', count='exact').eq(
            'current_class_id', str(class_id)
        ).execute()
        cls['student_count'] = student_count_response.count if hasattr(student_count_response, 'count') else 0
        
        # Get class teacher name
        if cls.get('class_teacher_id'):
            teacher_response = supabase.table('users').select('full_name').eq(
                'id', cls['class_teacher_id']
            ).execute()
            if teacher_response.data:
                cls['class_teacher_name'] = teacher_response.data[0]['full_name']
        
        return cls
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting class: {e}")
        raise DatabaseError(f"Failed to get class: {str(e)}")


@router.put("/{class_id}", response_model=ClassResponse)
def update_class(request: Request, class_id: UUID, data: ClassUpdate):
    """Update class. Only school admins can update classes."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        existing = supabase.table('classes').select('*').eq('id', str(class_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Class", class_id)
        
        # Validate class teacher if provided
        if data.class_teacher_id:
            teacher_check = supabase.table('users').select('id').eq(
                'id', str(data.class_teacher_id)
            ).eq('school_id', user["school_id"]).eq('role', 'teacher').execute()
            
            if not teacher_check.data:
                raise ValidationError("Class teacher must be a teacher in your school")
        
        update_data = {k: v for k, v in data.model_dump(mode="json", exclude_unset=True).items() if v is not None}
        if update_data:
            if 'class_teacher_id' in update_data:
                update_data['class_teacher_id'] = str(update_data['class_teacher_id'])
            
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = supabase.table('classes').update(update_data).eq('id', str(class_id)).execute()
            
            if not result.data:
                raise DatabaseError("Failed to update class")
            
            logger.info(f"Updated class: {class_id}")
            return result.data[0]
        
        return existing.data[0]
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating class: {e}")
        raise DatabaseError(f"Failed to update class: {str(e)}")


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(request: Request, class_id: UUID):
    """Delete class. Only school admins can delete classes."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        existing = supabase.table('classes').select('*').eq('id', str(class_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Class", class_id)
        
        # Check if class has students
        student_check = supabase.table('students').select('id', count='exact').eq(
            'current_class_id', str(class_id)
        ).execute()
        
        if hasattr(student_check, 'count') and student_check.count > 0:
            raise ValidationError(f"Cannot delete class with {student_check.count} students enrolled")
        
        supabase.table('classes').delete().eq('id', str(class_id)).execute()
        
        logger.info(f"Deleted class: {class_id}")
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting class: {e}")
        raise DatabaseError(f"Failed to delete class: {str(e)}")


@router.get("/{class_id}/students", response_model=List[dict])
def get_class_students(request: Request, class_id: UUID):
    """Get all students in a class."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify class exists and belongs to user's org
        class_check = supabase.table('classes').select('id').eq('id', str(class_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not class_check.data:
            raise NotFoundError("Class", class_id)
        
        # Get students
        response = supabase.table('students').select('*').eq('current_class_id', str(class_id)).order('last_name').execute()
        
        logger.info(f"Retrieved {len(response.data)} students for class {class_id}")
        return response.data
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting class students: {e}")
        raise DatabaseError(f"Failed to get class students: {str(e)}")
