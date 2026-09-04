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
