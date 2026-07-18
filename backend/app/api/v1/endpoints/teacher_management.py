"""
Phase 4: Teacher Management API endpoints.
Handles:
- Grading schemes (configurable grading formats)
- Class subjects (curriculum management)
- Teacher-class assignments (multi-class, multi-subject, form teacher)
- Student remarks (form teacher comments)
- School reports (report distribution to parents)
"""

from fastapi import APIRouter, Request, status, Query
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid
import logging

from app.models.teacher_management import (
    # Grading Schemes
    GradingSchemeCreate,
    GradingSchemeUpdate,
    GradingSchemeResponse,
    GradingSchemeComponentResponse,
    # Class Subjects
    ClassSubjectCreate,
    ClassSubjectUpdate,
    ClassSubjectResponse,
    # Teacher Assignments
    TeacherClassAssignmentCreate,
    TeacherClassAssignmentUpdate,
    TeacherClassAssignmentResponse,
    ClassDetailedResponse,
    # Remarks & Reports
    StudentRemarkCreate,
    StudentRemarkUpdate,
    StudentRemarkResponse,
    SchoolReportCreate,
    SchoolReportUpdate,
    SchoolReportResponse,
    BulkReportSend,
)
from app.core.database import get_supabase
from app.core.security import get_current_user_from_token, get_token_from_request
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    DatabaseError,
    AuthorizationError,
    DuplicateRecordError
)

router = APIRouter()
logger = logging.getLogger(__name__)


def require_admin(user: dict):
    """Ensure user is school admin, system admin, or dean."""
    if user.get("role") not in ["admin", "system_admin", "dean"]:
        raise AuthorizationError("Only administrators can perform this action")


def require_form_teacher_or_admin(user: dict, class_id: str = None):
    """Ensure user is form teacher of the class or admin."""
    if user.get("role") in ["admin", "system_admin"]:
        return True
    
    if user.get("role") != "teacher":
        raise AuthorizationError("Only form teachers or administrators can perform this action")
    
    # If class_id provided, check if user is form teacher of that class
    if class_id:
        supabase = get_supabase()
        assignment = supabase.table('teacher_class_assignments').select('id').eq(
            'teacher_id', user.get("teacher_id")
        ).eq('class_id', class_id).eq('is_form_teacher', True).execute()
        
        if not assignment.data:
            raise AuthorizationError("You are not the form teacher of this class")
    
    return True


# ============================================
# GRADING SCHEMES ENDPOINTS
# ============================================

@router.post("/grading-schemes", response_model=GradingSchemeResponse, status_code=status.HTTP_201_CREATED)
def create_grading_scheme(request: Request, data: GradingSchemeCreate):
    """Create a new grading scheme with components. Admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Check if scheme name already exists for this org/session
        existing = supabase.table('grading_schemes').select('id').eq(
            'organization_id', user["school_id"]
        ).eq('session_id', str(data.session_id)).eq('name', data.name).execute()
        
        if existing.data:
            raise DuplicateRecordError("Grading scheme", "name", data.name)
        
        # If setting as default, unset other defaults first
        if data.is_default:
            supabase.table('grading_schemes').update({
                'is_default': False
            }).eq('organization_id', user["school_id"]).eq(
                'session_id', str(data.session_id)
            ).execute()
        
        # Create scheme
        scheme_data = {
            'id': str(uuid.uuid4()),
            'organization_id': user["school_id"],
            'session_id': str(data.session_id),
            'name': data.name,
            'description': data.description,
            'is_active': True,
            'is_default': data.is_default,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        scheme_response = supabase.table('grading_schemes').insert(scheme_data).execute()
        
        if not scheme_response.data:
            raise DatabaseError("Failed to create grading scheme")
        
        scheme_id = scheme_response.data[0]['id']
        
        # Create components
        components_data = []
        for comp in data.components:
            components_data.append({
                'id': str(uuid.uuid4()),
                'grading_scheme_id': scheme_id,
                'component_type': comp.component_type,
                'component_name': comp.component_name,
                'weight_percentage': float(comp.weight_percentage),
                'max_score': float(comp.max_score),
                'required': comp.required,
                'display_order': comp.display_order,
                'created_at': datetime.utcnow().isoformat()
            })
        
        components_response = supabase.table('grading_scheme_components').insert(
            components_data
        ).execute()
        
        # Fetch complete scheme with components
        complete_scheme = scheme_response.data[0]
        complete_scheme['components'] = components_response.data
        
        logger.info(f"Created grading scheme {scheme_id} for org {user['school_id']}")
        return complete_scheme
        
    except (AuthorizationError, ValidationError, DuplicateRecordError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error creating grading scheme: {e}")
        raise DatabaseError(f"Failed to create grading scheme: {str(e)}")


@router.get("/grading-schemes", response_model=List[GradingSchemeResponse])
def list_grading_schemes(
    request: Request,
    session_id: Optional[UUID] = None,
    is_active: Optional[bool] = None
):
    """List all grading schemes for the organization."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        query = supabase.table('grading_schemes').select('*').eq(
            'organization_id', user["school_id"]
        )
        
        if session_id:
            query = query.eq('session_id', str(session_id))
        
        if is_active is not None:
            query = query.eq('is_active', is_active)
        
        query = query.order('created_at', desc=True)
        response = query.execute()
        
        # Fetch components for each scheme
        schemes = response.data or []
        for scheme in schemes:
            components = supabase.table('grading_scheme_components').select('*').eq(
                'grading_scheme_id', scheme['id']
            ).order('display_order').execute()
            scheme['components'] = components.data or []
        
        return schemes
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing grading schemes: {e}")
        raise DatabaseError(f"Failed to list grading schemes: {str(e)}")


@router.get("/grading-schemes/{scheme_id}", response_model=GradingSchemeResponse)
def get_grading_scheme(request: Request, scheme_id: UUID):
    """Get a specific grading scheme with its components."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Fetch scheme
        scheme_response = supabase.table('grading_schemes').select('*').eq(
            'id', str(scheme_id)
        ).eq('organization_id', user["school_id"]).execute()
        
        if not scheme_response.data:
            raise NotFoundError("Grading scheme", str(scheme_id))
        
        scheme = scheme_response.data[0]
        
        # Fetch components
        components = supabase.table('grading_scheme_components').select('*').eq(
            'grading_scheme_id', str(scheme_id)
        ).order('display_order').execute()
        
        scheme['components'] = components.data or []
        
        return scheme
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting grading scheme: {e}")
        raise DatabaseError(f"Failed to get grading scheme: {str(e)}")


@router.put("/grading-schemes/{scheme_id}", response_model=GradingSchemeResponse)
def update_grading_scheme(request: Request, scheme_id: UUID, data: GradingSchemeUpdate):
    """Update a grading scheme. Admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify scheme exists
        existing = supabase.table('grading_schemes').select('*').eq(
            'id', str(scheme_id)
        ).eq('organization_id', user["school_id"]).execute()
        
        if not existing.data:
            raise NotFoundError("Grading scheme", str(scheme_id))
        
        # If setting as default, unset other defaults
        if data.is_default:
            supabase.table('grading_schemes').update({
                'is_default': False
            }).eq('organization_id', user["school_id"]).eq(
                'session_id', existing.data[0]['session_id']
            ).execute()
        
        # Update scheme
        update_data = data.model_dump(mode="json", exclude_unset=True)
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            response = supabase.table('grading_schemes').update(update_data).eq(
                'id', str(scheme_id)
            ).execute()
            
            if not response.data:
                raise DatabaseError("Failed to update grading scheme")
            
            # Fetch components
            components = supabase.table('grading_scheme_components').select('*').eq(
                'grading_scheme_id', str(scheme_id)
            ).order('display_order').execute()
            
            scheme = response.data[0]
            scheme['components'] = components.data or []
            
            logger.info(f"Updated grading scheme {scheme_id}")
            return scheme
        
        return existing.data[0]
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating grading scheme: {e}")
        raise DatabaseError(f"Failed to update grading scheme: {str(e)}")


@router.delete("/grading-schemes/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grading_scheme(request: Request, scheme_id: UUID):
    """Delete a grading scheme. Admin only. Will cascade delete components."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify scheme exists and belongs to org
        existing = supabase.table('grading_schemes').select('id').eq(
            'id', str(scheme_id)
        ).eq('organization_id', user["school_id"]).execute()
        
        if not existing.data:
            raise NotFoundError("Grading scheme", str(scheme_id))
        
        # Delete (components will cascade delete)
        supabase.table('grading_schemes').delete().eq('id', str(scheme_id)).execute()
        
        logger.info(f"Deleted grading scheme {scheme_id}")
        return None
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting grading scheme: {e}")
        raise DatabaseError(f"Failed to delete grading scheme: {str(e)}")


# ============================================
# CLASS SUBJECTS ENDPOINTS (Curriculum)
# ============================================

@router.post("/classes/{class_id}/subjects", response_model=ClassSubjectResponse, status_code=status.HTTP_201_CREATED)
def add_subject_to_class(request: Request, class_id: UUID, data: ClassSubjectCreate):
    """Add a subject to a class curriculum. Admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify class exists
        class_check = supabase.table('classes').select('id').eq(
            'id', str(class_id)
        ).eq('organization_id', user["school_id"]).execute()
        
        if not class_check.data:
            raise NotFoundError("Class", str(class_id))
        
        # Verify subject exists
        subject_check = supabase.table('subjects').select('id, name').eq(
            'id', str(data.subject_id)
        ).eq('organization_id', user["school_id"]).execute()
        
        if not subject_check.data:
            raise NotFoundError("Subject", str(data.subject_id))
        
        # Check for duplicate
        existing = supabase.table('class_subjects').select('id').eq(
            'class_id', str(class_id)
        ).eq('subject_id', str(data.subject_id)).eq(
            'session_id', str(data.session_id)
        ).execute()
        
        if existing.data:
            raise DuplicateRecordError("Class subject", "class-subject-session", "this combination")
        
        # Create class-subject relationship
        class_subject_data = {
            'id': str(uuid.uuid4()),
            'class_id': str(class_id),
            'subject_id': str(data.subject_id),
            'session_id': str(data.session_id),
            'is_mandatory': data.is_mandatory,
            'display_order': data.display_order,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.table('class_subjects').insert(class_subject_data).execute()
        
        if not response.data:
            raise DatabaseError("Failed to add subject to class")
        
        # Enrich response
        result = response.data[0]
        result['subject_name'] = subject_check.data[0]['name']
        
        logger.info(f"Added subject {data.subject_id} to class {class_id}")
        return result
        
    except (AuthorizationError, NotFoundError, DuplicateRecordError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error adding subject to class: {e}")
        raise DatabaseError(f"Failed to add subject to class: {str(e)}")


@router.get("/classes/{class_id}/subjects", response_model=List[ClassSubjectResponse])
def list_class_subjects(
    request: Request,
    class_id: UUID,
    session_id: Optional[UUID] = None
):
    """List all subjects for a class (curriculum)."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify class exists
        class_check = supabase.table('classes').select('id').eq(
            'id', str(class_id)
        ).eq('organization_id', user["school_id"]).execute()
        
        if not class_check.data:
            raise NotFoundError("Class", str(class_id))
        
        query = supabase.table('class_subjects').select('*').eq('class_id', str(class_id))
        
        if session_id:
            query = query.eq('session_id', str(session_id))
        
        query = query.order('display_order')
        response = query.execute()
        
        # Enrich with subject names
        class_subjects = response.data or []
        for cs in class_subjects:
            subject = supabase.table('subjects').select('name').eq('id', cs['subject_id']).execute()
            if subject.data:
                cs['subject_name'] = subject.data[0]['name']
        
        return class_subjects
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing class subjects: {e}")
        raise DatabaseError(f"Failed to list class subjects: {str(e)}")


@router.delete("/classes/{class_id}/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_subject_from_class(
    request: Request,
    class_id: UUID,
    subject_id: UUID,
    session_id: UUID = Query(..., description="Session ID")
):
    """Remove a subject from class curriculum. Admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Find and delete
        existing = supabase.table('class_subjects').select('id').eq(
            'class_id', str(class_id)
        ).eq('subject_id', str(subject_id)).eq('session_id', str(session_id)).execute()
        
        if not existing.data:
            raise NotFoundError("Class subject", f"{class_id}-{subject_id}")
        
        supabase.table('class_subjects').delete().eq('id', existing.data[0]['id']).execute()
        
        logger.info(f"Removed subject {subject_id} from class {class_id}")
        return None
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error removing subject from class: {e}")
        raise DatabaseError(f"Failed to remove subject from class: {str(e)}")


# Continue in next part...


# ============================================
# TEACHER CLASS ASSIGNMENTS ENDPOINTS
# ============================================

@router.post("/teacher-assignments", response_model=TeacherClassAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_teacher_assignment(request: Request, data: TeacherClassAssignmentCreate):
    """Assign a teacher to teach a subject in a class. Admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify teacher exists
        teacher_check = supabase.table('teachers').select('id, first_name, last_name').eq(
            'id', str(data.teacher_id)
        ).eq('organization_id', user["school_id"]).execute()
        
        if not teacher_check.data:
            raise NotFoundError("Teacher", str(data.teacher_id))
        
        # Verify class exists
        class_check = supabase.table('classes').select('id, name').eq(
            'id', str(data.class_id)
        ).eq('organization_id', user["school_id"]).execute()
        
        if not class_check.data:
            raise NotFoundError("Class", str(data.class_id))
        
        # Verify subject exists
        subject_check = supabase.table('subjects').select('id, name').eq(
            'id', str(data.subject_id)
        ).eq('organization_id', user["school_id"]).execute()
        
        if not subject_check.data:
            raise NotFoundError("Subject", str(data.subject_id))
        
        # If setting as form teacher, check if class already has one
        if data.is_form_teacher:
            existing_form_teacher = supabase.table('teacher_class_assignments').select('id').eq(
                'class_id', str(data.class_id)
            ).eq('session_id', str(data.session_id)).eq('is_form_teacher', True).execute()
            
            if existing_form_teacher.data:
                raise ValidationError("This class already has a form teacher for this session")
        
        # Check for duplicate assignment
        existing_query = supabase.table('teacher_class_assignments').select('id').eq(
            'teacher_id', str(data.teacher_id)
        ).eq('subject_id', str(data.subject_id)).eq(
            'class_id', str(data.class_id)
        )
        if data.term_id:
            existing_query = existing_query.eq('term_id', str(data.term_id))
        else:
            existing_query = existing_query.is_('term_id', 'null')
        existing = existing_query.execute()
        
        if existing.data:
            raise DuplicateRecordError("Teacher assignment", "teacher-subject-class-term", "this combination")
        
        # Create assignment
        assignment_data = {
            'id': str(uuid.uuid4()),
            'teacher_id': str(data.teacher_id),
            'class_id': str(data.class_id),
            'subject_id': str(data.subject_id),
            'session_id': str(data.session_id),
            'term_id': str(data.term_id) if data.term_id else None,
            'is_form_teacher': data.is_form_teacher,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.table('teacher_class_assignments').insert(assignment_data).execute()
        
        if not response.data:
            raise DatabaseError("Failed to create teacher assignment")
        
        # Enrich response
        result = response.data[0]
        result['teacher_name'] = f"{teacher_check.data[0]['first_name']} {teacher_check.data[0]['last_name']}"
        result['class_name'] = class_check.data[0]['name']
        result['subject_name'] = subject_check.data[0]['name']
        
        logger.info(f"Created teacher assignment {result['id']}")
        return result
        
    except (AuthorizationError, NotFoundError, ValidationError, DuplicateRecordError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error creating teacher assignment: {e}")
        raise DatabaseError(f"Failed to create teacher assignment: {str(e)}")


@router.get("/teacher-assignments", response_model=List[TeacherClassAssignmentResponse])
def list_teacher_assignments(
    request: Request,
    teacher_id: Optional[UUID] = None,
    class_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
    is_form_teacher: Optional[bool] = None
):
    """List teacher assignments with filters."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Build query with joins (note: supabase doesn't support complex joins easily)
        # We'll fetch and enrich manually
        query = supabase.table('teacher_class_assignments').select('*')
        
        if teacher_id:
            query = query.eq('teacher_id', str(teacher_id))
        
        if class_id:
            query = query.eq('class_id', str(class_id))
        
        if session_id:
            query = query.eq('session_id', str(session_id))
        
        if is_form_teacher is not None:
            query = query.eq('is_form_teacher', is_form_teacher)
        
        query = query.order('created_at', desc=True)
        response = query.execute()
        
        assignments = response.data or []
        
        # Enrich with names
        for assignment in assignments:
            # Get teacher name
            teacher = supabase.table('teachers').select('first_name, last_name').eq(
                'id', assignment['teacher_id']
            ).eq('organization_id', user["school_id"]).execute()
            if teacher.data:
                assignment['teacher_name'] = f"{teacher.data[0]['first_name']} {teacher.data[0]['last_name']}"
            
            # Get class name
            cls = supabase.table('classes').select('name').eq('id', assignment['class_id']).execute()
            if cls.data:
                assignment['class_name'] = cls.data[0]['name']
            
            # Get subject name
            subject = supabase.table('subjects').select('name').eq('id', assignment['subject_id']).execute()
            if subject.data:
                assignment['subject_name'] = subject.data[0]['name']
        
        return assignments
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing teacher assignments: {e}")
        raise DatabaseError(f"Failed to list teacher assignments: {str(e)}")


@router.get("/teacher-assignments/{assignment_id}", response_model=TeacherClassAssignmentResponse)
def get_teacher_assignment(request: Request, assignment_id: UUID):
    """Get a specific teacher assignment."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        response = supabase.table('teacher_class_assignments').select('*').eq(
            'id', str(assignment_id)
        ).execute()
        
        if not response.data:
            raise NotFoundError("Teacher assignment", str(assignment_id))
        
        assignment = response.data[0]
        
        # Enrich with names
        teacher = supabase.table('teachers').select('first_name, last_name').eq(
            'id', assignment['teacher_id']
        ).eq('organization_id', user["school_id"]).execute()
        if teacher.data:
            assignment['teacher_name'] = f"{teacher.data[0]['first_name']} {teacher.data[0]['last_name']}"
        
        cls = supabase.table('classes').select('name').eq('id', assignment['class_id']).execute()
        if cls.data:
            assignment['class_name'] = cls.data[0]['name']
        
        subject = supabase.table('subjects').select('name').eq('id', assignment['subject_id']).execute()
        if subject.data:
            assignment['subject_name'] = subject.data[0]['name']
        
        return assignment
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting teacher assignment: {e}")
        raise DatabaseError(f"Failed to get teacher assignment: {str(e)}")


@router.put("/teacher-assignments/{assignment_id}", response_model=TeacherClassAssignmentResponse)
def update_teacher_assignment(request: Request, assignment_id: UUID, data: TeacherClassAssignmentUpdate):
    """Update a teacher assignment. Admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify assignment exists
        existing = supabase.table('teacher_class_assignments').select('*').eq(
            'id', str(assignment_id)
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Teacher assignment", str(assignment_id))
        
        assignment = existing.data[0]
        
        # If changing to form teacher, check if class already has one
        if data.is_form_teacher and not assignment['is_form_teacher']:
            existing_form_teacher = supabase.table('teacher_class_assignments').select('id').eq(
                'class_id', assignment['class_id']
            ).eq('session_id', assignment['session_id']).eq('is_form_teacher', True).execute()
            
            if existing_form_teacher.data:
                raise ValidationError("This class already has a form teacher for this session")
        
        # Update assignment
        update_data = data.model_dump(mode="json", exclude_unset=True)
        if update_data:
            if 'term_id' in update_data and update_data['term_id']:
                update_data['term_id'] = str(update_data['term_id'])
            
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            response = supabase.table('teacher_class_assignments').update(update_data).eq(
                'id', str(assignment_id)
            ).execute()
            
            if not response.data:
                raise DatabaseError("Failed to update teacher assignment")
            
            logger.info(f"Updated teacher assignment {assignment_id}")
            
            # Fetch and enrich
            assignment = response.data[0]
            teacher = supabase.table('teachers').select('first_name, last_name').eq('id', assignment['teacher_id']).execute()
            if teacher.data:
                assignment['teacher_name'] = f"{teacher.data[0]['first_name']} {teacher.data[0]['last_name']}"
            
            cls = supabase.table('classes').select('name').eq('id', assignment['class_id']).execute()
            if cls.data:
                assignment['class_name'] = cls.data[0]['name']
            
            subject = supabase.table('subjects').select('name').eq('id', assignment['subject_id']).execute()
            if subject.data:
                assignment['subject_name'] = subject.data[0]['name']
            
            return assignment
        
        return assignment
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating teacher assignment: {e}")
        raise DatabaseError(f"Failed to update teacher assignment: {str(e)}")


@router.delete("/teacher-assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher_assignment(request: Request, assignment_id: UUID):
    """Delete a teacher assignment. Admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify assignment exists
        existing = supabase.table('teacher_class_assignments').select('id').eq(
            'id', str(assignment_id)
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Teacher assignment", str(assignment_id))
        
        supabase.table('teacher_class_assignments').delete().eq('id', str(assignment_id)).execute()
        
        logger.info(f"Deleted teacher assignment {assignment_id}")
        return None
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting teacher assignment: {e}")
        raise DatabaseError(f"Failed to delete teacher assignment: {str(e)}")


@router.get("/teacher-assignments/teacher/{teacher_id}/classes", response_model=List[dict])
def get_teacher_classes(request: Request, teacher_id: UUID, session_id: Optional[UUID] = None):
    """Get all classes a teacher is assigned to (with subjects)."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        query = supabase.table('teacher_class_assignments').select('*').eq(
            'teacher_id', str(teacher_id)
        )
        
        if session_id:
            query = query.eq('session_id', str(session_id))
        
        response = query.execute()
        
        # Group by class
        classes_dict = {}
        for assignment in response.data or []:
            class_id = assignment['class_id']
            
            if class_id not in classes_dict:
                cls = supabase.table('classes').select('*').eq('id', class_id).execute()
                if cls.data:
                    classes_dict[class_id] = {
                        **cls.data[0],
                        'is_form_teacher': assignment['is_form_teacher'],
                        'subjects': []
                    }
            
            # Add subject
            subject = supabase.table('subjects').select('*').eq('id', assignment['subject_id']).execute()
            if subject.data:
                classes_dict[class_id]['subjects'].append(subject.data[0])
        
        return list(classes_dict.values())
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting teacher classes: {e}")
        raise DatabaseError(f"Failed to get teacher classes: {str(e)}")


@router.get("/form-teachers", response_model=List[dict])
def list_form_teachers(request: Request, session_id: Optional[UUID] = None):
    """List all form teachers with their classes."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        query = supabase.table('teacher_class_assignments').select('*').eq('is_form_teacher', True)
        
        if session_id:
            query = query.eq('session_id', str(session_id))
        
        response = query.execute()
        
        form_teachers = []
        for assignment in response.data or []:
            # Get teacher info
            teacher = supabase.table('teachers').select('id, first_name, last_name, email, phone').eq(
                'id', assignment['teacher_id']
            ).eq('organization_id', user["school_id"]).execute()
            
            # Get class info
            cls = supabase.table('classes').select('id, name, level, section').eq(
                'id', assignment['class_id']
            ).execute()
            
            if teacher.data and cls.data:
                form_teachers.append({
                    'teacher': teacher.data[0],
                    'class': cls.data[0],
                    'session_id': assignment['session_id'],
                    'assignment_id': assignment['id']
                })
        
        return form_teachers
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing form teachers: {e}")
        raise DatabaseError(f"Failed to list form teachers: {str(e)}")


# Continue with remarks and reports...


# ============================================
# STUDENT REMARKS ENDPOINTS
# ============================================

@router.post("/remarks", response_model=StudentRemarkResponse, status_code=status.HTTP_201_CREATED)
def create_student_remark(request: Request, data: StudentRemarkCreate):
    """Add a remark to a student's report card. Form teacher or admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Determine form teacher ID
        form_teacher_id = None
        if user.get("role") == "teacher" and user.get("teacher_id"):
            # Verify user is form teacher of this class
            assignment = supabase.table('teacher_class_assignments').select('id').eq(
                'teacher_id', user["teacher_id"]
            ).eq('class_id', str(data.class_id)).eq(
                'session_id', str(data.session_id)
            ).eq('is_form_teacher', True).execute()
            
            if not assignment.data and user.get("role") != "admin":
                raise AuthorizationError("You are not the form teacher of this class")
            
            form_teacher_id = user["teacher_id"]
        elif user.get("role") in ["admin", "system_admin"]:
            # Admin can add remarks, but we need a form teacher ID
            # Get the form teacher for this class
            assignment = supabase.table('teacher_class_assignments').select('teacher_id').eq(
                'class_id', str(data.class_id)
            ).eq('session_id', str(data.session_id)).eq('is_form_teacher', True).execute()
            
            if assignment.data:
                form_teacher_id = assignment.data[0]['teacher_id']
            else:
                raise ValidationError("This class does not have a form teacher assigned")
        
        if not form_teacher_id:
            raise AuthorizationError("Unable to determine form teacher")
        
        # Verify student exists in the class
        student = supabase.table('students').select('id, first_name, last_name').eq(
            'id', str(data.student_id)
        ).eq('organization_id', user["school_id"]).eq(
            'current_class_id', str(data.class_id)
        ).execute()
        
        if not student.data:
            raise NotFoundError("Student in this class", str(data.student_id))
        
        # Create remark
        remark_data = {
            'id': str(uuid.uuid4()),
            'student_id': str(data.student_id),
            'class_id': str(data.class_id),
            'session_id': str(data.session_id),
            'term_id': str(data.term_id),
            'form_teacher_id': form_teacher_id,
            'remark_text': data.remark_text,
            'remarks_category': data.remarks_category,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.table('student_remarks').insert(remark_data).execute()
        
        if not response.data:
            raise DatabaseError("Failed to create student remark")
        
        # Enrich response
        result = response.data[0]
        result['student_name'] = f"{student.data[0]['first_name']} {student.data[0]['last_name']}"
        
        teacher = supabase.table('teachers').select('first_name, last_name').eq('id', form_teacher_id).execute()
        if teacher.data:
            result['form_teacher_name'] = f"{teacher.data[0]['first_name']} {teacher.data[0]['last_name']}"
        
        logger.info(f"Created student remark {result['id']}")
        return result
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error creating student remark: {e}")
        raise DatabaseError(f"Failed to create student remark: {str(e)}")


@router.get("/remarks/student/{student_id}", response_model=List[StudentRemarkResponse])
def get_student_remarks(
    request: Request,
    student_id: UUID,
    session_id: Optional[UUID] = None,
    term_id: Optional[UUID] = None
):
    """Get all remarks for a student."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify student exists
        student = supabase.table('students').select('first_name, last_name').eq(
            'id', str(student_id)
        ).eq('organization_id', user["school_id"]).execute()
        
        if not student.data:
            raise NotFoundError("Student", str(student_id))
        
        query = supabase.table('student_remarks').select('*').eq('student_id', str(student_id))
        
        if session_id:
            query = query.eq('session_id', str(session_id))
        
        if term_id:
            query = query.eq('term_id', str(term_id))
        
        query = query.order('created_at', desc=True)
        response = query.execute()
        
        remarks = response.data or []
        student_name = f"{student.data[0]['first_name']} {student.data[0]['last_name']}"
        
        # Enrich with teacher names
        for remark in remarks:
            remark['student_name'] = student_name
            teacher = supabase.table('teachers').select('first_name, last_name').eq(
                'id', remark['form_teacher_id']
            ).execute()
            if teacher.data:
                remark['form_teacher_name'] = f"{teacher.data[0]['first_name']} {teacher.data[0]['last_name']}"
        
        return remarks
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting student remarks: {e}")
        raise DatabaseError(f"Failed to get student remarks: {str(e)}")


@router.get("/remarks/class/{class_id}", response_model=List[StudentRemarkResponse])
def get_class_remarks(
    request: Request,
    class_id: UUID,
    session_id: Optional[UUID] = None,
    term_id: Optional[UUID] = None
):
    """Get all remarks for a class. Form teacher or admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_form_teacher_or_admin(user, str(class_id))
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        query = supabase.table('student_remarks').select('*').eq('class_id', str(class_id))
        
        if session_id:
            query = query.eq('session_id', str(session_id))
        
        if term_id:
            query = query.eq('term_id', str(term_id))
        
        query = query.order('created_at', desc=True)
        response = query.execute()
        
        remarks = response.data or []
        
        # Enrich with student and teacher names
        for remark in remarks:
            student = supabase.table('students').select('first_name, last_name').eq(
                'id', remark['student_id']
            ).execute()
            if student.data:
                remark['student_name'] = f"{student.data[0]['first_name']} {student.data[0]['last_name']}"
            
            teacher = supabase.table('teachers').select('first_name, last_name').eq(
                'id', remark['form_teacher_id']
            ).execute()
            if teacher.data:
                remark['form_teacher_name'] = f"{teacher.data[0]['first_name']} {teacher.data[0]['last_name']}"
        
        return remarks
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting class remarks: {e}")
        raise DatabaseError(f"Failed to get class remarks: {str(e)}")


@router.put("/remarks/{remark_id}", response_model=StudentRemarkResponse)
def update_student_remark(request: Request, remark_id: UUID, data: StudentRemarkUpdate):
    """Update a student remark. Form teacher or admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify remark exists
        existing = supabase.table('student_remarks').select('*').eq('id', str(remark_id)).execute()
        
        if not existing.data:
            raise NotFoundError("Student remark", str(remark_id))
        
        remark = existing.data[0]

        # Check authorization - only the form teacher who wrote the remark,
        # or an admin, may edit it. Any other role (bursar/parent/student)
        # must be rejected explicitly rather than silently falling through.
        if user.get("role") == "teacher":
            if remark['form_teacher_id'] != user.get("teacher_id"):
                raise AuthorizationError("You can only edit your own remarks")
        elif user.get("role") not in ["admin", "system_admin"]:
            raise AuthorizationError("Only the form teacher or an admin can edit remarks")

        # Update remark
        update_data = data.model_dump(mode="json", exclude_unset=True)
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            response = supabase.table('student_remarks').update(update_data).eq(
                'id', str(remark_id)
            ).execute()
            
            if not response.data:
                raise DatabaseError("Failed to update student remark")
            
            logger.info(f"Updated student remark {remark_id}")
            return response.data[0]
        
        return remark
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating student remark: {e}")
        raise DatabaseError(f"Failed to update student remark: {str(e)}")


@router.delete("/remarks/{remark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_remark(request: Request, remark_id: UUID):
    """Delete a student remark. Form teacher or admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify remark exists
        existing = supabase.table('student_remarks').select('form_teacher_id').eq(
            'id', str(remark_id)
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Student remark", str(remark_id))
        
        # Check authorization - same rule as update: form teacher (own
        # remarks only) or admin; everyone else is rejected explicitly.
        if user.get("role") == "teacher":
            if existing.data[0]['form_teacher_id'] != user.get("teacher_id"):
                raise AuthorizationError("You can only delete your own remarks")
        elif user.get("role") not in ["admin", "system_admin"]:
            raise AuthorizationError("Only the form teacher or an admin can delete remarks")

        supabase.table('student_remarks').delete().eq('id', str(remark_id)).execute()
        
        logger.info(f"Deleted student remark {remark_id}")
        return None
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting student remark: {e}")
        raise DatabaseError(f"Failed to delete student remark: {str(e)}")


# ============================================
# SCHOOL REPORTS ENDPOINTS
# ============================================

@router.post("/reports", response_model=SchoolReportResponse, status_code=status.HTTP_201_CREATED)
def create_school_report(request: Request, data: SchoolReportCreate):
    """Create and send school report to parents. Form teacher or admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Determine form teacher
        form_teacher_id = None
        if user.get("role") == "teacher" and user.get("teacher_id"):
            # Verify user is form teacher of this class
            assignment = supabase.table('teacher_class_assignments').select('id').eq(
                'teacher_id', user["teacher_id"]
            ).eq('class_id', str(data.class_id)).eq(
                'session_id', str(data.session_id)
            ).eq('is_form_teacher', True).execute()
            
            if not assignment.data:
                raise AuthorizationError("You are not the form teacher of this class")
            
            form_teacher_id = user["teacher_id"]
        elif user.get("role") in ["admin", "system_admin"]:
            # Get the form teacher for this class
            assignment = supabase.table('teacher_class_assignments').select('teacher_id').eq(
                'class_id', str(data.class_id)
            ).eq('session_id', str(data.session_id)).eq('is_form_teacher', True).execute()
            
            if assignment.data:
                form_teacher_id = assignment.data[0]['teacher_id']
            else:
                raise ValidationError("This class does not have a form teacher assigned")
        
        if not form_teacher_id:
            raise AuthorizationError("Unable to determine form teacher")
        
        # Create report
        report_data = {
            'id': str(uuid.uuid4()),
            'organization_id': user["school_id"],
            'class_id': str(data.class_id),
            'session_id': str(data.session_id),
            'term_id': str(data.term_id),
            'report_type': data.report_type,
            'form_teacher_id': form_teacher_id,
            'created_by': user["user_id"],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        report_response = supabase.table('school_reports').insert(report_data).execute()
        
        if not report_response.data:
            raise DatabaseError("Failed to create school report")
        
        report_id = report_response.data[0]['id']
        
        # Create recipients
        recipients_data = []
        for parent_id in data.parent_ids:
            # Get student ID from parent-student relationship
            parent_student = supabase.table('parent_student_relationships').select('student_id').eq(
                'parent_id', str(parent_id)
            ).execute()
            
            student_id = parent_student.data[0]['student_id'] if parent_student.data else None
            
            recipients_data.append({
                'id': str(uuid.uuid4()),
                'report_id': report_id,
                'parent_id': str(parent_id),
                'student_id': student_id,
                'delivery_status': 'pending',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            })
        
        if recipients_data:
            recipients_response = supabase.table('school_report_recipients').insert(
                recipients_data
            ).execute()
        
        # Fetch complete report
        result = report_response.data[0]
        
        # Get class name
        cls = supabase.table('classes').select('name').eq('id', result['class_id']).execute()
        if cls.data:
            result['class_name'] = cls.data[0]['name']
        
        # Get form teacher name
        teacher = supabase.table('teachers').select('first_name, last_name').eq('id', form_teacher_id).execute()
        if teacher.data:
            result['form_teacher_name'] = f"{teacher.data[0]['first_name']} {teacher.data[0]['last_name']}"
        
        result['recipients'] = recipients_data
        
        logger.info(f"Created school report {report_id}")
        return result
        
    except (AuthorizationError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error creating school report: {e}")
        raise DatabaseError(f"Failed to create school report: {str(e)}")


@router.get("/reports", response_model=List[SchoolReportResponse])
def list_school_reports(
    request: Request,
    class_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
    term_id: Optional[UUID] = None,
    report_type: Optional[str] = None
):
    """List school reports with filters."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        query = supabase.table('school_reports').select('*').eq(
            'organization_id', user["school_id"]
        )
        
        if class_id:
            query = query.eq('class_id', str(class_id))
        
        if session_id:
            query = query.eq('session_id', str(session_id))
        
        if term_id:
            query = query.eq('term_id', str(term_id))
        
        if report_type:
            query = query.eq('report_type', report_type)
        
        query = query.order('created_at', desc=True)
        response = query.execute()
        
        reports = response.data or []
        
        # Enrich with details
        for report in reports:
            # Get class name
            cls = supabase.table('classes').select('name').eq('id', report['class_id']).execute()
            if cls.data:
                report['class_name'] = cls.data[0]['name']
            
            # Get form teacher name
            teacher = supabase.table('teachers').select('first_name, last_name').eq(
                'id', report['form_teacher_id']
            ).execute()
            if teacher.data:
                report['form_teacher_name'] = f"{teacher.data[0]['first_name']} {teacher.data[0]['last_name']}"
            
            # Get recipients count
            recipients = supabase.table('school_report_recipients').select('id').eq(
                'report_id', report['id']
            ).execute()
            report['recipient_count'] = len(recipients.data) if recipients.data else 0
        
        return reports
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing school reports: {e}")
        raise DatabaseError(f"Failed to list school reports: {str(e)}")


@router.get("/reports/{report_id}", response_model=SchoolReportResponse)
def get_school_report(request: Request, report_id: UUID):
    """Get a specific school report with recipients."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        response = supabase.table('school_reports').select('*').eq(
            'id', str(report_id)
        ).eq('organization_id', user["school_id"]).execute()
        
        if not response.data:
            raise NotFoundError("School report", str(report_id))
        
        report = response.data[0]
        
        # Get recipients
        recipients = supabase.table('school_report_recipients').select('*').eq(
            'report_id', str(report_id)
        ).execute()
        
        # Enrich recipients
        enriched_recipients = []
        for recipient in recipients.data or []:
            parent = supabase.table('parents').select('first_name, last_name').eq(
                'id', recipient['parent_id']
            ).execute()
            if parent.data:
                recipient['parent_name'] = f"{parent.data[0]['first_name']} {parent.data[0]['last_name']}"
            
            if recipient['student_id']:
                student = supabase.table('students').select('first_name, last_name').eq(
                    'id', recipient['student_id']
                ).execute()
                if student.data:
                    recipient['student_name'] = f"{student.data[0]['first_name']} {student.data[0]['last_name']}"
            
            enriched_recipients.append(recipient)
        
        report['recipients'] = enriched_recipients
        
        # Get class name
        cls = supabase.table('classes').select('name').eq('id', report['class_id']).execute()
        if cls.data:
            report['class_name'] = cls.data[0]['name']
        
        # Get form teacher name
        teacher = supabase.table('teachers').select('first_name, last_name').eq(
            'id', report['form_teacher_id']
        ).execute()
        if teacher.data:
            report['form_teacher_name'] = f"{teacher.data[0]['first_name']} {teacher.data[0]['last_name']}"
        
        return report
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting school report: {e}")
        raise DatabaseError(f"Failed to get school report: {str(e)}")


@router.post("/reports/bulk-send", response_model=SchoolReportResponse, status_code=status.HTTP_201_CREATED)
def bulk_send_reports(request: Request, data: BulkReportSend):
    """Send reports to all parents of students in a class. Form teacher or admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        parent_ids = []
        
        if data.include_all_parents:
            # Get all students in the class
            students = supabase.table('students').select('id').eq(
                'current_class_id', str(data.class_id)
            ).eq('organization_id', user["school_id"]).execute()
            
            # Get all parents of these students
            for student in students.data or []:
                parents = supabase.table('parent_student_relationships').select('parent_id').eq(
                    'student_id', student['id']
                ).execute()
                parent_ids.extend([p['parent_id'] for p in parents.data or []])
            
            # Remove duplicates
            parent_ids = list(set(parent_ids))
        else:
            parent_ids = [str(pid) for pid in data.parent_ids or []]
        
        if not parent_ids:
            raise ValidationError("No parents found to send reports to")
        
        # Create report using existing endpoint logic
        report_data = SchoolReportCreate(
            class_id=data.class_id,
            session_id=data.session_id,
            term_id=data.term_id,
            report_type=data.report_type,
            parent_ids=[UUID(pid) for pid in parent_ids]
        )
        
        return create_school_report(request, report_data)
        
    except (AuthorizationError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error bulk sending reports: {e}")
        raise DatabaseError(f"Failed to bulk send reports: {str(e)}")


logger.info("Phase 4 Teacher Management endpoints loaded successfully")
