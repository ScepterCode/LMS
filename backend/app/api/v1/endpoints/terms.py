"""
Terms API endpoints.
Handles CRUD operations for academic terms.
"""

from fastapi import APIRouter, Request, status, Query
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid
import logging

from app.models.academic import (
    TermCreate,
    TermUpdate,
    TermResponse
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
    """Ensure user is school admin, system admin, or dean."""
    if user.get("role") not in ["admin", "system_admin", "dean"]:
        raise AuthorizationError("Insufficient permissions to manage terms")


# ============================================
# TERM ENDPOINTS
# ============================================

@router.get("", response_model=List[TermResponse])
async def list_terms(
    request: Request,
    session_id: Optional[UUID] = Query(None, description="Filter by session"),
    is_current: Optional[bool] = Query(None, description="Filter by current status")
):
    """List all terms for the user's organization."""
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
        
        # Get terms through their sessions to ensure org isolation
        query = supabase.table('terms').select('*')
        
        if session_id:
            query = query.eq('session_id', str(session_id))
        else:
            # Get all sessions for this org to filter terms
            sessions = supabase.table('academic_sessions').select('id').eq(
                'organization_id', user["school_id"]
            ).execute()
            session_ids = [s['id'] for s in sessions.data]
            if session_ids:
                query = query.in_('session_id', session_ids)
            else:
                return []
        
        if is_current is not None:
            query = query.eq('is_current', is_current)
        
        query = query.order('term_number')
        response = query.execute()
        
        logger.info(f"Listed {len(response.data)} terms for org {user['school_id']}")
        return response.data
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing terms: {e}")
        raise DatabaseError(f"Failed to list terms: {str(e)}")


@router.post("", response_model=TermResponse, status_code=status.HTTP_201_CREATED)
async def create_term(request: Request, data: TermCreate):
    """Create a new term. Only admins can create terms."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify session exists and belongs to organization
        session_check = supabase.table('academic_sessions').select('id, organization_id').eq(
            'id', str(data.session_id)
        ).execute()
        
        if not session_check.data:
            raise ValidationError("Invalid session ID")
        
        if session_check.data[0]['organization_id'] != str(user["school_id"]):
            raise ValidationError("Session does not belong to your organization")
        
        # Check for duplicate term number in this session
        dup_check = supabase.table('terms').select('id').eq(
            'session_id', str(data.session_id)
        ).eq('term_number', data.term_number).execute()
        
        if dup_check.data:
            raise DuplicateRecordError("Term", "term_number", f"{data.term_number} in this session")
        
        # If setting as current, unset other current terms in this session
        if data.is_current:
            supabase.table('terms').update({'is_current': False}).eq(
                'session_id', str(data.session_id)
            ).execute()
        
        # Create term
        term_data = {
            'id': str(uuid.uuid4()),
            'session_id': str(data.session_id),
            'name': data.name,
            'term_number': data.term_number,
            'start_date': data.start_date.isoformat(),
            'end_date': data.end_date.isoformat(),
            'is_current': data.is_current,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('terms').insert(term_data).execute()
        
        if not result.data:
            raise DatabaseError("Failed to create term")
        
        logger.info(f"Created term: {data.name} for session {data.session_id}")
        return result.data[0]
        
    except (AuthorizationError, ValidationError, DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"Error creating term: {e}")
        raise DatabaseError(f"Failed to create term: {str(e)}")


@router.get("/{term_id}", response_model=TermResponse)
async def get_term(request: Request, term_id: UUID):
    """Get term by ID."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get term and verify through session
        term_response = supabase.table('terms').select('*').eq('id', str(term_id)).execute()
        
        if not term_response.data:
            raise NotFoundError("Term", term_id)
        
        term = term_response.data[0]
        
        # Verify session belongs to user's organization
        session_check = supabase.table('academic_sessions').select('organization_id').eq(
            'id', term['session_id']
        ).execute()
        
        if not session_check.data or session_check.data[0]['organization_id'] != str(user["school_id"]):
            raise NotFoundError("Term", term_id)
        
        return term
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting term: {e}")
        raise DatabaseError(f"Failed to get term: {str(e)}")


@router.put("/{term_id}", response_model=TermResponse)
async def update_term(request: Request, term_id: UUID, data: TermUpdate):
    """Update term details. Only admins can update."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get existing term and verify ownership
        term_response = supabase.table('terms').select('*').eq('id', str(term_id)).execute()
        
        if not term_response.data:
            raise NotFoundError("Term", term_id)
        
        term = term_response.data[0]
        
        # Verify session belongs to user's organization
        session_check = supabase.table('academic_sessions').select('organization_id').eq(
            'id', term['session_id']
        ).execute()
        
        if not session_check.data or session_check.data[0]['organization_id'] != str(user["school_id"]):
            raise NotFoundError("Term", term_id)
        
        # If setting as current, unset other current terms in this session
        if data.is_current:
            supabase.table('terms').update({'is_current': False}).eq(
                'session_id', term['session_id']
            ).neq('id', str(term_id)).execute()
        
        # model_dump(mode="json") already serializes date fields to ISO strings
        update_data = {k: v for k, v in data.model_dump(mode="json", exclude_unset=True).items() if v is not None}
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = supabase.table('terms').update(update_data).eq('id', str(term_id)).execute()
            
            if not result.data:
                raise DatabaseError("Failed to update term")
            
            logger.info(f"Updated term: {term_id}")
            return result.data[0]
        
        return term
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating term: {e}")
        raise DatabaseError(f"Failed to update term: {str(e)}")


@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_term(request: Request, term_id: UUID):
    """Delete term. Only admins can delete terms."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get existing term and verify ownership
        term_response = supabase.table('terms').select('*').eq('id', str(term_id)).execute()
        
        if not term_response.data:
            raise NotFoundError("Term", term_id)
        
        term = term_response.data[0]
        
        # Verify session belongs to user's organization
        session_check = supabase.table('academic_sessions').select('organization_id').eq(
            'id', term['session_id']
        ).execute()
        
        if not session_check.data or session_check.data[0]['organization_id'] != str(user["school_id"]):
            raise NotFoundError("Term", term_id)
        
        # Check for dependencies
        assignments = supabase.table('subject_assignments').select('id', count='exact').eq(
            'term_id', str(term_id)
        ).execute()
        
        if assignments.data:
            raise ValidationError(
                f"Cannot delete term with {len(assignments.data)} subject assignments. "
                "Remove assignments first."
            )
        
        supabase.table('terms').delete().eq('id', str(term_id)).execute()
        
        logger.info(f"Deleted term: {term_id}")
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting term: {e}")
        raise DatabaseError(f"Failed to delete term: {str(e)}")


@router.post("/{term_id}/set-current", response_model=TermResponse)
async def set_current_term(request: Request, term_id: UUID):
    """Set a term as the current term. Only admins can set current term."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get term and verify ownership
        term_response = supabase.table('terms').select('*').eq('id', str(term_id)).execute()
        
        if not term_response.data:
            raise NotFoundError("Term", term_id)
        
        term = term_response.data[0]
        
        # Verify session belongs to user's organization
        session_check = supabase.table('academic_sessions').select('organization_id').eq(
            'id', term['session_id']
        ).execute()
        
        if not session_check.data or session_check.data[0]['organization_id'] != str(user["school_id"]):
            raise NotFoundError("Term", term_id)
        
        # Unset all current terms in this session
        supabase.table('terms').update({'is_current': False}).eq(
            'session_id', term['session_id']
        ).execute()
        
        # Set this term as current
        result = supabase.table('terms').update({
            'is_current': True,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', str(term_id)).execute()
        
        if not result.data:
            raise DatabaseError("Failed to set current term")
        
        logger.info(f"Set term {term_id} as current")
        return result.data[0]
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error setting current term: {e}")
        raise DatabaseError(f"Failed to set current term: {str(e)}")
