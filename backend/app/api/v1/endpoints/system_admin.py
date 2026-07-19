"""
System Admin endpoints for Learnlyf.
Platform-level administration and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import logging

from app.core.database import get_supabase
from app.core.security import (
    get_token_from_request,
    get_current_user_from_token,
    is_system_admin,
    get_password_hash,
    validate_password_strength,
    create_access_token,
    create_user_token_data,
    set_auth_cookie,
    clear_auth_cookie,
    set_impersonator_cookie,
    clear_impersonator_cookie,
    get_impersonator_token_from_request,
)
from app.core.exceptions import AuthenticationError, InsufficientPermissionsError, DatabaseError, DuplicateRecordError
from app.core.audit import log_audit_event
from app.api.v1.endpoints.skills import seed_default_skill_categories

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# DEPENDENCY: Require System Admin
# ============================================

def require_system_admin(request: Request):
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
def list_organizations(
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
def get_organization(
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
def update_organization_status(
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

        log_audit_event(
            supabase, current_user, "organization.status_changed",
            target_type="organization", target_id=org_id, target_organization_id=org_id,
            details={"new_status": new_status},
        )

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
# ASSISTED SCHOOL ONBOARDING
# ============================================
# Deliberately duplicates register_school's insert sequence
# (app/api/v1/endpoints/auth.py) rather than sharing code with it, so the
# live public signup path can never be affected by changes made here.

class SystemAdminOrganizationCreate(BaseModel):
    """Request model for system-admin-assisted school onboarding."""
    school_name: str
    school_email: EmailStr
    school_phone: Optional[str] = None
    school_address: Optional[str] = None

    admin_name: str
    admin_email: EmailStr
    admin_password: str
    admin_phone: Optional[str] = None

    subscription_plan_id: str = "trial"
    subscription_status: str = "trial"

    @field_validator('admin_password')
    @classmethod
    def validate_password(cls, v):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v

    @field_validator('subscription_status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['trial', 'active', 'suspended', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


@router.post("/organizations", status_code=status.HTTP_201_CREATED)
def create_organization_by_system_admin(
    data: SystemAdminOrganizationCreate,
    current_user = Depends(require_system_admin),
):
    """
    Assisted school onboarding: a system admin creates a school and its
    admin account directly, optionally skipping the default trial.
    System admin only.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        existing_org = supabase.table('organizations').select('id').eq('email', data.school_email).execute()
        if existing_org.data:
            raise DuplicateRecordError("Organization", "email", data.school_email)

        existing_user = supabase.table('users').select('id').eq('email', data.admin_email).execute()
        if existing_user.data:
            raise DuplicateRecordError("User", "email", data.admin_email)

        org_id = str(uuid.uuid4())
        org_slug = data.school_name.lower().replace(' ', '-').replace("'", '')[:50]

        existing_slug = supabase.table('organizations').select('id').eq('slug', org_slug).execute()
        if existing_slug.data:
            org_slug = f"{org_slug}-{uuid.uuid4().hex[:6]}"

        org_data = {
            'id': org_id,
            'name': data.school_name,
            'slug': org_slug,
            'email': data.school_email,
            'phone': data.school_phone,
            'address': data.school_address,
            'subscription_plan_id': data.subscription_plan_id,
            'subscription_status': data.subscription_status,
            'trial_ends_at': (datetime.utcnow() + timedelta(days=14)).isoformat(),
            'is_active': True,
            'is_test_account': False,
            'created_at': datetime.utcnow().isoformat()
        }

        org_result = supabase.table('organizations').insert(org_data).execute()
        if not org_result.data:
            raise DatabaseError("Failed to create organization")

        logger.info(f"System admin {current_user['email']} created organization: {data.school_name} ({org_id})")

        admin_id = str(uuid.uuid4())
        password_hash = get_password_hash(data.admin_password)

        user_data = {
            'id': admin_id,
            'email': data.admin_email,
            'password_hash': password_hash,
            'full_name': data.admin_name,
            'role': 'admin',
            'school_id': org_id,
            'phone': data.admin_phone,
            'is_active': True,
            'email_verified': False,
            'created_at': datetime.utcnow().isoformat()
        }

        user_result = supabase.table('users').insert(user_data).execute()
        if not user_result.data:
            try:
                supabase.table('organizations').delete().eq('id', org_id).execute()
            except Exception:
                pass
            raise DatabaseError("Failed to create admin user")

        logger.info(f"Created admin user: {data.admin_email} for organization {org_id}")

        campus_id = str(uuid.uuid4())
        campus_data = {
            'id': campus_id,
            'organization_id': org_id,
            'name': f"{data.school_name} Main Campus",
            'campus_name': "Main Campus",
            'address': data.school_address,
            'phone': data.school_phone,
            'email': data.school_email,
            'is_main_campus': True,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat()
        }

        try:
            campus_result = supabase.table('campuses').insert(campus_data).execute()
            if campus_result.data:
                logger.info(f"Created default campus for organization {org_id}")
        except Exception as e:
            logger.warning(f"Failed to create campus (non-critical): {e}")

        seed_default_skill_categories(supabase, org_id)

        log_audit_event(
            supabase, current_user, "organization.created",
            target_type="organization", target_id=org_id, target_organization_id=org_id,
            details={"school_name": data.school_name, "subscription_plan_id": data.subscription_plan_id, "subscription_status": data.subscription_status},
        )

        return {
            "message": "School created successfully.",
            "organization_id": org_id,
            "admin_id": admin_id,
            "login_email": data.admin_email
        }

    except (DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"System admin school creation error: {str(e)}")
        raise DatabaseError(f"School creation failed: {str(e)}")


# ============================================
# PLATFORM ANALYTICS
# ============================================

@router.get("/analytics")
def get_platform_analytics(
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

class SubscriptionPlanCreate(BaseModel):
    """Subscription plan creation model."""
    id: str
    name: str
    description: Optional[str] = None
    price_monthly: float
    price_yearly: float
    max_students: int
    features: List[str] = []
    is_active: bool = True

    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        import re
        if not re.match(r'^[a-z0-9_-]{2,50}$', v):
            raise ValueError('Plan id must be lowercase letters, numbers, hyphens, or underscores (2-50 chars)')
        return v


class SubscriptionPlanUpdate(BaseModel):
    """Subscription plan update model."""
    name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    max_students: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None


@router.get("/subscription-plans")
def list_subscription_plans(
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


@router.post("/subscription-plans", status_code=status.HTTP_201_CREATED)
def create_subscription_plan(
    data: SubscriptionPlanCreate,
    current_user = Depends(require_system_admin),
):
    """
    Create a new subscription plan.
    System admin only.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        existing = supabase.table('subscription_plans').select('id').eq('id', data.id).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail=f"A plan with id '{data.id}' already exists")

        result = supabase.table('subscription_plans').insert(data.model_dump()).execute()

        if not result.data:
            raise DatabaseError("Failed to create subscription plan")

        logger.info(f"System admin {current_user['email']} created subscription plan {data.id}")

        log_audit_event(
            supabase, current_user, "subscription_plan.created",
            target_type="subscription_plan", target_id=data.id,
            details=data.model_dump(),
        )

        return {"plan": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription plan: {e}")
        raise DatabaseError("Failed to create subscription plan")


@router.put("/subscription-plans/{plan_id}")
def update_subscription_plan(
    plan_id: str,
    data: SubscriptionPlanUpdate,
    current_user = Depends(require_system_admin),
):
    """
    Update an existing subscription plan.
    System admin only.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}

        if not update_data:
            existing = supabase.table('subscription_plans').select('*').eq('id', plan_id).execute()
            if not existing.data:
                raise HTTPException(status_code=404, detail="Subscription plan not found")
            return {"plan": existing.data[0]}

        result = supabase.table('subscription_plans').update(update_data).eq('id', plan_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Subscription plan not found")

        logger.info(f"System admin {current_user['email']} updated subscription plan {plan_id}")

        log_audit_event(
            supabase, current_user, "subscription_plan.updated",
            target_type="subscription_plan", target_id=plan_id,
            details=update_data,
        )

        return {"plan": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription plan: {e}")
        raise DatabaseError("Failed to update subscription plan")


# ============================================
# USER MANAGEMENT
# ============================================

@router.get("/users")
def list_all_users(
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
# SUPPORT IMPERSONATION
# ============================================
# Starting impersonation mints a normal token for the target user and sets
# it as the main auth cookie, so every existing permission check elsewhere
# in the app keeps working completely unmodified - the app has no idea an
# admin is impersonating. The admin's own token is stashed in a second
# cookie (impersonator_token) rather than discarded, so exiting restores it.

@router.post("/impersonate/exit")
def exit_impersonation(request: Request, response: Response):
    """
    End impersonation and restore the system admin's own session.
    Deliberately not gated behind require_system_admin - while impersonating,
    the active session cookie belongs to the impersonated (non-admin) user,
    so this instead validates the stashed impersonator cookie directly.

    Must stay declared before /impersonate/{user_id} below: FastAPI matches
    path routes in registration order, and a literal "/impersonate/exit"
    would otherwise be swallowed by the "{user_id}" pattern (with
    user_id="exit"), silently routing exit requests into start_impersonation
    and 403'ing them under require_system_admin instead.
    """
    try:
        impersonator_token = get_impersonator_token_from_request(request)
        if not impersonator_token:
            raise HTTPException(status_code=400, detail="Not currently impersonating")

        admin_user = get_current_user_from_token(impersonator_token)
        if not admin_user or not is_system_admin(admin_user):
            clear_auth_cookie(response)
            clear_impersonator_cookie(response)
            raise AuthenticationError("Impersonator session invalid, please log in again")

        set_auth_cookie(response, impersonator_token)
        clear_impersonator_cookie(response)

        logger.info(f"System admin {admin_user['email']} exited impersonation")

        supabase = get_supabase()
        if supabase:
            log_audit_event(supabase, admin_user, "user.impersonation_ended")

        return {"message": "Returned to your own account", "user": admin_user}

    except HTTPException:
        raise
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Error exiting impersonation: {e}")
        raise DatabaseError("Failed to exit impersonation")


@router.post("/impersonate/{user_id}")
def start_impersonation(
    user_id: str,
    request: Request,
    response: Response,
    current_user = Depends(require_system_admin),
):
    """
    Begin impersonating another user for support purposes.
    System admin only. Cannot impersonate another system admin.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        target_response = supabase.table('users').select('*').eq('id', user_id).execute()
        if not target_response.data:
            raise HTTPException(status_code=404, detail="User not found")

        target = target_response.data[0]

        if target.get('role') == 'system_admin':
            raise HTTPException(status_code=400, detail="Cannot impersonate another system admin")
        if not target.get('is_active', True):
            raise HTTPException(status_code=400, detail="Cannot impersonate a deactivated user")

        admin_token = get_token_from_request(request)
        if not admin_token:
            raise AuthenticationError("Not authenticated")

        target_token = create_access_token(create_user_token_data(target))

        set_auth_cookie(response, target_token)
        set_impersonator_cookie(response, admin_token)

        logger.info(f"System admin {current_user['email']} started impersonating {target.get('email')}")

        log_audit_event(
            supabase, current_user, "user.impersonation_started",
            target_type="user", target_id=user_id, target_organization_id=target.get('school_id'),
            details={"target_email": target.get('email'), "target_role": target.get('role')},
        )

        target.pop('password_hash', None)
        return {"message": f"Now impersonating {target.get('email')}", "user": target}

    except HTTPException:
        raise
    except (AuthenticationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error starting impersonation: {e}")
        raise DatabaseError("Failed to start impersonation")


# ============================================
# AUDIT LOGS
# ============================================

@router.get("/audit-logs")
def get_audit_logs(
    current_user = Depends(require_system_admin),
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[str] = None,
    action: Optional[str] = None,
):
    """
    Get platform audit logs, most recent first.
    System admin only.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        query = supabase.table('audit_logs').select('*')
        count_query = supabase.table('audit_logs').select('id', count='exact')

        if organization_id:
            query = query.eq('target_organization_id', organization_id)
            count_query = count_query.eq('target_organization_id', organization_id)
        if action:
            query = query.eq('action', action)
            count_query = count_query.eq('action', action)

        query = query.order('created_at', desc=True).range(skip, skip + limit - 1)

        response = query.execute()
        count_response = count_query.execute()
        total = count_response.count if hasattr(count_response, 'count') else len(response.data)

        logger.info(f"System admin {current_user['email']} viewed audit logs")

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "logs": response.data
        }

    except Exception as e:
        logger.error(f"Error listing audit logs: {e}")
        raise DatabaseError("Failed to list audit logs")