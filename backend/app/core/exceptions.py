"""
Custom exceptions for the Nigerian LMS application.
Provides consistent error handling across the application.
"""

from fastapi import HTTPException, status
from typing import Optional, Any, Dict


class NigerianLMSException(HTTPException):
    """Base exception for Nigerian LMS application."""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An error occurred",
        headers: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or "UNKNOWN_ERROR"


# ============================================
# AUTHENTICATION EXCEPTIONS
# ============================================

class AuthenticationError(NigerianLMSException):
    """Authentication related errors."""
    
    def __init__(
        self,
        detail: str = "Authentication failed",
        error_code: str = "AUTH_ERROR",
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
        )


class AuthorizationError(NigerianLMSException):
    """Authorization related errors (403 Forbidden)."""
    
    def __init__(
        self,
        detail: str = "Access forbidden",
        error_code: str = "AUTHORIZATION_ERROR",
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password."""
    
    def __init__(self):
        super().__init__(
            detail="Invalid email or password",
            error_code="INVALID_CREDENTIALS",
        )


class TokenExpiredError(AuthenticationError):
    """JWT token has expired."""
    
    def __init__(self):
        super().__init__(
            detail="Token has expired",
            error_code="TOKEN_EXPIRED",
        )


class InvalidTokenError(AuthenticationError):
    """Invalid JWT token."""
    
    def __init__(self):
        super().__init__(
            detail="Invalid token",
            error_code="INVALID_TOKEN",
        )


class InsufficientPermissionsError(NigerianLMSException):
    """User doesn't have required permissions."""
    
    def __init__(
        self,
        detail: str = "Insufficient permissions",
        error_code: str = "INSUFFICIENT_PERMISSIONS",
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
        )


# ============================================
# VALIDATION EXCEPTIONS
# ============================================

class ValidationError(NigerianLMSException):
    """Data validation errors."""
    
    def __init__(
        self,
        detail: str = "Validation failed",
        error_code: str = "VALIDATION_ERROR",
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
        )


class RequiredFieldError(ValidationError):
    """Required field is missing."""
    
    def __init__(self, field_name: str):
        super().__init__(
            detail=f"Field '{field_name}' is required",
            error_code="REQUIRED_FIELD",
        )


class InvalidEmailError(ValidationError):
    """Invalid email format."""
    
    def __init__(self):
        super().__init__(
            detail="Invalid email format",
            error_code="INVALID_EMAIL",
        )


class PasswordStrengthError(ValidationError):
    """Password doesn't meet strength requirements."""
    
    def __init__(self, requirement: str):
        super().__init__(
            detail=f"Password must {requirement}",
            error_code="PASSWORD_STRENGTH",
        )


class InvalidRoleError(ValidationError):
    """Invalid user role."""
    
    def __init__(self, role: str, valid_roles: list):
        super().__init__(
            detail=f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}",
            error_code="INVALID_ROLE",
        )


# ============================================
# DATABASE EXCEPTIONS
# ============================================

class DatabaseError(NigerianLMSException):
    """Database related errors."""
    
    def __init__(
        self,
        detail: str = "Database error occurred",
        error_code: str = "DATABASE_ERROR",
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code,
        )


class RecordNotFoundError(DatabaseError):
    """Requested record not found in database."""
    
    def __init__(self, record_type: str, record_id: str):
        super().__init__(
            detail=f"{record_type} with ID '{record_id}' not found",
            error_code="RECORD_NOT_FOUND",
        )


class NotFoundError(NigerianLMSException):
    """Resource not found (404)."""
    
    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} with ID '{resource_id}' not found",
            error_code="NOT_FOUND",
        )


class DuplicateRecordError(DatabaseError):
    """Attempt to create duplicate record."""
    
    def __init__(self, record_type: str, field: str, value: str):
        super().__init__(
            detail=f"{record_type} with {field} '{value}' already exists",
            error_code="DUPLICATE_RECORD",
        )


class ConnectionError(DatabaseError):
    """Database connection error."""
    
    def __init__(self):
        super().__init__(
            detail="Database connection failed",
            error_code="CONNECTION_ERROR",
        )


# ============================================
# BUSINESS LOGIC EXCEPTIONS
# ============================================

class BusinessLogicError(NigerianLMSException):
    """Business logic related errors."""
    
    def __init__(
        self,
        detail: str = "Business logic error",
        error_code: str = "BUSINESS_LOGIC_ERROR",
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
        )


class SubscriptionError(BusinessLogicError):
    """Subscription related errors."""
    
    def __init__(
        self,
        detail: str = "Subscription error",
        error_code: str = "SUBSCRIPTION_ERROR",
    ):
        super().__init__(detail=detail, error_code=error_code)


class TrialExpiredError(SubscriptionError):
    """Trial period has expired."""
    
    def __init__(self):
        super().__init__(
            detail="Trial period has expired. Please upgrade your subscription.",
            error_code="TRIAL_EXPIRED",
        )


class SubscriptionLimitError(SubscriptionError):
    """Subscription limit reached."""
    
    def __init__(self, limit_type: str, current: int, max_allowed: int):
        super().__init__(
            detail=f"{limit_type} limit reached: {current}/{max_allowed}",
            error_code="SUBSCRIPTION_LIMIT",
        )


class OrganizationSuspendedError(BusinessLogicError):
    """Organization account is suspended."""
    
    def __init__(self):
        super().__init__(
            detail="Organization account is suspended. Please contact support.",
            error_code="ORGANIZATION_SUSPENDED",
        )


# ============================================
# EXTERNAL SERVICE EXCEPTIONS
# ============================================

class ExternalServiceError(NigerianLMSException):
    """External service errors (email, SMS, payment, etc.)."""
    
    def __init__(
        self,
        detail: str = "External service error",
        error_code: str = "EXTERNAL_SERVICE_ERROR",
    ):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            error_code=error_code,
        )


class EmailServiceError(ExternalServiceError):
    """Email service error."""
    
    def __init__(self):
        super().__init__(
            detail="Email service temporarily unavailable",
            error_code="EMAIL_SERVICE_ERROR",
        )


class SMSServiceError(ExternalServiceError):
    """SMS service error."""
    
    def __init__(self):
        super().__init__(
            detail="SMS service temporarily unavailable",
            error_code="SMS_SERVICE_ERROR",
        )


class PaymentServiceError(ExternalServiceError):
    """Payment service error."""
    
    def __init__(self):
        super().__init__(
            detail="Payment service temporarily unavailable",
            error_code="PAYMENT_SERVICE_ERROR",
        )


# ============================================
# HELPER FUNCTIONS
# ============================================

def handle_exception(exception: Exception) -> NigerianLMSException:
    """
    Convert generic exceptions to NigerianLMSException.
    
    Args:
        exception: The original exception
        
    Returns:
        NigerianLMSException: Appropriate application exception
    """
    if isinstance(exception, NigerianLMSException):
        return exception
    
    # Map common exceptions
    if isinstance(exception, ValueError):
        return ValidationError(detail=str(exception))
    
    if isinstance(exception, KeyError):
        return RequiredFieldError(str(exception))
    
    if isinstance(exception, ConnectionError):
        return ConnectionError()
    
    # Default to generic error
    return NigerianLMSException(
        detail=str(exception) or "An unexpected error occurred",
        error_code="UNEXPECTED_ERROR",
    )


def create_error_response(
    exception: NigerianLMSException,
    include_traceback: bool = False,
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        exception: The exception to convert to response
        include_traceback: Whether to include traceback in development
        
    Returns:
        Dict with error details
    """
    response = {
        "error": {
            "code": exception.error_code or "UNKNOWN_ERROR",
            "message": exception.detail,
            "status_code": exception.status_code,
        }
    }
    
    # Include traceback in development
    if include_traceback and hasattr(exception, "__traceback__"):
        import traceback
        response["error"]["traceback"] = traceback.format_exception(
            type(exception), exception, exception.__traceback__
        )
    
    return response


# ============================================
# ERROR CODES REFERENCE
# ============================================

ERROR_CODES = {
    # Authentication (AUTH_*)
    "AUTH_ERROR": "Authentication error",
    "INVALID_CREDENTIALS": "Invalid email or password",
    "TOKEN_EXPIRED": "Authentication token has expired",
    "INVALID_TOKEN": "Invalid authentication token",
    "INSUFFICIENT_PERMISSIONS": "User doesn't have required permissions",
    
    # Validation (VALIDATION_*)
    "VALIDATION_ERROR": "Data validation failed",
    "REQUIRED_FIELD": "Required field is missing",
    "INVALID_EMAIL": "Invalid email format",
    "PASSWORD_STRENGTH": "Password doesn't meet strength requirements",
    "INVALID_ROLE": "Invalid user role specified",
    
    # Database (DB_*)
    "DATABASE_ERROR": "Database operation failed",
    "RECORD_NOT_FOUND": "Requested record not found",
    "DUPLICATE_RECORD": "Record already exists",
    "CONNECTION_ERROR": "Database connection failed",
    
    # Business Logic (BUSINESS_*)
    "BUSINESS_LOGIC_ERROR": "Business logic violation",
    "SUBSCRIPTION_ERROR": "Subscription related error",
    "TRIAL_EXPIRED": "Trial period has expired",
    "SUBSCRIPTION_LIMIT": "Subscription limit reached",
    "ORGANIZATION_SUSPENDED": "Organization account is suspended",
    
    # External Services (SERVICE_*)
    "EXTERNAL_SERVICE_ERROR": "External service error",
    "EMAIL_SERVICE_ERROR": "Email service error",
    "SMS_SERVICE_ERROR": "SMS service error",
    "PAYMENT_SERVICE_ERROR": "Payment service error",
    
    # System (SYSTEM_*)
    "UNKNOWN_ERROR": "Unknown error occurred",
    "UNEXPECTED_ERROR": "Unexpected error occurred",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded",
    "MAINTENANCE_MODE": "System is in maintenance mode",
}