"""
Password reset flow. Real FastAPI app + real Supabase, same conventions
as the rest of the suite. There's no test mailbox, so these build the
reset token the same way forgot-password would (via
create_password_reset_token) rather than going through email.
"""
from fastapi.testclient import TestClient
from app.core.security import create_password_reset_token
from app.main import app


def _current_password_hash(supabase, user_id: str) -> str:
    row = supabase.table("users").select("password_hash").eq("id", user_id).execute()
    assert row.data, "user not found"
    return row.data[0]["password_hash"]


class TestForgotPassword:
    def test_known_and_unknown_email_get_identical_response(self, school):
        known = school["client"].post("/api/v1/auth/forgot-password", json={"email": school["admin_email"]})
        unknown = school["client"].post("/api/v1/auth/forgot-password", json={"email": "nobody-here@example.com"})

        assert known.status_code == 200, known.text
        assert unknown.status_code == 200, unknown.text
        assert known.json() == unknown.json()


def _restore_admin_password(school, supabase):
    """school["admin"] is a session-scoped fixture other test files log in
    with, so any test that changes its password must put it back - in a
    finally, so a failed assertion above doesn't strand the rest of the
    run with a broken admin login."""
    current_hash = _current_password_hash(supabase, school["admin_id"])
    token = create_password_reset_token(school["admin_id"], school["admin_email"], current_hash)
    res = TestClient(app).post("/api/v1/auth/reset-password", json={
        "token": token, "new_password": school["admin_password"],
    })
    assert res.status_code == 200, f"failed to restore admin password: {res.text}"


class TestResetPassword:
    def test_valid_token_changes_password_and_old_password_stops_working(self, school, supabase):
        current_hash = _current_password_hash(supabase, school["admin_id"])
        token = create_password_reset_token(school["admin_id"], school["admin_email"], current_hash)
        new_password = "NewPytestPassword123!"

        try:
            res = TestClient(app).post("/api/v1/auth/reset-password", json={
                "token": token, "new_password": new_password,
            })
            assert res.status_code == 200, res.text

            old_login = TestClient(app).post("/api/v1/auth/login", json={
                "email": school["admin_email"], "password": school["admin_password"],
            })
            assert old_login.status_code == 401, old_login.text

            new_login = TestClient(app).post("/api/v1/auth/login", json={
                "email": school["admin_email"], "password": new_password,
            })
            assert new_login.status_code == 200, new_login.text
        finally:
            _restore_admin_password(school, supabase)

    def test_token_cannot_be_reused_after_password_changes(self, school, supabase):
        current_hash = _current_password_hash(supabase, school["admin_id"])
        token = create_password_reset_token(school["admin_id"], school["admin_email"], current_hash)

        try:
            first = TestClient(app).post("/api/v1/auth/reset-password", json={
                "token": token, "new_password": "FirstNewPassword123!",
            })
            assert first.status_code == 200, first.text

            second = TestClient(app).post("/api/v1/auth/reset-password", json={
                "token": token, "new_password": "SecondNewPassword123!",
            })
            assert second.status_code == 400, second.text
        finally:
            _restore_admin_password(school, supabase)

    def test_rejects_weak_password(self, school, supabase):
        current_hash = _current_password_hash(supabase, school["admin_id"])
        token = create_password_reset_token(school["admin_id"], school["admin_email"], current_hash)

        res = TestClient(app).post("/api/v1/auth/reset-password", json={
            "token": token, "new_password": "short",
        })
        assert res.status_code == 400, res.text

    def test_rejects_garbage_token(self):
        res = TestClient(app).post("/api/v1/auth/reset-password", json={
            "token": "not-a-real-token", "new_password": "SomePassword123!",
        })
        assert res.status_code == 400, res.text

    def test_login_token_is_rejected_as_a_reset_token(self, school):
        """A normal session JWT has no `purpose` claim, so it must not work
        here even though it's signed with the same secret."""
        # school["client"] carries the session as a cookie, not a bearer
        # token we can read directly - decode a fresh one via login.
        login = TestClient(app).post("/api/v1/auth/login", json={
            "email": school["admin_email"], "password": school["admin_password"],
        })
        assert login.status_code == 200, login.text
        session_cookie = login.cookies.get("access_token")
        assert session_cookie

        res = TestClient(app).post("/api/v1/auth/reset-password", json={
            "token": session_cookie, "new_password": "SomePassword123!",
        })
        assert res.status_code == 400, res.text
