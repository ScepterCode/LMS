"""
Academic Sessions API endpoints.
Handles CRUD operations for academic sessions (school years).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import logging

from app.models.academic import (
    AcademicSessionCreate,
    AcademicSessionUpdate,
    AcademicSessionResponse
)
from app.core.database import get_supabase
from app.core.security import get_current_user_from_token, get_token_from_request
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    DatabaseError,
    AuthorizationError
)
from fastapi import Request

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# HELPER FUNCTIONS
# ============================================

def require_school_admin(user: dict):
    """Ensure user is school admin or system admin."""
    if not user:
        raise AuthorizationError("User authentication failed - no valid user found")
    if user.get("role") not in ["admin", "system_admin", "dean"]:
        raise AuthorizationError("Only school administrators can manage academic sessions")


# ============================================
# ACADEMIC SESSION ENDPOINTS
# ============================================

@router.get("", response_model=List[AcademicSessionResponse])
async def list_sessions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    is_current: Optional[bool] = None
):
    """
    List all academic sessions for the user's organization.
    """
    try:
        # Get current user
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        # Get Supabase client
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Build query
        query = supabase.table('academic_sessions').select('*').eq('organization_id', user["school_id"])
        
        # Apply filters
        if is_current is not None:
            query = query.eq('is_current', is_current)
        
        # Apply pagination and ordering
        query = query.order('start_date', desc=True).range(skip, skip + limit - 1)
        
        response = query.execute()
        
        logger.info(f"Listed {len(response.data)} academic sessions for org {user['school_id']}")
        
        return response.data
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise DatabaseError(f"Failed to list academic sessions: {str(e)}")


@router.post("", response_model=AcademicSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: Request,
    data: AcademicSessionCreate
):
    """
    Create a new academic session.
    Only school admins can create sessions.
    """
    try:
        # Get current user
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        # Get Supabase client
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # If setting as current, unset other current sessions
        # Wrap in try-except to handle potential timeouts
        if data.is_current:
            try:
                supabase.table('academic_sessions').update({'is_current': False}).eq(
                    'organization_id', str(user["school_id"])
                ).execute()
            except Exception as e:
                logger.warning(f"Could not unset previous current sessions (may retry): {e}")
                # Don't fail the entire operation due to this
        
        # Create session
        session_data = {
            'organization_id': str(user["school_id"]),
            'name': data.name,
            'start_date': data.start_date.isoformat(),
            'end_date': data.end_date.isoformat(),
            'is_current': data.is_current,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('academic_sessions').insert(session_data).execute()
        
        if not result.data:
            raise DatabaseError("Failed to create academic session")
        
        logger.info(f"Created academic session: {data.name} for org {user['school_id']}")
        
        return result.data[0]
        
    except (AuthorizationError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise DatabaseError(f"Failed to create academic session: {str(e)}")


@router.get("/{session_id}", response_model=AcademicSessionResponse)
async def get_session(
    request: Request,
    session_id: UUID
):
    """
    Get academic session by ID.
    """
    try:
        # Get current user
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed - no valid user found")
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        # Get Supabase client
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get session
        response = supabase.table('academic_sessions').select('*').eq('id', str(session_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not response.data:
            raise NotFoundError("Academic Session", session_id)
        
        return response.data[0]
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise DatabaseError(f"Failed to get academic session: {str(e)}")


@router.put("/{session_id}", response_model=AcademicSessionResponse)
async def update_session(
    request: Request,
    session_id: UUID,
    data: AcademicSessionUpdate
):
    """
    Update academic session.
    Only school admins can update sessions.
    """
    try:
        # Get current user
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        # Get Supabase client
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Check session exists
        existing = supabase.table('academic_sessions').select('*').eq('id', str(session_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Academic Session", session_id)
        
        # If setting as current, unset other current sessions
        if data.is_current:
            supabase.table('academic_sessions').update({'is_current': False}).eq(
                'organization_id', user["school_id"]
            ).neq('id', str(session_id)).execute()
        
        # Build update data
        # model_dump(mode="json") already serializes date fields to ISO strings
        update_data = {k: v for k, v in data.model_dump(mode="json", exclude_unset=True).items() if v is not None}
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()

            # Update session
            result = supabase.table('academic_sessions').update(update_data).eq(
                'id', str(session_id)
            ).execute()
            
            if not result.data:
                raise DatabaseError("Failed to update academic session")
            
            logger.info(f"Updated academic session: {session_id}")
            
            return result.data[0]
        
        return existing.data[0]
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating session: {e}")
        raise DatabaseError(f"Failed to update academic session: {str(e)}")


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    request: Request,
    session_id: UUID
):
    """
    Delete academic session.
    Only school admins can delete sessions.
    Note: This will cascade delete all related terms, enrollments, etc.
    """
    try:
        # Get current user
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        # Get Supabase client
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Check session exists
        existing = supabase.table('academic_sessions').select('*').eq('id', str(session_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Academic Session", session_id)
        
        # Delete session
        supabase.table('academic_sessions').delete().eq('id', str(session_id)).execute()
        
        logger.info(f"Deleted academic session: {session_id}")
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise DatabaseError(f"Failed to delete academic session: {str(e)}")


@router.post("/{session_id}/set-current", response_model=AcademicSessionResponse)
async def set_current_session(
    request: Request,
    session_id: UUID
):
    """
    Set an academic session as the current session.
    Only school admins can set current session.
    """
    try:
        # Get current user
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        # Get Supabase client
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Check session exists
        existing = supabase.table('academic_sessions').select('*').eq('id', str(session_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Academic Session", session_id)
        
        # Unset all current sessions for this org
        supabase.table('academic_sessions').update({'is_current': False}).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        # Set this session as current
        result = supabase.table('academic_sessions').update({
            'is_current': True,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', str(session_id)).execute()
        
        logger.info(f"Set academic session {session_id} as current")
        
        return result.data[0]
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error setting current session: {e}")
        raise DatabaseError(f"Failed to set current session: {str(e)}")
