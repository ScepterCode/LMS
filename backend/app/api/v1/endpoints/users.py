"""
User Management endpoints for Nigerian LMS.
Handles CRUD operations for user accounts.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from app.core.security import (
    get_password_hash,
    get_token_from_request,
    get_current_user_from_token,
    validate_password_strength,
)
from app.core.database import get_supabase
from app.core.exceptions import (
    AuthorizationError,
    ValidationError,
    DatabaseError,
    DuplicateRecordError,
    NotFoundError,
)
from app.core.audit import log_audit_event

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class UserCreate(BaseModel):
    """User creation model."""
    email: EmailStr
    password: str
    full_name: str
    role: str  # 'admin', 'teacher', 'bursar', 'parent', 'student'
    phone: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        valid_roles = ['admin', 'teacher', 'bursar', 'parent', 'student']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v


class UserUpdate(BaseModel):
    """User update model."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    full_name: str
    role: str
    school_id: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    email_verified: bool
    created_at: str
    updated_at: Optional[str] = None


# ============================================
# HELPER FUNCTIONS
# ============================================

def require_admin(user: dict):
    """Ensure user is school admin or system admin."""
    if not user:
        raise AuthorizationError("User authentication failed")
    if user.get("role") not in ["admin", "system_admin"]:
        raise AuthorizationError("Only administrators can manage users")


# ============================================
# USER MANAGEMENT ENDPOINTS
# ============================================

@router.get("", response_model=List[UserResponse])
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """
    List all users for the organization.
    Admins can see all users in their organization.
    System admins can see all users.
    """
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed")
        
        require_admin(user)
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Build query
        query = supabase.table('users').select('id, email, full_name, role, school_id, phone, is_active, email_verified, created_at, updated_at')
        
        # Filter by organization unless system admin
        if user.get("role") != "system_admin":
            if not user.get("school_id"):
                raise AuthorizationError("User must belong to a school")
            query = query.eq('school_id', user["school_id"])
        
        # Apply filters
        if role:
            query = query.eq('role', role)
        if is_active is not None:
            query = query.eq('is_active', is_active)
        
        # Apply pagination
        query = query.order('created_at', desc=True).range(skip, skip + limit - 1)
        
        response = query.execute()
        
        logger.info(f"User {user['email']} listed users (found {len(response.data)})")
        
        return response.data
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise DatabaseError(f"Failed to list users: {str(e)}")


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    data: UserCreate
):
    """
    Create a new user account.
    Only admins can create users.
    """
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed")
        
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Check if email already exists
        existing = supabase.table('users').select('id').eq('email', data.email).execute()
        if existing.data:
            raise DuplicateRecordError("User", "email", data.email)
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = get_password_hash(data.password)
        
        user_data = {
            'id': user_id,
            'email': data.email,
            'password_hash': password_hash,
            'full_name': data.full_name,
            'role': data.role,
            'school_id': str(user["school_id"]),
            'phone': data.phone,
            'is_active': True,
            'email_verified': False,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        
        if not result.data:
            raise DatabaseError("Failed to create user")
        
        logger.info(f"Created user: {data.email} (role: {data.role}) by {user['email']}")
        
        # Return user without password_hash
        created_user = result.data[0]
        created_user.pop('password_hash', None)
        
        return created_user
        
    except (AuthorizationError, ValidationError, DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise DatabaseError(f"Failed to create user: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    request: Request,
    user_id: str
):
    """
    Get user details by ID.
    Admins can view users in their organization.
    """
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get user
        query = supabase.table('users').select('id, email, full_name, role, school_id, phone, is_active, email_verified, created_at, updated_at').eq('id', user_id)
        
        # Filter by organization unless system admin
        if user.get("role") != "system_admin":
            if not user.get("school_id"):
                raise AuthorizationError("User must belong to a school")
            query = query.eq('school_id', user["school_id"])
        
        response = query.execute()
        
        if not response.data:
            raise NotFoundError("User", user_id)
        
        return response.data[0]
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise DatabaseError(f"Failed to get user: {str(e)}")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: str,
    data: UserUpdate
):
    """
    Update user details.
    Only admins can update users.
    """
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed")
        
        require_admin(user)
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Check user exists and belongs to organization
        existing_query = supabase.table('users').select('*').eq('id', user_id)
        
        if user.get("role") != "system_admin":
            if not user.get("school_id"):
                raise AuthorizationError("User must belong to a school")
            existing_query = existing_query.eq('school_id', user["school_id"])
        
        existing = existing_query.execute()
        
        if not existing.data:
            raise NotFoundError("User", user_id)
        
        # Build update data
        update_data = {k: v for k, v in data.model_dump(mode="json", exclude_unset=True).items() if v is not None}
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = supabase.table('users').update(update_data).eq('id', user_id).execute()
            
            if not result.data:
                raise DatabaseError("Failed to update user")
            
            logger.info(f"Updated user {user_id} by {user['email']}")

            if user.get("role") == "system_admin":
                log_audit_event(
                    supabase, user, "user.updated",
                    target_type="user", target_id=user_id,
                    target_organization_id=existing.data[0].get("school_id"),
                    details=update_data,
                )

            # Return without password_hash
            updated_user = result.data[0]
            updated_user.pop('password_hash', None)

            return updated_user
        
        # No changes, return existing
        existing.data[0].pop('password_hash', None)
        return existing.data[0]
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise DatabaseError(f"Failed to update user: {str(e)}")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    request: Request,
    user_id: str
):
    """
    Delete (deactivate) a user.
    Only admins can delete users.
    Note: This sets is_active=false rather than actually deleting the record.
    """
    try:
        token = get_token_from_request(request)
        if not token:
            raise AuthorizationError("Authentication token required")
        
        user = get_current_user_from_token(token)
        if not user:
            raise AuthorizationError("User authentication failed")
        
        require_admin(user)
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Check user exists and belongs to organization
        existing_query = supabase.table('users').select('*').eq('id', user_id)
        
        if user.get("role") != "system_admin":
            if not user.get("school_id"):
                raise AuthorizationError("User must belong to a school")
            existing_query = existing_query.eq('school_id', user["school_id"])
        
        existing = existing_query.execute()
        
        if not existing.data:
            raise NotFoundError("User", user_id)
        
        # Soft delete - set is_active to false
        supabase.table('users').update({
            'is_active': False,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', user_id).execute()
        
        logger.info(f"Deactivated user {user_id} by {user['email']}")

        if user.get("role") == "system_admin":
            log_audit_event(
                supabase, user, "user.deactivated",
                target_type="user", target_id=user_id,
                target_organization_id=existing.data[0].get("school_id"),
            )

    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise DatabaseError(f"Failed to delete user: {str(e)}")
