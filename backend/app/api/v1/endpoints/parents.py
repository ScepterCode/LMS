"""
Parents API endpoints.
Handles CRUD operations for parents and parent-student links.
"""

from fastapi import APIRouter, Request, status, Query
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid
import logging

from app.models.parent import (
    ParentCreate,
    ParentUpdate,
    ParentResponse,
    ParentStudentLinkCreate,
    ParentStudentLinkResponse
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
    """Ensure user is school admin, system admin, dean, or registrar."""
    if user.get("role") not in ["admin", "system_admin", "dean", "registrar"]:
        raise AuthorizationError("Insufficient permissions to manage parents")


# ============================================
# PARENT ENDPOINTS
# ============================================

@router.get("", response_model=List[ParentResponse])
def list_parents(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search by name or email")
):
    """List all parents for the user's organization."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        # A parent has no legitimate reason to browse the school's whole
        # parent directory - unlike students, there's no "my own parents"
        # subset to scope this down to, so it's simply not their endpoint.
        if user.get("role") == "parent":
            raise AuthorizationError("You do not have permission to list parents")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        query = supabase.table('parents').select('*').eq('organization_id', user["school_id"])

        if search:
            query = query.or_(f'first_name.ilike.%{search}%,last_name.ilike.%{search}%,email.ilike.%{search}%')
        
        query = query.order('last_name').order('first_name').range(skip, skip + limit - 1)
        response = query.execute()

        # Batch children counts in one query instead of one per parent
        # (was causing N+1 slowdowns on this page).
        parent_ids = [p['id'] for p in response.data]
        children_counts: dict = {}
        if parent_ids:
            links = supabase.table('parent_student_links').select('parent_id').in_(
                'parent_id', parent_ids
            ).execute()
            for row in (links.data or []):
                children_counts[row['parent_id']] = children_counts.get(row['parent_id'], 0) + 1

        # Enrich data
        enriched_data = []
        for parent in response.data:
            # Add full name
            parent['full_name'] = f"{parent.get('title') or ''} {parent['first_name']} {parent['last_name']}".strip()
            parent['children_count'] = children_counts.get(parent['id'], 0)
            enriched_data.append(parent)
        
        logger.info(f"Listed {len(enriched_data)} parents for org {user['school_id']}")
        return enriched_data
        
    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing parents: {e}")
        raise DatabaseError(f"Failed to list parents: {str(e)}")


@router.post("", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
def create_parent(request: Request, data: ParentCreate):
    """Register a new parent. Only admins can register parents."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Check if user_id already has a parent record
        user_check = supabase.table('parents').select('id').eq(
            'user_id', str(data.user_id)
        ).execute()
        
        if user_check.data:
            raise ValidationError("This user already has a parent record")
        
        # Verify user exists and belongs to organization
        user_verify = supabase.table('users').select('id, school_id, role').eq(
            'id', str(data.user_id)
        ).execute()

        if not user_verify.data:
            raise ValidationError("Invalid user ID")

        if user_verify.data[0]['school_id'] != str(user["school_id"]):
            raise ValidationError("User must belong to your organization")
        
        # Create parent
        parent_data = {
            'id': str(uuid.uuid4()),
            'user_id': str(data.user_id),
            'organization_id': str(user["school_id"]),
            'title': data.title,
            'first_name': data.first_name,
            'last_name': data.last_name,
            'phone': data.phone,
            'email': data.email,
            'occupation': data.occupation,
            'address': data.address,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('parents').insert(parent_data).execute()
        
        if not result.data:
            raise DatabaseError("Failed to create parent")
        
        logger.info(f"Created parent: {data.email} for org {user['school_id']}")
        
        created_parent = result.data[0]
        created_parent['full_name'] = f"{data.title or ''} {data.first_name} {data.last_name}".strip()
        created_parent['children_count'] = 0
        
        return created_parent
        
    except (AuthorizationError, ValidationError, DatabaseError, DuplicateRecordError):
        raise
    except Exception as e:
        logger.error(f"Error creating parent: {e}")
        raise DatabaseError(f"Failed to create parent: {str(e)}")


@router.get("/me/children")
def get_my_children(request: Request):
    """
    Get the calling parent's own linked children. Parent-only self-service
    endpoint - avoids the parent needing to know their own parent_id, and
    sidesteps the id-guessing risk of the equivalent /{parent_id}/children
    route entirely for this common case.

    Declared before /{parent_id} below: FastAPI matches path routes in
    registration order, and a literal "/me/children" would otherwise be
    swallowed by the "{parent_id}" pattern (with parent_id="me"), which
    would then fail UUID validation instead of ever reaching this handler.
    """
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)

        if user.get("role") != "parent":
            raise AuthorizationError("Only parent accounts have a children list")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        parent = supabase.table('parents').select('id').eq('user_id', user["id"]).execute()
        if not parent.data:
            return []
        parent_id = parent.data[0]['id']

        links = supabase.table('parent_student_links').select('*').eq('parent_id', parent_id).execute()

        enriched_data = []
        for link in links.data:
            student = supabase.table('students').select(
                'first_name, middle_name, last_name, admission_number, current_class_id'
            ).eq('id', link['student_id']).execute()

            if student.data:
                s = student.data[0]
                link['student_name'] = f"{s['first_name']} {s.get('middle_name') or ''} {s['last_name']}".replace('  ', ' ')
                link['admission_number'] = s.get('admission_number')

                if s.get('current_class_id'):
                    class_response = supabase.table('classes').select('name').eq('id', s['current_class_id']).execute()
                    if class_response.data:
                        link['class_name'] = class_response.data[0]['name']

            enriched_data.append(link)

        return enriched_data

    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting own children: {e}")
        raise DatabaseError(f"Failed to get children: {str(e)}")


@router.get("/{parent_id}", response_model=ParentResponse)
def get_parent(request: Request, parent_id: UUID):
    """Get parent by ID with full details."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)

        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        response = supabase.table('parents').select('*').eq('id', str(parent_id)).eq(
            'organization_id', user["school_id"]
        ).execute()

        if not response.data:
            raise NotFoundError("Parent", parent_id)

        # A parent may only view their own record, never another parent's.
        # Staff roles are unrestricted, unchanged from prior behavior.
        if user.get("role") == "parent" and response.data[0].get("user_id") != user["id"]:
            raise AuthorizationError("You can only view your own parent record")

        parent = response.data[0]
        
        # Enrich data
        parent['full_name'] = f"{parent.get('title') or ''} {parent['first_name']} {parent['last_name']}".strip()
        
        # Count children
        children = supabase.table('parent_student_links').select('id', count='exact').eq(
            'parent_id', parent['id']
        ).execute()
        parent['children_count'] = children.count if hasattr(children, 'count') else len(children.data) if children.data else 0
        
        return parent
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting parent: {e}")
        raise DatabaseError(f"Failed to get parent: {str(e)}")


@router.put("/{parent_id}", response_model=ParentResponse)
def update_parent(request: Request, parent_id: UUID, data: ParentUpdate):
    """Update parent details. Only admins can update."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        existing = supabase.table('parents').select('*').eq('id', str(parent_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Parent", parent_id)
        
        update_data = {k: v for k, v in data.model_dump(mode="json", exclude_unset=True).items() if v is not None}
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = supabase.table('parents').update(update_data).eq('id', str(parent_id)).execute()
            
            if not result.data:
                raise DatabaseError("Failed to update parent")
            
            logger.info(f"Updated parent: {parent_id}")
            
            updated_parent = result.data[0]
            updated_parent['full_name'] = f"{updated_parent.get('title') or ''} {updated_parent['first_name']} {updated_parent['last_name']}".strip()
            
            return updated_parent
        
        return existing.data[0]
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating parent: {e}")
        raise DatabaseError(f"Failed to update parent: {str(e)}")


@router.delete("/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parent(request: Request, parent_id: UUID):
    """Delete parent. Only admins can delete parents."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        existing = supabase.table('parents').select('*').eq('id', str(parent_id)).eq(
            'organization_id', user["school_id"]
        ).execute()
        
        if not existing.data:
            raise NotFoundError("Parent", parent_id)
        
        # Check for dependencies
        links = supabase.table('parent_student_links').select('id', count='exact').eq(
            'parent_id', str(parent_id)
        ).execute()
        
        if links.data:
            raise ValidationError(
                f"Cannot delete parent with {len(links.data)} linked children. "
                "Remove links first."
            )
        
        supabase.table('parents').delete().eq('id', str(parent_id)).execute()
        
        logger.info(f"Deleted parent: {parent_id}")
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error deleting parent: {e}")
        raise DatabaseError(f"Failed to delete parent: {str(e)}")


@router.get("/{parent_id}/children")
def get_parent_children(request: Request, parent_id: UUID):
    """Get all children linked to a parent."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify parent exists and belongs to user's org
        parent_check = supabase.table('parents').select('id, user_id').eq('id', str(parent_id)).eq(
            'organization_id', user["school_id"]
        ).execute()

        if not parent_check.data:
            raise NotFoundError("Parent", parent_id)

        # A parent may only view their own children, never another parent's.
        if user.get("role") == "parent" and parent_check.data[0].get("user_id") != user["id"]:
            raise AuthorizationError("You can only view your own children")

        # Get links
        links = supabase.table('parent_student_links').select('*').eq('parent_id', str(parent_id)).execute()
        
        # Enrich with student details
        enriched_data = []
        for link in links.data:
            # Get student info
            student = supabase.table('students').select('first_name, middle_name, last_name, admission_number').eq(
                'id', link['student_id']
            ).execute()
            
            if student.data:
                link['student_name'] = f"{student.data[0]['first_name']} {student.data[0].get('middle_name') or ''} {student.data[0]['last_name']}".replace('  ', ' ')
                link['admission_number'] = student.data[0].get('admission_number')
            
            enriched_data.append(link)
        
        logger.info(f"Retrieved {len(enriched_data)} children for parent {parent_id}")
        return enriched_data
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting parent children: {e}")
        raise DatabaseError(f"Failed to get parent children: {str(e)}")


@router.post("/{parent_id}/children", status_code=status.HTTP_201_CREATED)
def link_parent_to_student(
    request: Request,
    parent_id: UUID,
    data: ParentStudentLinkCreate
):
    """
    Link a parent to a student (ward).
    Only admins can create parent-student links.
    """
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify parent exists and belongs to org
        parent_check = supabase.table('parents').select('id, organization_id').eq(
            'id', str(parent_id)
        ).execute()
        
        if not parent_check.data:
            raise NotFoundError("Parent", parent_id)
        
        if parent_check.data[0]['organization_id'] != user["school_id"]:
            raise AuthorizationError("Parent does not belong to your organization")
        
        # Verify student exists and belongs to org
        student_check = supabase.table('students').select('id, organization_id').eq(
            'id', str(data.student_id)
        ).execute()
        
        if not student_check.data:
            raise NotFoundError("Student", data.student_id)
        
        if student_check.data[0]['organization_id'] != user["school_id"]:
            raise AuthorizationError("Student does not belong to your organization")
        
        # Check if link already exists
        existing = supabase.table('parent_student_links').select('id').eq(
            'parent_id', str(parent_id)
        ).eq('student_id', str(data.student_id)).execute()
        
        if existing.data:
            raise ValidationError("This student is already linked to this parent")
        
        # Create link
        import uuid as uuid_module
        link_data = {
            'id': str(uuid_module.uuid4()),
            'parent_id': str(parent_id),
            'student_id': str(data.student_id),
            'relationship': data.relationship,
            'is_primary': data.is_primary,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        result = supabase.table('parent_student_links').insert(link_data).execute()
        
        if not result.data:
            raise DatabaseError("Failed to link parent to student")
        
        logger.info(f"Linked parent {parent_id} to student {data.student_id} as {data.relationship}")
        
        return result.data[0]
        
    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error linking parent to student: {e}")
        raise DatabaseError(f"Failed to link parent to student: {str(e)}")


@router.delete("/{parent_id}/children/{student_id}")
def unlink_parent_from_student(
    request: Request,
    parent_id: UUID,
    student_id: UUID
):
    """
    Unlink a parent from a student.
    Only admins can remove parent-student links.
    """
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_admin(user)
        
        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")
        
        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")
        
        # Verify parent belongs to user's org
        parent_check = supabase.table('parents').select('id, organization_id').eq(
            'id', str(parent_id)
        ).execute()
        
        if not parent_check.data:
            raise NotFoundError("Parent", parent_id)
        
        if parent_check.data[0]['organization_id'] != user["school_id"]:
            raise AuthorizationError("Parent does not belong to your organization")
        
        # Verify link exists
        link_check = supabase.table('parent_student_links').select('id').eq(
            'parent_id', str(parent_id)
        ).eq('student_id', str(student_id)).execute()
        
        if not link_check.data:
            raise NotFoundError("Parent-student link", f"{parent_id}-{student_id}")
        
        # Delete link
        result = supabase.table('parent_student_links').delete().eq(
            'parent_id', str(parent_id)
        ).eq('student_id', str(student_id)).execute()
        
        logger.info(f"Unlinked parent {parent_id} from student {student_id}")
        
        return {"message": "Parent-student link removed successfully"}
        
    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error unlinking parent from student: {e}")
        raise DatabaseError(f"Failed to unlink parent from student: {str(e)}")
