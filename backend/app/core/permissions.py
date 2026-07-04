"""
Permission checks for Phase 4 teacher class features.
Enforces form teacher-only actions and subject teacher permissions.
"""

import logging
from typing import Optional
from uuid import UUID

from app.core.database import get_supabase
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class PermissionChecker:
    """Utility class for checking teacher permissions"""
    
    @staticmethod
    async def is_form_teacher(teacher_id: str, class_id: str, supabase) -> bool:
        """Check if teacher is the form teacher of a class."""
        try:
            response = supabase.table('teacher_class_assignments').select('id').eq(
                'teacher_id', teacher_id
            ).eq('class_id', class_id).eq('is_form_teacher', True).execute()
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error checking form teacher status: {e}")
            return False
    
    @staticmethod
    async def is_subject_teacher(teacher_id: str, subject_id: str, class_id: str, supabase) -> bool:
        """Check if teacher teaches a subject in a class."""
        try:
            response = supabase.table('teacher_class_assignments').select('id').eq(
                'teacher_id', teacher_id
            ).eq('subject_id', subject_id).eq('class_id', class_id).execute()
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error checking subject teacher status: {e}")
            return False
    
    @staticmethod
    async def get_teacher_classes(teacher_id: str, supabase) -> list[dict]:
        """Get all classes where teacher is form teacher."""
        try:
            response = supabase.table('teacher_class_assignments').select(
                'class_id'
            ).eq('teacher_id', teacher_id).eq('is_form_teacher', True).execute()
            
            return [r['class_id'] for r in response.data] if response.data else []
        except Exception as e:
            logger.error(f"Error getting teacher classes: {e}")
            return []
    
    @staticmethod
    async def get_teacher_subjects(teacher_id: str, class_id: Optional[str] = None, supabase = None) -> list[dict]:
        """Get all subjects taught by teacher (optionally in specific class)."""
        try:
            query = supabase.table('teacher_class_assignments').select(
                'subject_id, class_id'
            ).eq('teacher_id', teacher_id)
            
            if class_id:
                query = query.eq('class_id', class_id)
            
            response = query.execute()
            
            if not response.data:
                return []
            
            return response.data
        except Exception as e:
            logger.error(f"Error getting teacher subjects: {e}")
            return []
    
    @staticmethod
    async def can_mark_attendance(teacher_id: str, class_id: str, supabase) -> bool:
        """Form teachers can mark attendance for their class."""
        return await PermissionChecker.is_form_teacher(teacher_id, class_id, supabase)
    
    @staticmethod
    async def can_add_remark(teacher_id: str, class_id: str, student_id: str, supabase) -> bool:
        """Form teacher can add remarks for students in their class."""
        # Check 1: Is form teacher
        if not await PermissionChecker.is_form_teacher(teacher_id, class_id, supabase):
            return False
        
        # Check 2: Student is in this class
        try:
            student_check = supabase.table('students').select('id').eq(
                'id', student_id
            ).eq('current_class_id', class_id).execute()
            
            return bool(student_check.data)
        except Exception as e:
            logger.error(f"Error checking student in class: {e}")
            return False
    
    @staticmethod
    async def can_view_class_grades(teacher_id: str, class_id: str, supabase) -> bool:
        """Form teacher can view grades for their class."""
        return await PermissionChecker.is_form_teacher(teacher_id, class_id, supabase)
    
    @staticmethod
    async def can_enter_grades(teacher_id: str, subject_id: str, class_id: str, supabase) -> bool:
        """Subject teacher can enter grades for their subject in assigned classes."""
        return await PermissionChecker.is_subject_teacher(teacher_id, subject_id, class_id, supabase)
    
    @staticmethod
    async def can_send_report(teacher_id: str, class_id: str, supabase) -> bool:
        """Form teacher can send reports for their class."""
        return await PermissionChecker.is_form_teacher(teacher_id, class_id, supabase)
    
    @staticmethod
    async def can_view_students_in_class(teacher_id: str, class_id: str, supabase) -> bool:
        """
        Form teacher can view students in their class.
        Subject teacher can view students they teach in assigned classes.
        """
        # Check if form teacher
        is_form_teacher = await PermissionChecker.is_form_teacher(teacher_id, class_id, supabase)
        if is_form_teacher:
            return True
        
        # Check if subject teacher in any subject
        assignments = await PermissionChecker.get_teacher_subjects(teacher_id, class_id, supabase)
        return len(assignments) > 0
    
    @staticmethod
    async def verify_admin_only(user: dict):
        """Verify user is school admin or system admin."""
        if user.get("role") not in ["admin", "system_admin"]:
            raise AuthorizationError("Only school administrators can perform this action")
    
    @staticmethod
    async def verify_teacher_only(user: dict):
        """Verify user is a teacher."""
        if user.get("role") not in ["teacher", "admin", "system_admin"]:
            raise AuthorizationError("Only teachers can access this resource")
    
    @staticmethod
    async def verify_form_teacher_permission(teacher_id: str, class_id: str, supabase) -> bool:
        """Verify teacher is form teacher of class. Raises exception if not."""
        is_form_teacher = await PermissionChecker.is_form_teacher(teacher_id, class_id, supabase)
        if not is_form_teacher:
            raise AuthorizationError(f"You are not the form teacher of this class")
        return True
    
    @staticmethod
    async def verify_subject_teacher_permission(teacher_id: str, subject_id: str, class_id: str, supabase) -> bool:
        """Verify teacher teaches subject in class. Raises exception if not."""
        is_subject_teacher = await PermissionChecker.is_subject_teacher(teacher_id, subject_id, class_id, supabase)
        if not is_subject_teacher:
            raise AuthorizationError(f"You do not teach {subject_id} in this class")
        return True


# ============================================
# Permission Matrix Documentation
# ============================================

PERMISSION_MATRIX = {
    "form_teacher": {
        "can_mark_attendance": {
            "description": "Mark attendance for class students",
            "requires": ["is_form_teacher"],
            "scope": "own_class_only"
        },
        "can_add_remark": {
            "description": "Add remarks to student report cards",
            "requires": ["is_form_teacher", "student_in_class"],
            "scope": "own_class_only"
        },
        "can_view_class_grades": {
            "description": "View all grades for class students",
            "requires": ["is_form_teacher"],
            "scope": "own_class_only"
        },
        "can_send_report": {
            "description": "Send reports to parents",
            "requires": ["is_form_teacher"],
            "scope": "own_class_only"
        },
        "can_view_students": {
            "description": "View list of students in class",
            "requires": ["is_form_teacher"],
            "scope": "own_class_only"
        }
    },
    
    "subject_teacher": {
        "can_enter_grades": {
            "description": "Enter grades for own subject",
            "requires": ["is_subject_teacher"],
            "scope": "assigned_subject_in_assigned_class"
        },
        "can_view_students": {
            "description": "View students in assigned class",
            "requires": ["is_subject_teacher"],
            "scope": "assigned_class_only"
        },
        "can_create_assessment": {
            "description": "Create assessments for own subject",
            "requires": ["is_subject_teacher"],
            "scope": "assigned_subject_in_assigned_class"
        }
    },
    
    "school_admin": {
        "can_create_grading_scheme": {
            "description": "Create and configure grading schemes",
            "requires": ["is_school_admin"],
            "scope": "all"
        },
        "can_assign_teacher_to_class": {
            "description": "Assign teachers to classes/subjects",
            "requires": ["is_school_admin"],
            "scope": "all"
        },
        "can_set_form_teacher": {
            "description": "Designate form teacher for class",
            "requires": ["is_school_admin"],
            "scope": "all"
        },
        "can_create_class_with_subjects": {
            "description": "Create classes and define curriculum",
            "requires": ["is_school_admin"],
            "scope": "all"
        },
        "can_manage_subjects": {
            "description": "Add/remove subjects from classes",
            "requires": ["is_school_admin"],
            "scope": "all"
        }
    },
    
    "system_admin": {
        "all_permissions": {
            "description": "Full system access",
            "requires": ["is_system_admin"],
            "scope": "all"
        }
    }
}


# ============================================
# API Endpoint Permission Map
# ============================================

ENDPOINT_PERMISSIONS = {
    # Admin Endpoints
    "POST /teacher-management/grading-schemes": ["admin"],
    "PUT /teacher-management/grading-schemes/{id}": ["admin"],
    "POST /teacher-management/classes/{id}/subjects": ["admin"],
    "DELETE /teacher-management/classes/{id}/subjects/{subject_id}": ["admin"],
    "POST /teacher-management/teacher-class-assignments": ["admin"],
    "PUT /teacher-management/teacher-class-assignments/{id}": ["admin"],
    "DELETE /teacher-management/teacher-class-assignments/{id}": ["admin"],
    
    # Teacher Endpoints - Form Teacher Only
    "POST /teacher/my-classes/{id}/attendance": ["teacher", "form_teacher_check"],
    "POST /teacher/my-classes/{id}/remarks": ["teacher", "form_teacher_check"],
    "POST /teacher/my-classes/{id}/send-reports": ["teacher", "form_teacher_check"],
    "GET /teacher/my-classes/{id}/attendance": ["teacher", "form_teacher_check"],
    "GET /teacher/my-classes/{id}/remarks": ["teacher", "form_teacher_check"],
    "GET /teacher/my-classes/{id}/grades": ["teacher", "form_teacher_check"],
    "GET /teacher/my-classes/{id}/students": ["teacher", "form_teacher_check"],
    
    # Teacher Endpoints - General
    "GET /teacher/my-classes": ["teacher"],
    "GET /teacher/my-reports": ["teacher"],
    "GET /teacher/my-reports/{id}": ["teacher"],
    "PUT /teacher/remarks/{id}": ["teacher", "remarks_author_check"],
}
