"""
Integration tests for the "dean" role: same academic/staff/student
management access as admin (classes, teachers, students, subjects,
sessions/terms, grading schemes), but explicitly excluded from
fees/payments and school-wide settings, and restricted to only
creating/managing teacher and parent accounts (not admin/bursar/dean/
system_admin accounts).

Requires database/phase7_dean_role.sql to have been applied first -
without it, the users.role CHECK constraint rejects role='dean' and
every test in this file fails at the `dean` fixture.
"""
from tests.conftest import unique


class TestDeanAcademicManagement:
    def test_dean_can_create_class(self, school, dean):
        res = dean["client"].post("/api/v1/classes", json={
            "name": unique("JSS"), "level": "Junior", "section": "A", "capacity": 40,
        })
        assert res.status_code == 201, res.text

    def test_dean_can_create_subject(self, school, dean):
        res = dean["client"].post("/api/v1/subjects", json={
            "name": unique("Subject"), "code": unique("SUB")[:10].upper(), "subject_type": "core",
        })
        assert res.status_code == 201, res.text

    def test_dean_can_create_academic_session(self, school, dean):
        res = dean["client"].post("/api/v1/sessions", json={
            "name": unique("2099/2100"), "start_date": "2099-09-01", "end_date": "2100-07-31", "is_current": False,
        })
        assert res.status_code == 201, res.text

    def test_dean_can_manage_students(self, school, dean, klass):
        res = dean["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Dean", "last_name": "Managed",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
        })
        assert res.status_code == 201, res.text


class TestDeanAccountManagement:
    def test_dean_can_create_teacher_account(self, school, dean):
        res = dean["client"].post("/api/v1/users", json={
            "email": f"{unique('teacher')}@example.com", "password": "PytestTeacher123!",
            "full_name": "Dean Created Teacher", "role": "teacher",
        })
        assert res.status_code == 201, res.text

    def test_dean_can_create_parent_account(self, school, dean):
        res = dean["client"].post("/api/v1/users", json={
            "email": f"{unique('parent')}@example.com", "password": "PytestParent123!",
            "full_name": "Dean Created Parent", "role": "parent",
        })
        assert res.status_code == 201, res.text

    def test_dean_cannot_create_bursar_account(self, school, dean):
        res = dean["client"].post("/api/v1/users", json={
            "email": f"{unique('bursar')}@example.com", "password": "PytestBursar123!",
            "full_name": "Should Not Be Created", "role": "bursar",
        })
        assert res.status_code == 403, res.text

    def test_dean_cannot_create_admin_account(self, school, dean):
        res = dean["client"].post("/api/v1/users", json={
            "email": f"{unique('admin')}@example.com", "password": "PytestAdmin123!",
            "full_name": "Should Not Be Created", "role": "admin",
        })
        assert res.status_code == 403, res.text

    def test_dean_cannot_deactivate_bursar_account(self, school, dean):
        bursar_res = school["client"].post("/api/v1/users", json={
            "email": f"{unique('bursar')}@example.com", "password": "PytestBursar123!",
            "full_name": "Real Bursar", "role": "bursar",
        })
        assert bursar_res.status_code == 201, bursar_res.text
        bursar_id = bursar_res.json()["id"]

        res = dean["client"].delete(f"/api/v1/users/{bursar_id}")
        assert res.status_code == 403, res.text


class TestDeanExclusions:
    def test_dean_cannot_access_fees(self, school, dean):
        res = dean["client"].post("/api/v1/fees/categories", json={
            "name": unique("Tuition"), "code": unique("TUI")[:10].upper(), "description": "Should be rejected",
        })
        assert res.status_code == 403, res.text

    def test_dean_cannot_update_organization_settings(self, school, dean):
        res = dean["client"].patch(f"/api/v1/organizations/{school['org_id']}", json={
            "motto": "Should not be allowed",
        })
        assert res.status_code == 403, res.text
