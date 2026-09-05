"""
HTML builders for outbound emails. Plain f-strings rather than a
templating engine - the set of emails is small and none of them have
loops/conditionals complex enough to need one.
"""

_BRAND = "#2563eb"


def _wrapper(preheader: str, body_html: str) -> str:
    """Shared shell: brand header, one content block, footer. `preheader`
    is the hidden preview text most mail clients show next to the subject."""
    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <span style="display:none;font-size:1px;color:#f3f4f6;">{preheader}</span>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;max-width:480px;width:100%;">
        <tr><td style="background:{_BRAND};padding:20px 28px;">
          <span style="color:#ffffff;font-size:18px;font-weight:700;">Learnlyf</span>
        </td></tr>
        <tr><td style="padding:28px;color:#1f2937;font-size:15px;line-height:1.6;">
          {body_html}
        </td></tr>
        <tr><td style="padding:16px 28px;background:#f9fafb;color:#9ca3af;font-size:12px;">
          You're receiving this because you have an account on Learnlyf. If this wasn't you, you can ignore this email.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _button(label: str, url: str) -> str:
    return (
        f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:20px 0;">'
        f'<tr><td style="border-radius:8px;background:{_BRAND};">'
        f'<a href="{url}" style="display:inline-block;padding:12px 22px;color:#ffffff;'
        f'text-decoration:none;font-weight:600;font-size:14px;">{label}</a>'
        f'</td></tr></table>'
    )


def password_reset_email(name: str, reset_link: str) -> tuple[str, str]:
    subject = "Reset your Learnlyf password"
    body = f"""\
    <p>Hi {name},</p>
    <p>Someone asked to reset the password on your Learnlyf account. If that was you, choose a new password here - this link expires in 30 minutes:</p>
    {_button("Reset password", reset_link)}
    <p style="color:#6b7280;font-size:13px;">If you didn't request this, you can ignore this email - your password won't change.</p>
    """
    return subject, _wrapper("Reset your Learnlyf password", body)


def welcome_email(name: str, email: str, role_label: str, school_name: str, login_link: str) -> tuple[str, str]:
    subject = f"Your Learnlyf account is ready"
    body = f"""\
    <p>Hi {name},</p>
    <p>An account was created for you at <strong>{school_name}</strong> on Learnlyf, as <strong>{role_label}</strong>.</p>
    <p>Your login email is <strong>{email}</strong>. If you don't already have a password from your administrator, set one now:</p>
    {_button("Set your password", login_link)}
    <p style="color:#6b7280;font-size:13px;">That link takes you to Learnlyf's sign-in page, where you can choose "Forgot password" to set your first password.</p>
    """
    return subject, _wrapper(f"Your {school_name} account on Learnlyf is ready", body)


def test_email(sent_by: str) -> tuple[str, str]:
    subject = "Learnlyf test email"
    body = f"""\
    <p>This is a test email, sent by {sent_by} from the system admin dashboard.</p>
    <p>If you're reading this, Resend is configured correctly and Learnlyf can deliver mail.</p>
    """
    return subject, _wrapper(subject, body)


def attendance_notice_email(
    parent_name: str, student_name: str, class_name: str, school_name: str,
    reason: str, absence_count: int | None = None
) -> tuple[str, str]:
    """`reason` is "absent" or "late". `absence_count` (absences this
    session, only set for `reason="absent"`) adds the pattern context that's
    the whole point of only notifying once a threshold is crossed."""
    if reason == "late":
        subject = f"{student_name} was marked late today"
        detail = f"was marked <strong>late</strong> for <strong>{class_name}</strong> today"
    else:
        subject = f"{student_name} has been absent {absence_count or ''} times this session".replace("  ", " ")
        detail = (
            f"was marked <strong>absent</strong> from <strong>{class_name}</strong> today - "
            f"their {_ordinal(absence_count)} absence this session" if absence_count
            else f"was marked <strong>absent</strong> from <strong>{class_name}</strong> today"
        )

    body = f"""\
    <p>Hi {parent_name},</p>
    <p><strong>{student_name}</strong> {detail} at {school_name}.</p>
    <p style="color:#6b7280;font-size:13px;">If this doesn't match what you expect, please contact the school.</p>
    """
    return subject, _wrapper(subject, body)


def _ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def fee_overdue_email(
    parent_name: str, student_name: str, category_name: str, balance: float, school_name: str
) -> tuple[str, str]:
    subject = f"{student_name}'s {category_name} is now overdue"
    body = f"""\
    <p>Hi {parent_name},</p>
    <p><strong>{student_name}'s {category_name}</strong> at {school_name} is past its due date, with a balance of <strong>&#8358;{balance:,.2f}</strong> outstanding.</p>
    <p style="color:#6b7280;font-size:13px;">If you've already paid, please allow a little time for it to be recorded, or contact the school.</p>
    """
    return subject, _wrapper(subject, body)


def report_card_published_email(
    parent_name: str, student_name: str, term_label: str, school_name: str, view_link: str
) -> tuple[str, str]:
    subject = f"{student_name}'s report card is ready"
    body = f"""\
    <p>Hi {parent_name},</p>
    <p><strong>{student_name}'s</strong> report card for {term_label} has been published by {school_name}.</p>
    {_button("View report card", view_link)}
    """
    return subject, _wrapper(f"{student_name}'s report card is ready", body)
