"""
Platform audit logging.

log_audit_event() is deliberately best-effort: a failure here must
never break the action it's attached to (suspending a school, editing
a user, etc.). Any exception is caught and logged as a warning, not
raised.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def log_audit_event(
    supabase,
    actor: dict,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    target_organization_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Record a platform audit event. Never raises.

    actor is a current_user-shaped dict (id, email, role) as returned
    by get_current_user_from_token/require_system_admin.
    """
    try:
        supabase.table("audit_logs").insert({
            "actor_user_id": actor.get("id"),
            "actor_email": actor.get("email"),
            "actor_role": actor.get("role"),
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "target_organization_id": target_organization_id,
            "details": details or {},
        }).execute()
    except Exception as e:
        logger.warning(f"Failed to write audit log for action '{action}': {e}")
