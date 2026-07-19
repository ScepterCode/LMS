"""
Organizations endpoints for Learnlyf.
School-level administration and management.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from pydantic import BaseModel
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
    ValidationError,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# DEPENDENCY: Require Authentication
# ============================================

def get_current_user(request: Request):
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
def get_organization_details(
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
def list_organization_users(
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
def list_organization_campuses(
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
# ORGANIZATION BRANDING (name, address, motto, logo)
# ============================================

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    motto: Optional[str] = None


LOGO_BUCKET = "school-assets"
ALLOWED_LOGO_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_LOGO_SIZE_BYTES = 2 * 1024 * 1024  # 2MB


def _require_school_admin(current_user: dict, org_id: str):
    if not is_system_admin(current_user):
        if not can_access_school(current_user, org_id):
            raise InsufficientPermissionsError("You don't have access to this organization")
        if not is_school_admin(current_user):
            raise InsufficientPermissionsError("Only school admins can update organization settings")


@router.patch("/{org_id}")
def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    current_user = Depends(get_current_user),
):
    """Update organization name/address/phone/motto. School admin only."""
    _require_school_admin(current_user, org_id)

    supabase = get_supabase()
    if not supabase:
        raise DatabaseError("Database connection not available")

    update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not update_data:
        existing = supabase.table('organizations').select('*').eq('id', org_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Organization not found")
        return existing.data[0]

    result = supabase.table('organizations').update(update_data).eq('id', org_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Organization not found")

    logger.info(f"User {current_user['email']} updated organization {org_id} settings")
    return result.data[0]


@router.post("/{org_id}/logo")
def upload_organization_logo(
    org_id: str,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
):
    """Upload/replace the organization's logo. School admin only."""
    _require_school_admin(current_user, org_id)

    if file.content_type not in ALLOWED_LOGO_TYPES:
        raise ValidationError("Logo must be a PNG, JPEG, or WebP image")

    contents = file.file.read()
    if len(contents) > MAX_LOGO_SIZE_BYTES:
        raise ValidationError("Logo must be smaller than 2MB")

    supabase = get_supabase()
    if not supabase:
        raise DatabaseError("Database connection not available")

    extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[file.content_type]
    path = f"{org_id}/logo.{extension}"

    try:
        storage = supabase.storage.from_(LOGO_BUCKET)
        try:
            storage.upload(
                path, contents,
                file_options={"content-type": file.content_type, "upsert": "true"}
            )
        except Exception:
            # Bucket likely doesn't exist yet - create it (public, so logos can be
            # rendered directly in <img> tags and printed report cards) and retry once.
            supabase.storage.create_bucket(LOGO_BUCKET, options={"public": True})
            storage.upload(
                path, contents,
                file_options={"content-type": file.content_type, "upsert": "true"}
            )

        # get_public_url() in this supabase-py version already returns a
        # trailing "?" - strip it before appending our own cache-busting param.
        public_url = storage.get_public_url(path).rstrip("?")
        public_url = f"{public_url}?v={uuid.uuid4().hex[:8]}"
    except Exception as e:
        logger.error(f"Error uploading organization logo: {e}")
        raise DatabaseError(f"Failed to upload logo: {str(e)}")

    result = supabase.table('organizations').update(
        {"logo_url": public_url}
    ).eq('id', org_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Organization not found")

    logger.info(f"User {current_user['email']} uploaded a new logo for organization {org_id}")
    return {"logo_url": public_url}