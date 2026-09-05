"""
Outbound email via Resend's HTTP API (https://resend.com).

No Resend SDK - it's a single POST endpoint, and adding the package
risked a dependency conflict with the httpx version pinned for
supabase-py. RESEND_API_KEY and EMAIL_FROM come from the environment;
with either unset, send_email() logs and returns False instead of
raising, so a request that also does a DB write (creating an account,
resetting a password, ...) never fails just because email isn't
configured.

Sending to real recipients requires a domain verified in the Resend
dashboard - without one, Resend only delivers to the account owner's
own address. Until RESEND_API_KEY/EMAIL_FROM are set (in Render's env
vars, not committed here), every send is a logged no-op.
"""
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


def send_email(to: str, subject: str, html: str, text: str | None = None) -> bool:
    """Best-effort send. Returns whether it was actually sent - callers
    should log/ignore a False, not treat it as a request failure."""
    if not settings.RESEND_API_KEY or not settings.EMAIL_FROM:
        logger.warning(f"Email not configured - skipped '{subject}' to {to}")
        return False

    payload = {
        "from": settings.EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text

    try:
        response = httpx.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            json=payload,
            timeout=10,
        )
        if response.status_code >= 400:
            logger.error(f"Resend API {response.status_code} sending '{subject}' to {to}: {response.text[:300]}")
            return False
        return True
    except httpx.HTTPError as e:
        logger.error(f"Failed to send '{subject}' to {to}: {e}")
        return False


def send_diagnostic_email(to: str, subject: str, html: str) -> dict:
    """Same send as send_email(), but returns *why* it did or didn't go out
    instead of a bare bool - for the system-admin "send test email" tool,
    where "nothing happened" isn't an actionable answer."""
    if not settings.RESEND_API_KEY or not settings.EMAIL_FROM:
        return {"sent": False, "detail": "RESEND_API_KEY and/or EMAIL_FROM is not set in this environment."}

    payload = {"from": settings.EMAIL_FROM, "to": [to], "subject": subject, "html": html}

    try:
        response = httpx.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            json=payload,
            timeout=10,
        )
        if response.status_code >= 400:
            return {"sent": False, "detail": f"Resend rejected it (HTTP {response.status_code}): {response.text[:500]}"}
        return {"sent": True, "detail": f"Sent via Resend to {to}."}
    except httpx.HTTPError as e:
        return {"sent": False, "detail": f"Could not reach Resend: {e}"}
