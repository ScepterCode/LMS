"""
Email verification (POST /auth/verify-email). Non-enforcing - it only
flips users.email_verified. Real FastAPI + real Supabase, same as the rest.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_email_verification_token, create_password_reset_token
from tests.conftest import unique


def _verified(supabase, user_id: str) -> bool:
    row = supabase.table("users").select("email_verified").eq("id", user_id).execute()
    return bool(row.data and row.data[0].get("email_verified"))


def _make_user(school, role="teacher"):
    email = f"{unique('verify')}@example.com"
    res = school["client"].post("/api/v1/users", json={
        "email": email, "password": "PytestUser123!", "full_name": "Verify Me", "role": role,
    })
    assert res.status_code == 201, res.text
    return res.json()["id"], email


class TestVerifyEmail:
    def test_valid_token_flips_the_flag_and_is_idempotent(self, school, supabase):
        user_id, email = _make_user(school)
        assert _verified(supabase, user_id) is False

        token = create_email_verification_token(user_id, email)
        first = TestClient(app).post("/api/v1/auth/verify-email", json={"token": token})
        assert first.status_code == 200, first.text
        assert _verified(supabase, user_id) is True

        second = TestClient(app).post("/api/v1/auth/verify-email", json={"token": token})
        assert second.status_code == 200, second.text

    def test_garbage_token_rejected(self):
        res = TestClient(app).post("/api/v1/auth/verify-email", json={"token": "nope"})
        assert res.status_code == 400, res.text

    def test_token_for_a_different_email_than_current_is_rejected(self, school, supabase):
        user_id, _ = _make_user(school)
        stale = create_email_verification_token(user_id, "old-address@example.com")
        res = TestClient(app).post("/api/v1/auth/verify-email", json={"token": stale})
        assert res.status_code == 400, res.text

    def test_login_token_is_not_accepted(self, school):
        login = TestClient(app).post("/api/v1/auth/login", json={
            "email": school["admin_email"], "password": school["admin_password"],
        })
        assert login.status_code == 200, login.text
        session_cookie = login.cookies.get("access_token")
        res = TestClient(app).post("/api/v1/auth/verify-email", json={"token": session_cookie})
        assert res.status_code == 400, res.text

    def test_completing_a_password_reset_marks_the_email_verified(self, school, supabase):
        user_id, email = _make_user(school)
        assert _verified(supabase, user_id) is False

        pw_hash = supabase.table("users").select("password_hash").eq("id", user_id).execute().data[0]["password_hash"]
        token = create_password_reset_token(user_id, email, pw_hash)
        res = TestClient(app).post("/api/v1/auth/reset-password", json={
            "token": token, "new_password": "BrandNewPass123!",
        })
        assert res.status_code == 200, res.text
        assert _verified(supabase, user_id) is True
