"""
System Admin endpoints for Nigerian LMS.
Platform-level administration and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional
import logging

from app.core.database import get_supabase
from app.core.security import get_token_from_request, get_current_user_from_token, is_system_admin
from app.core.exceptions import AuthenticationError, InsufficientPermissionsError, DatabaseError

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# DEPENDENCY: Require System Admin
# ============================================

async def require_system_admin(request: Request):
    """Dependency to require system admin authentication."""
    token = get_token_from_request(request)
    if not token:
        raise AuthenticationError("Not authenticated")
    
    user = get_current_user_from_token(token)
    if not user:
        raise AuthenticationError("Invalid or expired token")
    
    if not is_system_admin(user):
        raise InsufficientPermissionsError("System admin access required")
    
    return user


# ============================================
# ORGANIZATIONS MANAGEMENT
# ============================================

@router.get("/organizations")
async def list_organizations(
    current_user = Depends(require_system_admin),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
):
    """
    List all organizations (schools).
    System admin only.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Build query
        query = supabase.table('organizations').select('*')
        
        # Filter by status if provided
        if status:
            query = query.eq('subscription_status', status)
        
        # Apply pagination
        query = query.range(skip, skip + limit - 1)
        
        # Execute query
        response = query.execute()
        
        # Get total count
        count_response = supabase.table('organizations').select('id', count='exact').execute()
        total = count_response.count if hasattr(count_response, 'count') else len(response.data)
        
        logger.info(f"System admin {current_user['email']} listed organizations")
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "organizations": response.data
        }
        
    except Exception as e:
        logger.error(f"Error listing organizations: {e}")
        raise DatabaseError("Failed to list organizations")


@router.get("/organizations/{org_id}")
async def get_organization(
    org_id: str,
    current_user = Depends(require_system_admin),
):
    """
    Get organization details.
    System admin only.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get organization
        org_response = supabase.table('organizations').select('*').eq('id', org_id).execute()
        
        if not org_response.data:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        organization = org_response.data[0]
        
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
        
        logger.info(f"System admin {current_user['email']} viewed organization {org_id}")
        
        return {
            "organization": organization,
            "statistics": {
                "users": user_counts,
                "campuses": campus_count,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization: {e}")
        raise DatabaseError("Failed to get organization details")


@router.patch("/organizations/{org_id}/status")
async def update_organization_status(
    org_id: str,
    new_status: str,
    current_user = Depends(require_system_admin),
):
    """
    Update organization subscription status.
    System admin only.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Validate status
        valid_statuses = ['trial', 'active', 'suspended', 'cancelled']
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Update organization
        update_response = supabase.table('organizations').update({
            'subscription_status': new_status
        }).eq('id', org_id).execute()
        
        if not update_response.data:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        logger.info(f"System admin {current_user['email']} updated organization {org_id} status to {new_status}")
        
        return {
            "message": f"Organization status updated to {new_status}",
            "organization": update_response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization status: {e}")
        raise DatabaseError("Failed to update organization status")


# ============================================
# PLATFORM ANALYTICS
# ============================================

@router.get("/analytics")
async def get_platform_analytics(
    current_user = Depends(require_system_admin),
):
    """
    Get platform-wide analytics.
    System admin only.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Get organization counts by status
        orgs_response = supabase.table('organizations').select('subscription_status').execute()
        
        org_stats = {
            "total": len(orgs_response.data) if orgs_response.data else 0,
            "trial": 0,
            "active": 0,
            "suspended": 0,
            "cancelled": 0,
        }
        
        if orgs_response.data:
            for org in orgs_response.data:
                status = org.get('subscription_status', 'trial')
                if status in org_stats:
                    org_stats[status] += 1
        
        # Get user counts by role
        users_response = supabase.table('users').select('role').execute()
        
        user_stats = {
            "total": len(users_response.data) if users_response.data else 0,
            "system_admin": 0,
            "admin": 0,
            "teacher": 0,
            "bursar": 0,
            "parent": 0,
        }
        
        if users_response.data:
            for user in users_response.data:
                role = user.get('role')
                if role in user_stats:
                    user_stats[role] += 1
        
        # Get subscription plan distribution
        plans_response = supabase.table('organizations').select('subscription_plan_id').execute()
        
        plan_stats = {}
        if plans_response.data:
            for org in plans_response.data:
                plan_id = org.get('subscription_plan_id', 'trial')
                plan_stats[plan_id] = plan_stats.get(plan_id, 0) + 1
        
        logger.info(f"System admin {current_user['email']} viewed platform analytics")
        
        return {
            "organizations": org_stats,
            "users": user_stats,
            "subscription_plans": plan_stats,
            "summary": {
                "total_organizations": org_stats["total"],
                "total_users": user_stats["total"],
                "active_organizations": org_stats["active"],
                "trial_organizations": org_stats["trial"],
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise DatabaseError("Failed to get platform analytics")


# ============================================
# SUBSCRIPTION PLANS
# ============================================

@router.get("/subscription-plans")
async def list_subscription_plans(
    current_user = Depends(require_system_admin),
):
    """
    List all subscription plans.
    System admin only.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        response = supabase.table('subscription_plans').select('*').execute()
        
        logger.info(f"System admin {current_user['email']} listed subscription plans")
        
        return {
            "plans": response.data
        }
        
    except Exception as e:
        logger.error(f"Error listing subscription plans: {e}")
        raise DatabaseError("Failed to list subscription plans")


# ============================================
# USER MANAGEMENT
# ============================================

@router.get("/users")
async def list_all_users(
    current_user = Depends(require_system_admin),
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
):
    """
    List all users across all organizations.
    System admin only.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Build query
        query = supabase.table('users').select('id, email, full_name, role, school_id, is_active, created_at')
        
        # Filter by role if provided
        if role:
            query = query.eq('role', role)
        
        # Apply pagination
        query = query.range(skip, skip + limit - 1)
        
        # Execute query
        response = query.execute()
        
        # Get total count
        count_query = supabase.table('users').select('id', count='exact')
        if role:
            count_query = count_query.eq('role', role)
        count_response = count_query.execute()
        total = count_response.count if hasattr(count_response, 'count') else len(response.data)
        
        logger.info(f"System admin {current_user['email']} listed users")
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "users": response.data
        }
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise DatabaseError("Failed to list users")


# ============================================
# AUDIT LOGS (Placeholder for Phase 2)
# ============================================

@router.get("/audit-logs")
async def get_audit_logs(
    current_user = Depends(require_system_admin),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get platform audit logs (placeholder for Phase 2).
    System admin only.
    """
    # TODO: Implement in Phase 2
    return {
        "message": "Audit logs functionality coming in Phase 2",
        "total": 0,
        "logs": []
    }