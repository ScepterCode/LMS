"""
Integrated Registration endpoints for Nigerian LMS.
Combined user + profile creation in atomic transactions.
"""

from fastapi import APIRouter, status, Request
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, date
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
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# REQUEST MODELS
# ============================================

class TeacherRegistration(BaseModel):
    """Integrated teacher registration model."""
    # User account details
    email: EmailStr
    password: str
    full_name: str
    phone: str
    
    # Teacher profile details
    staff_number: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: Optional[date] = None
    gender: str
    address: Optional[str] = None
    state_of_origin: Optional[str] = None
    lga: Optional[str] = None
    nationality: str = "Nigerian"
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    employment_date: date = None
    employment_type: str = "full-time"
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        if v not in ['Male', 'Female', 'Other']:
            raise ValueError('Gender must be Male, Female, or Other')
        return v
    
    @field_validator('employment_type')
    @classmethod
    def validate_employment_type(cls, v):
        if v not in ['full-time', 'part-time', 'contract']:
            raise ValueError('Employment type must be full-time, part-time, or contract')
        return v


class StudentRegistration(BaseModel):
    """Integrated student registration model."""
    # User account details (optional - some schools may not give students login)
    create_user_account: bool = False
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    
    # Student profile details
    admission_number: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: date
    gender: str
    blood_group: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    state_of_origin: Optional[str] = None
    lga: Optional[str] = None
    nationality: str = "Nigerian"
    religion: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    current_class_id: Optional[str] = None
    admission_date: date = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v, values):
        if values.data.get('create_user_account') and not v:
            raise ValueError('Password required when creating user account')
        if v:
            is_valid, message = validate_password_strength(v)
            if not is_valid:
                raise ValueError(message)
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v, values):
        if values.data.get('create_user_account') and not v:
            raise ValueError('Email required when creating user account')
        return v
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        if v not in ['Male', 'Female', 'Other']:
            raise ValueError('Gender must be Male, Female, or Other')
        return v


class ParentRegistration(BaseModel):
    """Integrated parent registration model."""
    # User account details
    email: EmailStr
    password: str
    
    # Parent profile details
    title: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    phone: str
    alternate_phone: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v


# ============================================
# HELPER FUNCTIONS
# ============================================

def require_admin(user: dict):
    """Ensure user is school admin or system admin."""
    if not user:
        raise AuthorizationError("User authentication failed")
    if user.get("role") not in ["admin", "system_admin"]:
        raise AuthorizationError("Only administrators can register users")


# ============================================
# INTEGRATED REGISTRATION ENDPOINTS
# ============================================

@router.post("/register-teacher", status_code=status.HTTP_201_CREATED)
async def register_teacher(request: Request, data: TeacherRegistration):
    """
    Register a new teacher with user account and profile in one atomic operation.
    Only admins can register teachers.
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
        
        # Check for duplicate email
        existing_user = supabase.table('users').select('id').eq('email', data.email).execute()
        if existing_user.data:
            raise DuplicateRecordError("User", "email", data.email)
        
        # Check for duplicate staff number
        existing_teacher = supabase.table('teachers').select('id').eq('staff_number', data.staff_number).execute()
        if existing_teacher.data:
            raise DuplicateRecordError("Teacher", "staff_number", data.staff_number)
        
        # Generate IDs
        user_id = str(uuid.uuid4())
        teacher_id = str(uuid.uuid4())
        password_hash = get_password_hash(data.password)
        
        # Step 1: Create user account
        user_data = {
            'id': user_id,
            'email': data.email,
            'password_hash': password_hash,
            'full_name': data.full_name,
            'role': 'teacher',
            'school_id': str(user["school_id"]),
            'phone': data.phone,
            'is_active': True,
            'email_verified': False,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        user_result = supabase.table('users').insert(user_data).execute()
        if not user_result.data:
            raise DatabaseError("Failed to create user account")
        
        # Step 2: Create teacher profile
        teacher_data = {
            'id': teacher_id,
            'user_id': user_id,
            'organization_id': str(user["school_id"]),
            'staff_number': data.staff_number,
            'first_name': data.first_name,
            'middle_name': data.middle_name,
            'last_name': data.last_name,
            'date_of_birth': data.date_of_birth.isoformat() if data.date_of_birth else None,
            'gender': data.gender,
            'email': data.email,
            'phone': data.phone,
            'address': data.address,
            'state_of_origin': data.state_of_origin,
            'lga': data.lga,
            'nationality': data.nationality,
            'qualification': data.qualification,
            'specialization': data.specialization,
            'employment_date': (data.employment_date or date.today()).isoformat(),
            'employment_type': data.employment_type,
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        teacher_result = supabase.table('teachers').insert(teacher_data).execute()
        if not teacher_result.data:
            # Rollback: delete user account
            supabase.table('users').delete().eq('id', user_id).execute()
            raise DatabaseError("Failed to create teacher profile")
        
        logger.info(f"Registered teacher: {data.email} (staff: {data.staff_number}) by {user['email']}")
        
        return {
            "message": "Teacher registered successfully",
            "user_id": user_id,
            "teacher_id": teacher_id,
            "email": data.email,
            "staff_number": data.staff_number
        }
        
    except (AuthorizationError, ValidationError, DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"Error registering teacher: {e}")
        raise DatabaseError(f"Failed to register teacher: {str(e)}")


@router.post("/register-student", status_code=status.HTTP_201_CREATED)
async def register_student(request: Request, data: StudentRegistration):
    """
    Register a new student with optional user account.
    Only admins can register students.
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
        
        # Check for duplicate admission number
        existing_student = supabase.table('students').select('id').eq(
            'admission_number', data.admission_number
        ).eq('organization_id', user["school_id"]).execute()
        
        if existing_student.data:
            raise DuplicateRecordError("Student", "admission_number", data.admission_number)
        
        user_id = None
        
        # Step 1: Create user account if requested
        if data.create_user_account:
            if not data.email or not data.password:
                raise ValidationError("Email and password required for user account")
            
            # Check for duplicate email
            existing_user = supabase.table('users').select('id').eq('email', data.email).execute()
            if existing_user.data:
                raise DuplicateRecordError("User", "email", data.email)
            
            user_id = str(uuid.uuid4())
            password_hash = get_password_hash(data.password)
            
            user_data = {
                'id': user_id,
                'email': data.email,
                'password_hash': password_hash,
                'full_name': f"{data.first_name} {data.middle_name or ''} {data.last_name}".replace('  ', ' '),
                'role': 'student',
                'school_id': str(user["school_id"]),
                'phone': data.phone,
                'is_active': True,
                'email_verified': False,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            user_result = supabase.table('users').insert(user_data).execute()
            if not user_result.data:
                raise DatabaseError("Failed to create user account")
        
        # Step 2: Create student profile
        student_id = str(uuid.uuid4())
        
        student_data = {
            'id': student_id,
            'organization_id': str(user["school_id"]),
            'user_id': user_id,  # Will be None if no user account created
            'admission_number': data.admission_number,
            'first_name': data.first_name,
            'middle_name': data.middle_name,
            'last_name': data.last_name,
            'date_of_birth': data.date_of_birth.isoformat(),
            'gender': data.gender,
            'blood_group': data.blood_group,
            'email': data.email,
            'phone': data.phone,
            'address': data.address,
            'state_of_origin': data.state_of_origin,
            'lga': data.lga,
            'nationality': data.nationality,
            'religion': data.religion,
            'medical_conditions': data.medical_conditions,
            'allergies': data.allergies,
            'current_class_id': data.current_class_id,
            'admission_date': (data.admission_date or date.today()).isoformat(),
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        student_result = supabase.table('students').insert(student_data).execute()
        if not student_result.data:
            # Rollback: delete user account if created
            if user_id:
                supabase.table('users').delete().eq('id', user_id).execute()
            raise DatabaseError("Failed to create student profile")
        
        logger.info(f"Registered student: {data.admission_number} (user_account: {data.create_user_account}) by {user['email']}")
        
        return {
            "message": "Student registered successfully",
            "student_id": student_id,
            "user_id": user_id,
            "admission_number": data.admission_number,
            "has_user_account": data.create_user_account
        }
        
    except (AuthorizationError, ValidationError, DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"Error registering student: {e}")
        raise DatabaseError(f"Failed to register student: {str(e)}")


@router.post("/register-parent", status_code=status.HTTP_201_CREATED)
async def register_parent(request: Request, data: ParentRegistration):
    """
    Register a new parent with user account and profile in one atomic operation.
    Only admins can register parents.
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
        
        # Check for duplicate email
        existing_user = supabase.table('users').select('id').eq('email', data.email).execute()
        if existing_user.data:
            raise DuplicateRecordError("User", "email", data.email)
        
        # Generate IDs
        user_id = str(uuid.uuid4())
        parent_id = str(uuid.uuid4())
        password_hash = get_password_hash(data.password)
        
        # Step 1: Create user account
        user_data = {
            'id': user_id,
            'email': data.email,
            'password_hash': password_hash,
            'full_name': f"{data.title or ''} {data.first_name} {data.last_name}".strip(),
            'role': 'parent',
            'school_id': str(user["school_id"]),
            'phone': data.phone,
            'is_active': True,
            'email_verified': False,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        user_result = supabase.table('users').insert(user_data).execute()
        if not user_result.data:
            raise DatabaseError("Failed to create user account")
        
        # Step 2: Create parent profile
        parent_data = {
            'id': parent_id,
            'user_id': user_id,
            'organization_id': str(user["school_id"]),
            'title': data.title,
            'first_name': data.first_name,
            'middle_name': data.middle_name,
            'last_name': data.last_name,
            'email': data.email,
            'phone': data.phone,
            'alternate_phone': data.alternate_phone,
            'address': data.address,
            'occupation': data.occupation,
            'employer': data.employer,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        parent_result = supabase.table('parents').insert(parent_data).execute()
        if not parent_result.data:
            # Rollback: delete user account
            supabase.table('users').delete().eq('id', user_id).execute()
            raise DatabaseError("Failed to create parent profile")
        
        logger.info(f"Registered parent: {data.email} by {user['email']}")
        
        return {
            "message": "Parent registered successfully",
            "user_id": user_id,
            "parent_id": parent_id,
            "email": data.email
        }
        
    except (AuthorizationError, ValidationError, DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"Error registering parent: {e}")
        raise DatabaseError(f"Failed to register parent: {str(e)}")
