"""
Shared fixtures for the real integration test suite.

These tests hit the actual FastAPI app wired to the real Supabase
project configured in .env - there is no separate test database. Every
fixture that creates data cleans up after itself (see `school`
fixture), but tests should still avoid depending on global state beyond
what a fixture explicitly hands them.
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_supabase


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def supabase():
    return get_supabase()


@pytest.fixture(scope="session")
def school(supabase):
    """
    Registers one throwaway school + admin for the whole test session,
    and deletes everything it created afterwards. users.school_id is
    ON DELETE SET NULL (not CASCADE), so the admin user is deleted
    explicitly rather than relying on deleting the organization alone.
    """
    with TestClient(app) as client:
        email = f"{unique('admin')}@example.com"
        password = "PytestAdmin123!"
        res = client.post("/api/v1/auth/register-school", json={
            "school_name": unique("Pytest School"),
            "school_email": f"{unique('school')}@example.com",
            "admin_name": "Pytest Admin",
            "admin_email": email,
            "admin_password": password,
        })
        assert res.status_code == 200, res.text
        body = res.json()
        org_id = body["organization_id"]
        admin_id = body["admin_id"]

        login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, login.text

        yield {
            "client": client,
            "org_id": org_id,
            "admin_id": admin_id,
            "admin_email": email,
            "admin_password": password,
        }

        # Cleanup - order matters for FK constraints without CASCADE.
        supabase.table("users").delete().eq("school_id", org_id).execute()
        supabase.table("campuses").delete().eq("organization_id", org_id).execute()
        supabase.table("organizations").delete().eq("id", org_id).execute()


@pytest.fixture
def academic_session(school):
    client = school["client"]
    res = client.post("/api/v1/sessions", json={
        "name": unique("2099/2100"), "start_date": "2099-09-01", "end_date": "2100-07-31", "is_current": True
    })
    assert res.status_code == 201, res.text
    return res.json()


@pytest.fixture
def term(school, academic_session):
    client = school["client"]
    res = client.post("/api/v1/terms", json={
        "session_id": academic_session["id"], "name": "1st Term", "term_number": 1,
        "start_date": "2099-09-01", "end_date": "2099-12-15", "is_current": True
    })
    assert res.status_code == 201, res.text
    return res.json()


@pytest.fixture
def klass(school):
    client = school["client"]
    res = client.post("/api/v1/classes", json={
        "name": unique("JSS"), "level": "Junior", "section": "A", "capacity": 40
    })
    assert res.status_code == 201, res.text
    return res.json()


@pytest.fixture
def subject(school):
    client = school["client"]
    res = client.post("/api/v1/subjects", json={
        "name": unique("Subject"), "code": unique("SUB")[:10].upper(), "subject_type": "core"
    })
    assert res.status_code == 201, res.text
    return res.json()


@pytest.fixture
def student(school, klass):
    client = school["client"]
    res = client.post("/api/v1/students", json={
        "admission_number": unique("ADM"), "first_name": "Test", "last_name": "Student",
        "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"]
    })
    assert res.status_code == 201, res.text
    return res.json()


def make_teacher(school, email=None, password="PytestTeacher123!"):
    """
    Creates a teacher user + teacher profile, and returns a *separate*
    logged-in TestClient for them (each TestClient has its own cookie
    jar, so this is how multi-user permission tests get distinct
    sessions without clobbering the admin's).
    """
    admin_client = school["client"]
    email = email or f"{unique('teacher')}@example.com"

    user_res = admin_client.post("/api/v1/users", json={
        "email": email, "password": password, "full_name": "Pytest Teacher", "role": "teacher"
    })
    assert user_res.status_code == 201, user_res.text
    user = user_res.json()

    teacher_res = admin_client.post("/api/v1/teachers", json={
        "user_id": user["id"], "staff_number": unique("STF"), "first_name": "Pytest",
        "last_name": "Teacher", "gender": "Female", "email": email, "phone": "08000000000"
    })
    assert teacher_res.status_code == 201, teacher_res.text
    teacher = teacher_res.json()

    teacher_client = TestClient(app)
    login = teacher_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text

    return {"user": user, "teacher": teacher, "client": teacher_client, "email": email, "password": password}


@pytest.fixture
def teacher(school):
    return make_teacher(school)


def make_dean(school, email=None, password="PytestDean123!"):
    """Creates a dean user (no separate profile table - dean is just a
    users row with role='dean') and returns a logged-in TestClient."""
    admin_client = school["client"]
    email = email or f"{unique('dean')}@example.com"

    user_res = admin_client.post("/api/v1/users", json={
        "email": email, "password": password, "full_name": "Pytest Dean", "role": "dean"
    })
    assert user_res.status_code == 201, user_res.text
    user = user_res.json()

    dean_client = TestClient(app)
    login = dean_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text

    return {"user": user, "client": dean_client, "email": email, "password": password}


@pytest.fixture
def dean(school):
    return make_dean(school)
