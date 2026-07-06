"""
Skill category and student skill rating endpoints.

Skill categories are an admin-configurable list of psychomotor/affective
domain traits (Sports, Handling of Tools, Punctuality, Neatness, etc.) that
appear on the report card. Form teachers rate each student on each active
trait per term - the same "form teacher of this class" permission used for
report card generation applies here.
"""

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid
import logging

from app.core.database import get_supabase
from app.core.security import get_current_user_from_token, get_token_from_request
from app.core.permissions import PermissionChecker
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    DatabaseError,
    AuthorizationError,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# MODELS
# ============================================

class SkillCategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    domain: str = Field(default="psychomotor")
    display_order: int = 0


class SkillCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    domain: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class SkillRatingEntry(BaseModel):
    skill_category_id: UUID
    rating: int = Field(..., ge=1, le=5)


class SkillRatingsBulkSubmit(BaseModel):
    student_id: UUID
    session_id: UUID
    term_id: UUID
    ratings: List[SkillRatingEntry]


def _require_admin(user: dict):
    if user.get("role") not in ["admin", "system_admin"]:
        raise AuthorizationError("Only school administrators can manage skill categories")


# ============================================
# SKILL CATEGORIES (admin-configurable)
# ============================================

@router.get("/categories")
async def list_skill_categories(request: Request, include_inactive: bool = False):
    """List this school's skill categories, grouped implicitly by domain."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)

        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        query = supabase.table('skill_categories').select('*').eq(
            'organization_id', user["school_id"]
        )
        if not include_inactive:
            query = query.eq('is_active', True)

        response = query.order('domain').order('display_order').execute()
        return response.data or []

    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing skill categories: {e}")
        raise DatabaseError(f"Failed to list skill categories: {str(e)}")


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_skill_category(request: Request, data: SkillCategoryCreate):
    """Create a new skill category. Admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        _require_admin(user)

        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        if data.domain not in ("psychomotor", "affective"):
            raise ValidationError("Domain must be 'psychomotor' or 'affective'")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        category_data = {
            'id': str(uuid.uuid4()),
            'organization_id': user["school_id"],
            'name': data.name,
            'domain': data.domain,
            'display_order': data.display_order,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
        }

        response = supabase.table('skill_categories').insert(category_data).execute()
        if not response.data:
            raise DatabaseError("Failed to create skill category")

        logger.info(f"Created skill category '{data.name}' for org {user['school_id']}")
        return response.data[0]

    except (AuthorizationError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error creating skill category: {e}")
        if 'duplicate' in str(e).lower() or '23505' in str(e):
            raise ValidationError(f"A skill category named '{data.name}' already exists")
        raise DatabaseError(f"Failed to create skill category: {str(e)}")


@router.patch("/categories/{category_id}")
async def update_skill_category(request: Request, category_id: UUID, data: SkillCategoryUpdate):
    """Update or deactivate a skill category. Admin only."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        _require_admin(user)

        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        existing = supabase.table('skill_categories').select('id').eq(
            'id', str(category_id)
        ).eq('organization_id', user["school_id"]).execute()

        if not existing.data:
            raise NotFoundError("Skill category", str(category_id))

        if data.domain and data.domain not in ("psychomotor", "affective"):
            raise ValidationError("Domain must be 'psychomotor' or 'affective'")

        update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            response = supabase.table('skill_categories').update(update_data).eq(
                'id', str(category_id)
            ).execute()
            if not response.data:
                raise DatabaseError("Failed to update skill category")
            return response.data[0]

        return existing.data[0]

    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error updating skill category: {e}")
        raise DatabaseError(f"Failed to update skill category: {str(e)}")


# ============================================
# STUDENT SKILL RATINGS
# ============================================

@router.get("/student/{student_id}")
async def get_student_skill_ratings(
    request: Request,
    student_id: UUID,
    session_id: UUID,
    term_id: UUID,
):
    """Get a student's skill ratings for a term, enriched with category name/domain."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)

        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        student = supabase.table('students').select('id').eq(
            'id', str(student_id)
        ).eq('organization_id', user["school_id"]).execute()

        if not student.data:
            raise NotFoundError("Student", str(student_id))

        response = supabase.table('student_skill_ratings').select(
            '*, skill_categories(name, domain)'
        ).eq('student_id', str(student_id)).eq(
            'session_id', str(session_id)
        ).eq('term_id', str(term_id)).execute()

        ratings = []
        for row in (response.data or []):
            category = row.pop('skill_categories', None) or {}
            ratings.append({
                **row,
                'category_name': category.get('name'),
                'domain': category.get('domain'),
            })

        return ratings

    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error getting student skill ratings: {e}")
        raise DatabaseError(f"Failed to get student skill ratings: {str(e)}")


@router.post("/ratings/bulk", status_code=status.HTTP_201_CREATED)
async def submit_skill_ratings(request: Request, data: SkillRatingsBulkSubmit):
    """
    Submit/update skill ratings for a student for a term.
    Only the form teacher of the student's current class (or an admin) may do this -
    the exact same permission check used for report card generation.
    """
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)

        if user.get("role") not in ["admin", "teacher"]:
            raise AuthorizationError("Only admins and teachers can submit skill ratings")

        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        student = supabase.table('students').select('current_class_id').eq(
            'id', str(data.student_id)
        ).eq('organization_id', user["school_id"]).execute()

        if not student.data:
            raise NotFoundError("Student", str(data.student_id))

        class_id = student.data[0]["current_class_id"]

        if user.get("role") == "teacher":
            teacher_id = user.get("teacher_id")
            try:
                await PermissionChecker.verify_form_teacher_permission(teacher_id, class_id, supabase)
            except AuthorizationError as e:
                raise AuthorizationError(f"Form teacher access required: {str(e)}")

        if not data.ratings:
            raise ValidationError("At least one rating must be provided")

        now = datetime.utcnow().isoformat()
        rows = [
            {
                'organization_id': user["school_id"],
                'student_id': str(data.student_id),
                'skill_category_id': str(entry.skill_category_id),
                'session_id': str(data.session_id),
                'term_id': str(data.term_id),
                'rating': entry.rating,
                'rated_by': user.get("teacher_id"),
                'updated_at': now,
            }
            for entry in data.ratings
        ]

        response = supabase.table('student_skill_ratings').upsert(
            rows, on_conflict="student_id,skill_category_id,term_id,session_id"
        ).execute()

        if not response.data:
            raise DatabaseError("Failed to save skill ratings")

        logger.info(f"Saved {len(response.data)} skill ratings for student {data.student_id}")
        return {"message": f"Saved {len(response.data)} skill ratings", "ratings": response.data}

    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error submitting skill ratings: {e}")
        raise DatabaseError(f"Failed to submit skill ratings: {str(e)}")
