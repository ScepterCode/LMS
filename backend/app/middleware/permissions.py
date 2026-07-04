"""
Permission middleware and decorators for endpoint authorization.
Provides reusable permission checks and audit logging.
"""

import logging
from typing import Callable, List, Optional
from functools import wraps
from datetime import datetime

from fastapi import HTTPException, status
from app.core.database import get_supabase
from app.core.permissions import PermissionChecker
from app.core.exceptions import AuthorizationError

logger = logging.getLogger(__name__)


# ============================================
# PERMISSION DECORATORS
# ============================================

def require_roles(allowed_roles: List[str]):
    """Decorator to require specific roles for endpoint access."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = current_user.get("role")
            if user_role not in allowed_roles:
                logger.warning(
                    f"Unauthorized access attempt: User {current_user.get('id')} "
                    f"with role '{user_role}' tried to access endpoint requiring {allowed_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_form_teacher(class_id_param: str = "class_id"):
    """Decorator to require form teacher access for a specific class."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Admins bypass form teacher check
            if current_user.get("role") in ["admin", "system_admin"]:
                return await func(*args, **kwargs)
            
            # Extract class_id from kwargs or args
            class_id = kwargs.get(class_id_param)
            if not class_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required parameter: {class_id_param}"
                )
            
            teacher_id = current_user.get("teacher_id")
            supabase = get_supabase()

            try:
                await PermissionChecker.verify_form_teacher_permission(
                    teacher_id, class_id, supabase
                )
            except AuthorizationError as e:
                logger.warning(
                    f"Form teacher check failed: Teacher {teacher_id} "
                    f"attempted to access class {class_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Form teacher access required: {str(e)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_subject_teacher(subject_id_param: str = "subject_id", class_id_param: str = "class_id"):
    """Decorator to require subject teacher access for a specific subject+class."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Admins bypass subject teacher check
            if current_user.get("role") in ["admin", "system_admin"]:
                return await func(*args, **kwargs)
            
            # Extract parameters
            subject_id = kwargs.get(subject_id_param)
            class_id = kwargs.get(class_id_param)
            
            if not subject_id or not class_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required parameters: {subject_id_param}, {class_id_param}"
                )
            
            teacher_id = current_user.get("teacher_id")
            supabase = get_supabase()

            try:
                await PermissionChecker.verify_subject_teacher_permission(
                    teacher_id, subject_id, class_id, supabase
                )
            except AuthorizationError as e:
                logger.warning(
                    f"Subject teacher check failed: Teacher {teacher_id} "
                    f"attempted to access subject {subject_id} in class {class_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Subject teacher access required: {str(e)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================
# PERMISSION AUDIT LOGGING
# ============================================

class PermissionAuditLog:
    """Log permission checks for security auditing."""
    
    @staticmethod
    async def log_access_attempt(
        user_id: str,
        action: str,
        resource: str,
        resource_id: str,
        granted: bool,
        reason: Optional[str] = None
    ):
        """Log an access attempt to the audit log."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "granted": granted,
            "reason": reason
        }
        
        # Log to application logs
        if granted:
            logger.info(f"ACCESS GRANTED: {log_entry}")
        else:
            logger.warning(f"ACCESS DENIED: {log_entry}")
        
        # In production, also log to database table for persistent audit trail
        # supabase = get_supabase()
        # supabase.table("permission_audit_log").insert(log_entry).execute()
    
    @staticmethod
    async def log_attendance_access(user_id: str, class_id: str, granted: bool, reason: Optional[str] = None):
        """Log attendance marking access attempt."""
        await PermissionAuditLog.log_access_attempt(
            user_id, "mark_attendance", "class", class_id, granted, reason
        )
    
    @staticmethod
    async def log_grade_entry_access(user_id: str, assessment_id: str, granted: bool, reason: Optional[str] = None):
        """Log grade entry access attempt."""
        await PermissionAuditLog.log_access_attempt(
            user_id, "enter_grades", "assessment", assessment_id, granted, reason
        )
    
    @staticmethod
    async def log_report_card_access(user_id: str, report_card_id: str, granted: bool, reason: Optional[str] = None):
        """Log report card access attempt."""
        await PermissionAuditLog.log_access_attempt(
            user_id, "access_report_card", "report_card", report_card_id, granted, reason
        )


# ============================================
# PERMISSION CACHING
# ============================================

class PermissionCache:
    """
    Simple in-memory cache for permission checks.
    In production, use Redis for distributed caching.
    """
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def get(self, key: str) -> Optional[bool]:
        """Get cached permission result."""
        if key in self._cache:
            result, timestamp = self._cache[key]
            # Check if expired
            if (datetime.utcnow() - timestamp).total_seconds() < self._cache_ttl:
                return result
            else:
                # Remove expired entry
                del self._cache[key]
        return None
    
    def set(self, key: str, value: bool):
        """Cache permission result."""
        self._cache[key] = (value, datetime.utcnow())
    
    def clear(self):
        """Clear all cached permissions."""
        self._cache.clear()
    
    def clear_user(self, user_id: str):
        """Clear cached permissions for a specific user."""
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"user:{user_id}:")]
        for key in keys_to_remove:
            del self._cache[key]


# Global permission cache instance
permission_cache = PermissionCache()


# ============================================
# ENHANCED PERMISSION CHECKER WITH CACHING
# ============================================

async def check_form_teacher_cached(teacher_id: str, class_id: str, supabase) -> bool:
    """Check form teacher permission with caching."""
    cache_key = f"user:{teacher_id}:form_teacher:class:{class_id}"
    
    # Check cache first
    cached_result = permission_cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Not in cache, check database
    result = await PermissionChecker.is_form_teacher(teacher_id, class_id, supabase)
    
    # Cache the result
    permission_cache.set(cache_key, result)
    
    return result


async def check_subject_teacher_cached(teacher_id: str, subject_id: str, class_id: str, supabase) -> bool:
    """Check subject teacher permission with caching."""
    cache_key = f"user:{teacher_id}:subject_teacher:subject:{subject_id}:class:{class_id}"
    
    # Check cache first
    cached_result = permission_cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Not in cache, check database
    result = await PermissionChecker.is_subject_teacher(teacher_id, subject_id, class_id, supabase)
    
    # Cache the result
    permission_cache.set(cache_key, result)
    
    return result


# ============================================
# PERMISSION VALIDATION HELPERS
# ============================================

async def validate_teacher_class_access(
    teacher_id: str,
    class_id: str,
    supabase,
    require_form_teacher: bool = False
) -> bool:
    """
    Validate if teacher has access to a class.
    
    Args:
        teacher_id: ID of the teacher
        class_id: ID of the class
        supabase: Supabase client
        require_form_teacher: If True, requires form teacher access
    
    Returns:
        True if access granted
    
    Raises:
        AuthorizationError if access denied
    """
    if require_form_teacher:
        is_form_teacher = await check_form_teacher_cached(teacher_id, class_id, supabase)
        if not is_form_teacher:
            raise AuthorizationError("You are not the form teacher of this class")
    else:
        # Check if teacher has any assignment to this class
        can_view = await PermissionChecker.can_view_students_in_class(teacher_id, class_id, supabase)
        if not can_view:
            raise AuthorizationError("You do not have access to this class")
    
    return True


async def validate_teacher_subject_access(
    teacher_id: str,
    subject_id: str,
    class_id: str,
    supabase
) -> bool:
    """
    Validate if teacher teaches a subject in a class.
    
    Raises:
        AuthorizationError if access denied
    """
    is_subject_teacher = await check_subject_teacher_cached(
        teacher_id, subject_id, class_id, supabase
    )
    
    if not is_subject_teacher:
        raise AuthorizationError(
            f"You do not teach this subject in this class"
        )
    
    return True


# ============================================
# ROLE HIERARCHY
# ============================================

ROLE_HIERARCHY = {
    "system_admin": 100,  # Highest level
    "admin": 80,          # School admin
    "bursar": 60,         # Financial admin
    "teacher": 40,        # Teaching staff
    "parent": 20,         # Parent access
    "student": 10         # Lowest level
}


def has_higher_role(user_role: str, required_role: str) -> bool:
    """Check if user's role is at or above the required role level."""
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


def get_accessible_roles(user_role: str) -> List[str]:
    """Get list of roles that a user can manage (roles at or below their level)."""
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    return [role for role, level in ROLE_HIERARCHY.items() if level <= user_level]
