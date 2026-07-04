"""
Organizations endpoints for Nigerian LMS.
School-level administration and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional
import logging

from app.core.database import get_supabase
from app.core.security import (
    get_token_from_request,
    get_current_user_from_token,
    is_system_admin,
    is_school_admin,
    can_access_school,
)
from app.core.exceptions import (
    AuthenticationError,
    InsufficientPermissionsError,
    DatabaseError,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# DEPENDENCY: Require Authentication
# ============================================

async def get_current_user(request: Request):
    """Dependency to get current authenticated user."""
    token = get_token_from_request(request)
    if not token:
        raise AuthenticationError("Not authenticated")
    
    user = get_current_user_from_token(token)
    if not user:
        raise AuthenticationError("Invalid or expired token")
    
    return user


# ============================================
# ORGANIZATION DETAILS
# ============================================

@router.get("/{org_id}")
async def get_organization_details(
    org_id: str,
    current_user = Depends(get_current_user),
):
    """
    Get organization details.
    Accessible by system admin or users from the organization.
    """
    try:
        # Check permissions
        if not is_system_admin(current_user) and not can_access_school(current_user, org_id):
            raise InsufficientPermissionsError("You don't have access to this organization")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get organization
        org_response = supabase.table('organizations').select('*').eq('id', org_id).execute()
        
        if not org_response.data:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        organization = org_response.data[0]
        
        # Get subscription plan details
        plan_id = organization.get('subscription_plan_id')
        plan = None
        if plan_id:
            plan_response = supabase.table('subscription_plans').select('*').eq('id', plan_id).execute()
            if plan_response.data:
                plan = plan_response.data[0]
        
        # Get user counts
        users_response = supabase.table('users').select('role').eq('school_id', org_id).execute()
        
        user_counts = {
            "admin": 0,
            "teacher": 0,
            "bursar": 0,
            "parent": 0,
            "total": len(users_response.data) if users_response.data else 0
        }
        
        if users_response.data:
            for user in users_response.data:
                role = user.get('role')
                if role in user_counts:
                    user_counts[role] += 1
        
        # Get campus count
        campus_response = supabase.table('campuses').select('id', count='exact').eq('organization_id', org_id).execute()
        campus_count = campus_response.count if hasattr(campus_response, 'count') else 0
        
        logger.info(f"User {current_user['email']} viewed organization {org_id}")
        
        return {
            "organization": organization,
            "subscription_plan": plan,
            "statistics": {
                "users": user_counts,
                "campuses": campus_count,
            }
        }
        
    except (HTTPException, InsufficientPermissionsError):
        raise
    except Exception as e:
        logger.error(f"Error getting organization: {e}")
        raise DatabaseError("Failed to get organization details")


# ============================================
# ORGANIZATION USERS
# ============================================

@router.get("/{org_id}/users")
async def list_organization_users(
    org_id: str,
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
):
    """
    List users in an organization.
    Accessible by system admin or school admin.
    """
    try:
        # Check permissions
        if not is_system_admin(current_user):
            if not can_access_school(current_user, org_id):
                raise InsufficientPermissionsError("You don't have access to this organization")
            if not is_school_admin(current_user):
                raise InsufficientPermissionsError("Only school admins can view user list")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Build query
        query = supabase.table('users').select(
            'id, email, full_name, role, phone, is_active, email_verified, created_at'
        ).eq('school_id', org_id)
        
        # Filter by role if provided
        if role:
            query = query.eq('role', role)
        
        # Apply pagination
        query = query.range(skip, skip + limit - 1)
        
        # Execute query
        response = query.execute()
        
        # Get total count
        count_query = supabase.table('users').select('id', count='exact').eq('school_id', org_id)
        if role:
            count_query = count_query.eq('role', role)
        count_response = count_query.execute()
        total = count_response.count if hasattr(count_response, 'count') else len(response.data)
        
        logger.info(f"User {current_user['email']} listed users for organization {org_id}")
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "users": response.data
        }
        
    except (InsufficientPermissionsError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Error listing organization users: {e}")
        raise DatabaseError("Failed to list organization users")


# ============================================
# ORGANIZATION CAMPUSES
# ============================================

@router.get("/{org_id}/campuses")
async def list_organization_campuses(
    org_id: str,
    current_user = Depends(get_current_user),
):
    """
    List campuses in an organization.
    Accessible by system admin or users from the organization.
    """
    try:
        # Check permissions
        if not is_system_admin(current_user) and not can_access_school(current_user, org_id):
            raise InsufficientPermissionsError("You don't have access to this organization")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get campuses
        response = supabase.table('campuses').select('*').eq('organization_id', org_id).execute()
        
        logger.info(f"User {current_user['email']} listed campuses for organization {org_id}")
        
        return {
            "total": len(response.data) if response.data else 0,
            "campuses": response.data
        }
        
    except (InsufficientPermissionsError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Error listing campuses: {e}")
        raise DatabaseError("Failed to list campuses")


# ============================================
# ORGANIZATION SETTINGS (Placeholder)
# ============================================

@router.get("/{org_id}/settings")
async def get_organization_settings(
    org_id: str,
    current_user = Depends(get_current_user),
):
    """
    Get organization settings (placeholder for Phase 2).
    """
    # Check permissions
    if not is_system_admin(current_user) and not can_access_school(current_user, org_id):
        raise InsufficientPermissionsError("You don't have access to this organization")
    
    # TODO: Implement in Phase 2
    return {
        "message": "Organization settings functionality coming in Phase 2",
        "organization_id": org_id
    }


@router.patch("/{org_id}/settings")
async def update_organization_settings(
    org_id: str,
    settings: dict,
    current_user = Depends(get_current_user),
):
    """
    Update organization settings (placeholder for Phase 2).
    """
    # Check permissions
    if not is_system_admin(current_user):
        if not can_access_school(current_user, org_id):
            raise InsufficientPermissionsError("You don't have access to this organization")
        if not is_school_admin(current_user):
            raise InsufficientPermissionsError("Only school admins can update settings")
    
    # TODO: Implement in Phase 2
    return {
        "message": "Organization settings update functionality coming in Phase 2",
        "organization_id": org_id
    }