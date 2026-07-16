"""
Integration tests for the "registrar" (front desk) role: admissions
intake and enrollment records only - students, class enrollments, and
parent/guardian contact records. Explicitly excluded from academic
setup (classes/subjects/sessions/terms), teacher management, grading,
and fees.

Requires database/phase8_registrar_role.sql to have been applied first -
without it, the users.role CHECK constraint rejects role='registrar'
and every test in this file fails at the `registrar` fixture.
"""
from tests.conftest import unique


class TestRegistrarAdmissionsAccess:
    def test_registrar_can_create_student(self, school, registrar, klass):
        res = registrar["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Registrar", "last_name": "Managed",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
        })
        assert res.status_code == 201, res.text

    def test_registrar_can_create_parent_account(self, school, registrar):
        res = registrar["client"].post("/api/v1/users", json={
            "email": f"{unique('parent')}@example.com", "password": "PytestParent123!",
            "full_name": "Registrar Created Parent", "role": "parent",
        })
        assert res.status_code == 201, res.text


class TestRegistrarExclusions:
    def test_registrar_cannot_create_class(self, school, registrar):
        res = registrar["client"].post("/api/v1/classes", json={
            "name": unique("JSS"), "level": "Junior", "section": "A", "capacity": 40,
        })
        assert res.status_code == 403, res.text

    def test_registrar_cannot_create_subject(self, school, registrar):
        res = registrar["client"].post("/api/v1/subjects", json={
            "name": unique("Subject"), "code": unique("SUB")[:10].upper(), "subject_type": "core",
        })
        assert res.status_code == 403, res.text

    def test_registrar_cannot_create_teacher_account(self, school, registrar):
        res = registrar["client"].post("/api/v1/users", json={
            "email": f"{unique('teacher')}@example.com", "password": "PytestTeacher123!",
            "full_name": "Should Not Be Created", "role": "teacher",
        })
        assert res.status_code == 403, res.text

    def test_registrar_cannot_create_bursar_account(self, school, registrar):
        res = registrar["client"].post("/api/v1/users", json={
            "email": f"{unique('bursar')}@example.com", "password": "PytestBursar123!",
            "full_name": "Should Not Be Created", "role": "bursar",
        })
        assert res.status_code == 403, res.text

    def test_registrar_cannot_access_fees(self, school, registrar):
        res = registrar["client"].post("/api/v1/fees/categories", json={
            "name": unique("Tuition"), "code": unique("TUI")[:10].upper(), "description": "Should be rejected",
        })
        assert res.status_code == 403, res.text

    def test_registrar_cannot_manage_grading_schemes(self, school, registrar, academic_session):
        res = registrar["client"].post("/api/v1/teacher-management/grading-schemes", json={
            "session_id": academic_session["id"], "name": unique("Scheme"),
            "components": [{"component_type": "exam", "component_name": "Final Exam", "weight_percentage": 100}],
        })
        assert res.status_code == 403, res.text
