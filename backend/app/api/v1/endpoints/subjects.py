"""
Subjects API endpoints.
Handles CRUD operations for subjects.
"""

from fastapi import APIRouter, Request, status
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import logging

from app.models.academic import SubjectCreate, SubjectUpdate, SubjectResponse
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
    """Ensure user is school admin or system admin."""
    if user.get("role") not in ["admin", "system_admin"]:
        raise AuthorizationError("Only school administrators can manage subjects")


@router.get("", response_model=List[SubjectResponse])
async def list_subjects(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    subject_type: Optional[str] = None
):
    """List all subjects for the user's organization."""
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
        
        query = supabase.table('subjects').select('*').eq('organization_id', user["school_id"])
        
        if subject_type:
            query = query.eq('subject_type', subject_type)
        
        query = query.order('name').range(skip, skip + limit - 1)
        response = query.execute()

        # Batch teacher counts in one query instead of one per subject
        # (was causing N+1 slowdowns on this page).
        subject_ids = [s['id'] for s in response.data]
        teacher_counts: dict = {}
        if subject_ids:
            assignments = supabase.table('subject_assignments').select('subject_id').in_(
                'subject_id', subject_ids
            ).execute()
            for row in (assignments.data or []):
                teacher_counts[row['subject_id']] = teacher_counts.get(row['subject_id'], 0) + 1

        # Enrich with teacher count
        enriched_data = []
        for subject in response.data:
            subject['teacher_count'] = teacher_counts.get(subject['id'], 0)
            enriched_data.append(subject)
        
        logger.info(f"Listed {len(enriched_data)} subjects for org {user['school_id']}")
        return enriched_data
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing subjects: {e}")
        raise DatabaseError(f"Failed to list subjects: {str(e)}")


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(request: Request, data: SubjectCreate):
    """Create a new subject. Only school admins can create subjects."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Check if subject code already exists
        if data.code:
            code_check = supabase.table('subjects').select('id').eq(
                'code', data.code
            ).eq('organization_id', user["school_id"]).execute()
            
            if code_check.data:
                raise ValidationError(f"Subject with code '{data.code}' already exists")
        
        subject_data = {
            'organization_id': str(user["school_id"]),
            'name': data.name,
            'code': data.code,
            'subject_type': data.subject_type,
            'description': data.description,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('subjects').insert(subject_data).execute()
        
        if not result.data:
            raise DatabaseError("Failed to create subject")
        
        logger.info(f"Created subject: {data.name} for org {user['school_id']}")
        
        created_subject = result.data[0]
        created_subject['teacher_count'] = 0
        return created_subject
        
    except (AuthorizationError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error creating subject: {e}")
        raise DatabaseError(f"Failed to create subject: {str(e)}")


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(request: Request, subject_id: UUID):
    """Get subject by ID."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        response = supabase.table('subjects').select('*').eq('id', str(subject_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not response.data:
            raise NotFoundError("Subject", subject_id)
        
        subject = response.data[0]
        
        # Get teacher count
        teacher_count_response = supabase.table('subject_assignments').select('id', count='exact').eq(
            'subject_id', str(subject_id)
        ).execute()
        subject['teacher_count'] = teacher_count_response.count if hasattr(teacher_count_response, 'count') else 0
        
        return subject
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting subject: {e}")
        raise DatabaseError(f"Failed to get subject: {str(e)}")


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(request: Request, subject_id: UUID, data: SubjectUpdate):
    """Update subject. Only school admins can update subjects."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        existing = supabase.table('subjects').select('*').eq('id', str(subject_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Subject", subject_id)
        
        # Check if new code conflicts
        if data.code and data.code != existing.data[0].get('code'):
            code_check = supabase.table('subjects').select('id').eq(
                'code', data.code
            ).eq('organization_id', user["school_id"]).execute()
            
            if code_check.data:
                raise ValidationError(f"Subject with code '{data.code}' already exists")
        
        update_data = {k: v for k, v in data.model_dump(mode="json", exclude_unset=True).items() if v is not None}
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = supabase.table('subjects').update(update_data).eq('id', str(subject_id)).execute()
            
            if not result.data:
                raise DatabaseError("Failed to update subject")
            
            logger.info(f"Updated subject: {subject_id}")
            return result.data[0]
        
        return existing.data[0]
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating subject: {e}")
        raise DatabaseError(f"Failed to update subject: {str(e)}")


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(request: Request, subject_id: UUID):
    """Delete subject. Only school admins can delete subjects."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        existing = supabase.table('subjects').select('*').eq('id', str(subject_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Subject", subject_id)
        
        # Check if subject has assignments
        assignment_check = supabase.table('subject_assignments').select('id', count='exact').eq(
            'subject_id', str(subject_id)
        ).execute()
        
        if hasattr(assignment_check, 'count') and assignment_check.count > 0:
            raise ValidationError(f"Cannot delete subject with {assignment_check.count} teacher assignments")
        
        supabase.table('subjects').delete().eq('id', str(subject_id)).execute()
        
        logger.info(f"Deleted subject: {subject_id}")
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting subject: {e}")
        raise DatabaseError(f"Failed to delete subject: {str(e)}")
