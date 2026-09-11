"""
End-of-session promotion / graduation API endpoints.

Two-step flow:
  1. GET /promotions/preview?session_id=... computes a default promote /
     repeat / graduate decision for every active student, from that
     session's promotion_basis + promotion_pass_mark. Nothing is saved.
  2. POST /promotions/commit takes the admin's final (possibly edited)
     list of decisions and applies them: moves students to their next
     class, marks graduates, and writes a permanent promotion_records
     row for each student, one per session.
"""

from fastapi import APIRouter, Request
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import logging

from app.models.promotion import (
    PromotionPreviewResponse,
    PromotionPreviewRow,
    PromotionCommitRequest,
    PromotionCommitResponse,
    PromotionCommitResultRow,
    PromotionRecordResponse,
)
from app.core.database import get_supabase
from app.core.security import get_current_user_from_token, get_token_from_request
from app.core.audit import log_audit_event
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    DatabaseError,
    AuthorizationError,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def require_school_admin(user: dict):
    """Ensure user is school admin, system admin, or dean."""
    if not user:
        raise AuthorizationError("User authentication failed - no valid user found")
    if user.get("role") not in ["admin", "system_admin", "dean"]:
        raise AuthorizationError("Only school administrators can manage promotions")


def _load_session(supabase, organization_id: str, session_id: str) -> dict:
    result = supabase.table("academic_sessions").select("*").eq(
        "id", session_id
    ).eq("organization_id", organization_id).execute()
    if not result.data:
        raise NotFoundError("Academic Session", session_id)
    return result.data[0]


def _compute_promotion_rows(supabase, organization_id: str, session: dict) -> List[dict]:
    session_id = str(session["id"])
    promotion_basis = session.get("promotion_basis") or "third_term"
    pass_mark = float(session.get("promotion_pass_mark") or 40.0)

    terms = supabase.table("terms").select("id, term_number").eq(
        "session_id", session_id
    ).execute().data
    term_ids = [t["id"] for t in terms]
    third_term = next((t for t in terms if t.get("term_number") == 3), None)

    classes = supabase.table("classes").select(
        "id, name, sequence_order, is_graduating_class"
    ).eq("organization_id", organization_id).execute().data
    classes_by_id = {c["id"]: c for c in classes}
    ordered = sorted(
        (c for c in classes if c.get("sequence_order") is not None),
        key=lambda c: c["sequence_order"],
    )
    next_class_by_id = {}
    for idx, cls in enumerate(ordered):
        if idx + 1 < len(ordered):
            next_class_by_id[cls["id"]] = ordered[idx + 1]

    students = supabase.table("students").select(
        "id, first_name, last_name, admission_number, current_class_id"
    ).eq("organization_id", organization_id).eq("status", "active").execute().data
    students = [s for s in students if s.get("current_class_id")]
    student_ids = [s["id"] for s in students]

    report_cards = []
    if student_ids and term_ids:
        report_cards = supabase.table("report_cards").select(
            "student_id, term_id, average_score"
        ).eq("session_id", session_id).in_("student_id", student_ids).execute().data

    cards_by_student: dict = {}
    for rc in report_cards:
        cards_by_student.setdefault(rc["student_id"], {})[rc["term_id"]] = rc.get("average_score")

    rows = []
    for s in students:
        cls = classes_by_id.get(s["current_class_id"])
        if not cls:
            # Student's current class no longer exists / belongs to another
            # org's data - skip defensively rather than guess.
            continue

        student_cards = cards_by_student.get(s["id"], {})
        basis_score = None
        has_data = False

        if promotion_basis == "third_term":
            if third_term and student_cards.get(third_term["id"]) is not None:
                basis_score = float(student_cards[third_term["id"]])
                has_data = True
        else:  # cumulative
            scores = [float(v) for v in student_cards.values() if v is not None]
            if scores:
                basis_score = sum(scores) / len(scores)
                has_data = True

        if not has_data:
            # No score to promote on - default to "repeated" as the safe
            # choice; the admin sees has_data=False and must confirm or
            # override with real information.
            decision = "repeated"
        elif basis_score >= pass_mark:
            decision = "graduated" if cls.get("is_graduating_class") else "promoted"
        else:
            decision = "repeated"

        to_class = next_class_by_id.get(cls["id"]) if decision == "promoted" else None

        rows.append({
            "student_id": s["id"],
            "student_name": f"{s['first_name']} {s['last_name']}",
            "admission_number": s["admission_number"],
            "from_class_id": cls["id"],
            "from_class_name": cls["name"],
            "basis_score": basis_score,
            "pass_mark": pass_mark,
            "has_data": has_data,
            "decision": decision,
            "to_class_id": to_class["id"] if to_class else None,
            "to_class_name": to_class["name"] if to_class else None,
            "is_graduating_class": bool(cls.get("is_graduating_class")),
        })

    rows.sort(key=lambda r: (r["from_class_name"], r["student_name"]))
    return rows


@router.get("/preview", response_model=PromotionPreviewResponse)
def preview_promotions(request: Request, session_id: UUID):
    """Compute (without saving) the default promotion outcome for every
    active student, based on the session's promotion policy."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)

        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        organization_id = str(user["school_id"])
        session = _load_session(supabase, organization_id, str(session_id))
        rows = _compute_promotion_rows(supabase, organization_id, session)

        return PromotionPreviewResponse(
            session_id=session_id,
            promotion_basis=session.get("promotion_basis") or "third_term",
            default_pass_mark=float(session.get("promotion_pass_mark") or 40.0),
            rows=[PromotionPreviewRow(**row) for row in rows],
        )

    except (AuthorizationError, NotFoundError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error computing promotion preview: {e}")
        raise DatabaseError(f"Failed to compute promotion preview: {str(e)}")


@router.post("/commit", response_model=PromotionCommitResponse)
def commit_promotions(request: Request, data: PromotionCommitRequest):
    """Apply the admin's final list of promotion decisions.

    Moves each student to their new class (or marks them graduated),
    and records a permanent promotion_records row. One row per row in
    the request; a single bad row is reported as a failure rather than
    aborting the whole batch, matching the existing bulk-action pattern
    used elsewhere (e.g. fee bulk actions).
    """
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)

        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        organization_id = str(user["school_id"])
        session = _load_session(supabase, organization_id, str(data.session_id))
        default_pass_mark = float(session.get("promotion_pass_mark") or 40.0)

        counts = {"promoted": 0, "repeated": 0, "graduated": 0, "failed": 0}
        results = []

        for row in data.decisions:
            try:
                if row.decision not in ("promoted", "repeated", "graduated"):
                    raise ValueError("decision must be 'promoted', 'repeated', or 'graduated'")

                student = supabase.table("students").select("id, current_class_id").eq(
                    "id", str(row.student_id)
                ).eq("organization_id", organization_id).execute()
                if not student.data:
                    raise ValueError("Student not found in your school")
                from_class_id = student.data[0].get("current_class_id")

                to_class_id = None
                new_status = None

                if row.decision == "promoted":
                    if not row.to_class_id:
                        raise ValueError("to_class_id is required to promote a student")
                    target = supabase.table("classes").select("id").eq(
                        "id", str(row.to_class_id)
                    ).eq("organization_id", organization_id).execute()
                    if not target.data:
                        raise ValueError("Target class not found in your school")
                    to_class_id = str(row.to_class_id)
                elif row.decision == "graduated":
                    new_status = "graduated"
                # "repeated": student stays in from_class_id, nothing to change there.

                update_fields = {}
                if to_class_id:
                    update_fields["current_class_id"] = to_class_id
                if new_status:
                    update_fields["status"] = new_status
                if update_fields:
                    update_fields["updated_at"] = datetime.utcnow().isoformat()
                    supabase.table("students").update(update_fields).eq(
                        "id", str(row.student_id)
                    ).execute()

                # One promotion decision per student per session - replace
                # any existing row rather than erroring on a re-run.
                supabase.table("promotion_records").delete().eq(
                    "student_id", str(row.student_id)
                ).eq("session_id", str(data.session_id)).execute()

                supabase.table("promotion_records").insert({
                    "organization_id": organization_id,
                    "session_id": str(data.session_id),
                    "student_id": str(row.student_id),
                    "from_class_id": from_class_id,
                    "to_class_id": to_class_id,
                    "decision": row.decision,
                    "basis_score": row.basis_score,
                    "pass_mark_used": default_pass_mark,
                    "overridden": bool(row.override_reason),
                    "override_reason": row.override_reason,
                    "decided_by": user.get("id"),
                    "created_at": datetime.utcnow().isoformat(),
                }).execute()

                counts[row.decision] += 1
                results.append(PromotionCommitResultRow(
                    student_id=row.student_id, decision=row.decision, success=True
                ))

            except Exception as e:
                counts["failed"] += 1
                logger.warning(f"Promotion failed for student {row.student_id}: {e}")
                results.append(PromotionCommitResultRow(
                    student_id=row.student_id, decision=row.decision,
                    success=False, error=str(e),
                ))

        log_audit_event(
            supabase, user, "promotions.commit",
            target_type="academic_session", target_id=str(data.session_id),
            target_organization_id=organization_id,
            details={
                "promoted": counts["promoted"],
                "repeated": counts["repeated"],
                "graduated": counts["graduated"],
                "failed": counts["failed"],
            },
        )

        logger.info(
            f"Promotions committed for session {data.session_id} by {user.get('email')}: {counts}"
        )

        return PromotionCommitResponse(session_id=data.session_id, results=results, **counts)

    except (AuthorizationError, NotFoundError, ValidationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error committing promotions: {e}")
        raise DatabaseError(f"Failed to commit promotions: {str(e)}")


@router.get("/history", response_model=List[PromotionRecordResponse])
def get_promotion_history(
    request: Request,
    session_id: Optional[UUID] = None,
    student_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 200,
):
    """List past promotion decisions, most recent first."""
    try:
        token = get_token_from_request(request)
        user = get_current_user_from_token(token)
        require_school_admin(user)

        if not user.get("school_id"):
            raise AuthorizationError("User must belong to a school")

        supabase = get_supabase()
        if not supabase:
            raise DatabaseError("Database connection not available")

        query = supabase.table("promotion_records").select("*").eq(
            "organization_id", str(user["school_id"])
        )
        if session_id:
            query = query.eq("session_id", str(session_id))
        if student_id:
            query = query.eq("student_id", str(student_id))

        query = query.order("created_at", desc=True).range(skip, skip + limit - 1)
        response = query.execute()

        return response.data

    except (AuthorizationError, DatabaseError):
        raise
    except Exception as e:
        logger.error(f"Error listing promotion history: {e}")
        raise DatabaseError(f"Failed to list promotion history: {str(e)}")
