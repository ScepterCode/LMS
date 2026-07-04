"""
Authentication endpoints for Nigerian LMS.
Handles login, logout, registration, and user profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, timedelta
import uuid
import logging

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    set_auth_cookie,
    clear_auth_cookie,
    get_token_from_request,
    get_current_user_from_token,
    blacklist_token,
    validate_password_strength,
    create_user_token_data,
)
from app.core.database import get_supabase
from app.core.exceptions import (
    AuthenticationError,
    ValidationError,
    DatabaseError,
    DuplicateRecordError,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    user: dict


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


class SchoolRegistrationRequest(BaseModel):
    """School registration request model."""
    # School details
    school_name: str
    school_email: EmailStr
    school_phone: Optional[str] = None
    school_address: Optional[str] = None
    
    # Admin details
    admin_name: str
    admin_email: EmailStr
    admin_password: str
    admin_phone: Optional[str] = None
    
    # Subscription
    subscription_plan_id: str = "trial"
    
    @field_validator('admin_password')
    @classmethod
    def validate_password(cls, v):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v
    
    @field_validator('school_name')
    @classmethod
    def validate_school_name(cls, v):
        if len(v) < 3:
            raise ValueError('School name must be at least 3 characters')
        return v


class SchoolRegistrationResponse(BaseModel):
    """School registration response model."""
    message: str
    organization_id: str
    admin_id: str
    login_email: str


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@router.post("/login", response_model=TokenResponse)
async def login(response: Response, data: LoginRequest):
    """
    Login endpoint for all user types.
    Checks both users and system_admins tables.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        user = None
        user_type = "user"
        
        # Try system_admins table first
        try:
            admin_response = supabase.table('system_admins').select('*').eq('email', data.email).execute()
            if admin_response.data and len(admin_response.data) > 0:
                user = admin_response.data[0]
                user_type = "system_admin"
                logger.info(f"Found system admin: {data.email}")
        except Exception as e:
            logger.debug(f"Not a system admin: {e}")
        
        # Try users table if not system admin
        if not user:
            try:
                users_response = supabase.table('users').select('*').eq('email', data.email).execute()
                if users_response.data and len(users_response.data) > 0:
                    user = users_response.data[0]
                    user_type = "user"
            except Exception as e:
                logger.error(f"Error querying users table: {e}")
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {data.email}")
            raise AuthenticationError("Invalid email or password")
        
        # Verify password
        if not verify_password(data.password, user["password_hash"]):
            logger.warning(f"Failed login attempt for user: {data.email}")
            raise AuthenticationError("Invalid email or password")
        
        # Check if user is active
        if not user.get("is_active", True):
            raise AuthenticationError("Account is inactive")
        
        # Determine role
        role = user.get("role", "admin")
        school_id = user.get("school_id")
        
        # Create access token
        token_data = {
            "sub": str(user["id"]),
            "email": user["email"],
            "role": role,
            "school_id": str(school_id) if school_id else None,
            "user_type": user_type,
        }
        
        access_token = create_access_token(data=token_data)
        
        logger.info(f"Successful login for {user_type}: {data.email}")
        
        # Prepare safe user data
        safe_user = {
            "id": str(user["id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "role": role,
            "school_id": str(school_id) if school_id else None,
            "phone": user.get("phone"),
            "is_active": user.get("is_active", True),
            "email_verified": user.get("email_verified", False),
            "user_type": user_type,
        }
        
        # Set HttpOnly cookie
        set_auth_cookie(response, access_token)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": safe_user
        }
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Login error for {data.email}: {str(e)}")
        raise DatabaseError("Login failed due to server error")


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response):
    """
    Logout endpoint - blacklists the token and clears the cookie.
    """
    try:
        # Get token from request
        token = get_token_from_request(request)
        
        # Blacklist the token if it exists
        if token:
            blacklist_token(token)
        
        # Clear the cookie
        clear_auth_cookie(response)
        
        logger.info("User logged out successfully")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Still clear the cookie even if there's an error
        clear_auth_cookie(response)
        return {"message": "Logged out"}


@router.get("/me", response_model=dict)
async def get_current_user_profile(request: Request):
    """
    Get current user profile from token.
    """
    try:
        # Get token from request
        token = get_token_from_request(request)
        if not token:
            raise AuthenticationError("Not authenticated")
        
        # Get user from token
        user = get_current_user_from_token(token)
        if not user:
            raise AuthenticationError("Invalid or expired token")
        
        # Fetch full user details from database
        supabase = get_supabase()
        if not supabase:
            # Return token data if database not available
            return user
        
        try:
            user_response = supabase.table('users').select('*').eq('id', user["id"]).execute()
            if user_response.data and len(user_response.data) > 0:
                db_user = user_response.data[0]
                
                # Return safe user data
                return {
                    "id": str(db_user["id"]),
                    "email": db_user["email"],
                    "full_name": db_user["full_name"],
                    "role": db_user["role"],
                    "school_id": str(db_user["school_id"]) if db_user.get("school_id") else None,
                    "phone": db_user.get("phone"),
                    "is_active": db_user.get("is_active", True),
                    "email_verified": db_user.get("email_verified", False),
                    "created_at": db_user.get("created_at"),
                }
        except Exception as e:
            logger.error(f"Error fetching user details: {e}")
            # Return token data as fallback
            return user
        
        return user
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        raise AuthenticationError("Failed to get user profile")


# ============================================
# SCHOOL REGISTRATION
# ============================================

@router.post("/register-school", response_model=SchoolRegistrationResponse)
async def register_school(data: SchoolRegistrationRequest):
    """
    Public endpoint for school registration.
    Creates organization, admin user, and sets up trial subscription.
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Step 1: Check if organization email already exists
        try:
            existing_org = supabase.table('organizations').select('id').eq('email', data.school_email).execute()
            if existing_org.data:
                raise DuplicateRecordError("Organization", "email", data.school_email)
        except DuplicateRecordError:
            raise
        except Exception as e:
            logger.error(f"Error checking organization: {e}")
        
        # Step 2: Check if admin email already exists
        try:
            existing_user = supabase.table('users').select('id').eq('email', data.admin_email).execute()
            if existing_user.data:
                raise DuplicateRecordError("User", "email", data.admin_email)
        except DuplicateRecordError:
            raise
        except Exception as e:
            logger.error(f"Error checking user: {e}")
        
        # Step 3: Create organization
        org_id = str(uuid.uuid4())
        org_slug = data.school_name.lower().replace(' ', '-').replace("'", '')[:50]
        
        # Add timestamp to slug if needed to ensure uniqueness
        try:
            existing_slug = supabase.table('organizations').select('id').eq('slug', org_slug).execute()
            if existing_slug.data:
                org_slug = f"{org_slug}-{uuid.uuid4().hex[:6]}"
        except Exception:
            pass
        
        org_data = {
            'id': org_id,
            'name': data.school_name,
            'slug': org_slug,
            'email': data.school_email,
            'phone': data.school_phone,
            'address': data.school_address,
            'subscription_plan_id': data.subscription_plan_id,
            'subscription_status': 'trial',
            'trial_ends_at': (datetime.utcnow() + timedelta(days=14)).isoformat(),
            'is_active': True,
            'is_test_account': False,
            'created_at': datetime.utcnow().isoformat()
        }
        
        org_result = supabase.table('organizations').insert(org_data).execute()
        if not org_result.data:
            raise DatabaseError("Failed to create organization")
        
        logger.info(f"Created organization: {data.school_name} ({org_id})")
        
        # Step 4: Create admin user
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
            # Rollback: delete organization
            try:
                supabase.table('organizations').delete().eq('id', org_id).execute()
            except Exception:
                pass
            raise DatabaseError("Failed to create admin user")
        
        logger.info(f"Created admin user: {data.admin_email} for organization {org_id}")
        
        # Step 5: Create default campus
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
        
        return {
            "message": "School registered successfully! You can now login with your admin credentials.",
            "organization_id": org_id,
            "admin_id": admin_id,
            "login_email": data.admin_email
        }
        
    except (ValidationError, DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"School registration error: {str(e)}")
        raise DatabaseError(f"Registration failed: {str(e)}")


# ============================================
# PASSWORD RESET (Placeholder for Phase 2)
# ============================================

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(email: EmailStr):
    """
    Request password reset (placeholder for Phase 2).
    """
    # TODO: Implement in Phase 2
    return {"message": "Password reset functionality coming in Phase 2"}


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(token: str, new_password: str):
    """
    Reset password with token (placeholder for Phase 2).
    """
    # TODO: Implement in Phase 2
    return {"message": "Password reset functionality coming in Phase 2"}