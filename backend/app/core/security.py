"""
Security utilities for authentication and authorization.
Includes JWT token handling, password hashing, and cookie management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Request, Response
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token blacklist (in-memory for now, use Redis in production)
token_blacklist = set()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        # Check if token is blacklisted
        if token in token_blacklist:
            logger.warning("Attempt to use blacklisted token")
            return None
        
        # Decode the token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Check expiration
        exp_time = datetime.fromtimestamp(payload["exp"])
        current_time = datetime.utcnow()
        if current_time > exp_time:
            logger.warning(f"Token has expired. Current: {current_time}, Expiration: {exp_time}")
            return None
        
        logger.debug(f"Token decoded successfully. Sub: {payload.get('sub')}, Exp: {exp_time}")
        return payload
        
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        return None


def blacklist_token(token: str) -> None:
    """Add a token to the blacklist."""
    token_blacklist.add(token)
    logger.info(f"Token blacklisted: {token[:20]}...")


def clear_expired_tokens() -> None:
    """Clear expired tokens from blacklist (call periodically)."""
    # In production, use Redis with TTL instead
    # For now, we'll keep it simple
    global token_blacklist
    current_size = len(token_blacklist)
    
    # Simple cleanup: if blacklist gets too large, clear it
    if current_size > 1000:
        token_blacklist.clear()
        logger.info("Cleared token blacklist")


def set_auth_cookie(response: Response, token: str) -> None:
    """Set authentication cookie in response."""
    # In development, use more permissive settings for localhost/127.0.0.1 cross-origin
    if settings.is_production:
        response.set_cookie(
            key=settings.COOKIE_NAME,
            value=token,
            httponly=True,
            secure=True,
            samesite="none",  # Required for cross-origin in production with secure=True
            max_age=settings.COOKIE_MAX_AGE,
            path="/"
        )
    else:
        # Development: Use lax samesite (browsers reject none without secure=True)
        response.set_cookie(
            key=settings.COOKIE_NAME,
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",  # Fixed: lax works with secure=False in development
            max_age=settings.COOKIE_MAX_AGE,
            path="/"
        )
    logger.debug("Auth cookie set")


def clear_auth_cookie(response: Response) -> None:
    """Clear authentication cookie."""
    if settings.is_production:
        response.delete_cookie(
            key=settings.COOKIE_NAME,
            path="/",
            httponly=True,
            secure=True,
            samesite="none"
        )
    else:
        response.delete_cookie(
            key=settings.COOKIE_NAME,
            path="/",
            httponly=True,
            secure=False,
            samesite="lax"  # Fixed: match the set_cookie samesite value
        )
    logger.debug("Auth cookie cleared")


def get_token_from_request(request: Request) -> Optional[str]:
    """Extract token from request (cookie or Authorization header)."""
    # Try cookie first
    token = request.cookies.get(settings.COOKIE_NAME)
    
    # If no cookie, try Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    return token


def get_current_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token."""
    payload = decode_access_token(token)
    if not payload:
        return None
    
    # Extract user information from token
    user_data = {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role"),
        "school_id": payload.get("school_id"),
        "user_type": payload.get("user_type", "user"),
        "teacher_id": payload.get("teacher_id"),
    }
    
    # Validate required fields
    if not all([user_data["id"], user_data["email"], user_data["role"]]):
        logger.warning(f"Incomplete user data in token: {user_data}")
        return None
    
    return user_data


def create_user_token_data(user: Dict[str, Any]) -> Dict[str, Any]:
    """Create token data from user object."""
    return {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "school_id": str(user.get("school_id")) if user.get("school_id") else None,
        "user_type": user.get("user_type", "user"),
        "teacher_id": user.get("teacher_id"),
    }


# Password validation functions
def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    # Optional: Add special character requirement
    # if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in password):
    #     return False, "Password must contain at least one special character"
    
    return True, "Password is strong"


# Role-based access control helpers
def has_role(user: Dict[str, Any], required_role: str) -> bool:
    """Check if user has the required role."""
    return user.get("role") == required_role


def has_any_role(user: Dict[str, Any], required_roles: list[str]) -> bool:
    """Check if user has any of the required roles."""
    return user.get("role") in required_roles


def is_system_admin(user: Dict[str, Any]) -> bool:
    """Check if user is a system admin."""
    return user.get("role") == "system_admin" or user.get("user_type") == "system_admin"


def is_school_admin(user: Dict[str, Any]) -> bool:
    """Check if user is a school admin."""
    return user.get("role") == "admin"


def is_teacher(user: Dict[str, Any]) -> bool:
    """Check if user is a teacher."""
    return user.get("role") == "teacher"


def is_bursar(user: Dict[str, Any]) -> bool:
    """Check if user is a bursar."""
    return user.get("role") == "bursar"


def is_parent(user: Dict[str, Any]) -> bool:
    """Check if user is a parent."""
    return user.get("role") == "parent"


# Permission check functions
def can_access_school(user: Dict[str, Any], school_id: str) -> bool:
    """Check if user can access a specific school."""
    if is_system_admin(user):
        return True
    
    user_school_id = user.get("school_id")
    if not user_school_id:
        return False
    
    return str(user_school_id) == str(school_id)


def can_manage_users(user: Dict[str, Any]) -> bool:
    """Check if user can manage other users."""
    return is_system_admin(user) or is_school_admin(user)


def can_view_financials(user: Dict[str, Any]) -> bool:
    """Check if user can view financial information."""
    return is_system_admin(user) or is_school_admin(user) or is_bursar(user)


# Example usage in dependency injection
async def get_current_user(request: Request) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_current_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(current_user: Dict[str, Any] = None) -> Dict[str, Any]:
    """FastAPI dependency to get current active user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    return current_user