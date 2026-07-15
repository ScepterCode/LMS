"""
Integration tests for Phase 3/4 features: form teachers, grading,
attendance, remarks, report cards, fees, and parent linking.

Unlike the previous version of this file, every test here calls the
real FastAPI app (via TestClient) which talks to the real Supabase
project. There is no mocking of app.api.v1.endpoints or app.core -
these tests fail if the actual code is broken.
"""
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import make_teacher, unique


# ============================================
# FORM TEACHER ASSIGNMENT
# ============================================

class TestFormTeacherAssignment:
    def test_assign_form_teacher_success(self, school, teacher, klass, subject, academic_session):
        client = school["client"]
        res = client.post("/api/v1/teacher-management/teacher-assignments", json={
            "teacher_id": teacher["teacher"]["id"], "class_id": klass["id"],
            "subject_id": subject["id"], "session_id": academic_session["id"],
            "is_form_teacher": True,
        })
        assert res.status_code == 201, res.text
        assert res.json()["is_form_teacher"] is True

    def test_only_one_form_teacher_per_class_session(self, school, teacher, klass, subject, academic_session):
        client = school["client"]
        first = client.post("/api/v1/teacher-management/teacher-assignments", json={
            "teacher_id": teacher["teacher"]["id"], "class_id": klass["id"],
            "subject_id": subject["id"], "session_id": academic_session["id"],
            "is_form_teacher": True,
        })
        assert first.status_code == 201, first.text

        other_teacher = make_teacher(school)
        second = client.post("/api/v1/teacher-management/teacher-assignments", json={
            "teacher_id": other_teacher["teacher"]["id"], "class_id": klass["id"],
            "subject_id": subject["id"], "session_id": academic_session["id"],
            "is_form_teacher": True,
        })
        assert second.status_code == 422, second.text
        assert "form teacher" in second.json()["error"]["message"].lower()

    def test_non_admin_cannot_assign_form_teacher(self, school, teacher, klass, subject, academic_session):
        other_teacher = make_teacher(school)
        res = other_teacher["client"].post("/api/v1/teacher-management/teacher-assignments", json={
            "teacher_id": teacher["teacher"]["id"], "class_id": klass["id"],
            "subject_id": subject["id"], "session_id": academic_session["id"],
            "is_form_teacher": True,
        })
        assert res.status_code == 403, res.text


# ============================================
# GRADING SCHEMES
# ============================================

class TestGradingScheme:
    def test_create_grading_scheme_20_20_60(self, school, academic_session):
        client = school["client"]
        res = client.post("/api/v1/teacher-management/grading-schemes", json={
            "session_id": academic_session["id"], "name": unique("20-20-60"), "is_default": True,
            "components": [
                {"component_type": "test", "component_name": "Test 1", "weight_percentage": 20},
                {"component_type": "coursework", "component_name": "Coursework", "weight_percentage": 20},
                {"component_type": "exam", "component_name": "Exam", "weight_percentage": 60},
            ],
        })
        assert res.status_code == 201, res.text
        assert len(res.json()["components"]) == 3

    def test_grading_scheme_percentage_validation(self, school, academic_session):
        """Components must sum to 100 - this is enforced by a Pydantic validator."""
        client = school["client"]
        res = client.post("/api/v1/teacher-management/grading-schemes", json={
            "session_id": academic_session["id"], "name": unique("Bad Scheme"),
            "components": [
                {"component_type": "test", "component_name": "Test 1", "weight_percentage": 20},
                {"component_type": "exam", "component_name": "Exam", "weight_percentage": 60},
            ],
        })
        assert res.status_code == 422, res.text

    def test_non_admin_cannot_create_grading_scheme(self, school, teacher, academic_session):
        res = teacher["client"].post("/api/v1/teacher-management/grading-schemes", json={
            "session_id": academic_session["id"], "name": unique("Scheme"),
            "components": [{"component_type": "exam", "component_name": "Exam", "weight_percentage": 100}],
        })
        assert res.status_code == 403, res.text


# ============================================
# CLASS SUBJECT CURRICULUM
# ============================================

class TestClassSubjectCurriculum:
    def test_add_subject_to_class(self, school, klass, subject, academic_session):
        """class_id comes from the URL path, not the body - the frontend never
        sends it in the body, so ClassSubjectCreate must not require it there
        (it previously did, silently 422ing every real caller)."""
        client = school["client"]
        res = client.post(f"/api/v1/teacher-management/classes/{klass['id']}/subjects", json={
            "subject_id": subject["id"], "session_id": academic_session["id"],
        })
        assert res.status_code == 201, res.text
        assert res.json()["subject_name"] == subject["name"]

    def test_create_class_with_subjects_inline(self, school, subject, academic_session):
        """ClassCreate.subject_ids lets admins attach subjects at class-creation time."""
        client = school["client"]
        res = client.post("/api/v1/classes", json={
            "name": unique("JSS"), "level": "Junior", "section": "B", "capacity": 40,
            "session_id": academic_session["id"], "subject_ids": [subject["id"]],
        })
        assert res.status_code == 201, res.text


# ============================================
# TEACHER PERMISSIONS (the core of the form-teacher fix)
# ============================================

class TestTeacherPermissions:
    def _assign_form_teacher(self, school, teacher, klass, subject, academic_session):
        res = school["client"].post("/api/v1/teacher-management/teacher-assignments", json={
            "teacher_id": teacher["teacher"]["id"], "class_id": klass["id"],
            "subject_id": subject["id"], "session_id": academic_session["id"],
            "is_form_teacher": True,
        })
        assert res.status_code == 201, res.text

    def test_form_teacher_can_mark_attendance_for_own_class(
        self, school, teacher, klass, subject, academic_session, term, student
    ):
        self._assign_form_teacher(school, teacher, klass, subject, academic_session)
        res = teacher["client"].post("/api/v1/attendance/mark", json={
            "class_id": klass["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "attendance_date": "2099-09-02",
            "records": [{"student_id": student["id"], "status": "present"}],
        })
        assert res.status_code == 201, res.text

    def test_non_form_teacher_cannot_mark_attendance(
        self, school, teacher, klass, academic_session, term, student
    ):
        """Regression test for the exact bug fixed this session: teacher_id
        was never in the JWT, so this check always silently failed."""
        res = teacher["client"].post("/api/v1/attendance/mark", json={
            "class_id": klass["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "attendance_date": "2099-09-02",
            "records": [{"student_id": student["id"], "status": "present"}],
        })
        assert res.status_code == 403, res.text

    def test_form_teacher_can_add_remarks_for_own_class(
        self, school, teacher, klass, subject, academic_session, term, student
    ):
        self._assign_form_teacher(school, teacher, klass, subject, academic_session)
        res = teacher["client"].post("/api/v1/teacher-management/remarks", json={
            "student_id": student["id"], "class_id": klass["id"], "session_id": academic_session["id"],
            "term_id": term["id"], "remark_text": "Good progress this term.",
        })
        assert res.status_code == 201, res.text
        assert res.json()["form_teacher_id"] == teacher["teacher"]["id"]

    def test_subject_teacher_can_create_assessment_for_assigned_subject(
        self, school, teacher, klass, subject, academic_session, term
    ):
        client = school["client"]
        at = client.post("/api/v1/grading/assessment-types", json={
            "name": unique("Test"), "code": unique("T")[:10].upper(), "weight_percentage": 100,
        })
        assert at.status_code == 201, at.text

        assign = client.post("/api/v1/teacher-management/teacher-assignments", json={
            "teacher_id": teacher["teacher"]["id"], "class_id": klass["id"],
            "subject_id": subject["id"], "session_id": academic_session["id"], "is_form_teacher": False,
        })
        assert assign.status_code == 201, assign.text

        res = teacher["client"].post("/api/v1/grading/assessments", json={
            "assessment_type_id": at.json()["id"], "subject_id": subject["id"], "class_id": klass["id"],
            "session_id": academic_session["id"], "term_id": term["id"], "title": "Quiz",
            "max_score": 100, "assessment_date": "2099-09-05",
        })
        assert res.status_code == 201, res.text

    def test_teacher_cannot_create_assessment_for_unassigned_subject(
        self, school, teacher, klass, subject, academic_session, term
    ):
        client = school["client"]
        at = client.post("/api/v1/grading/assessment-types", json={
            "name": unique("Test"), "code": unique("T")[:10].upper(), "weight_percentage": 100,
        })
        assert at.status_code == 201, at.text

        res = teacher["client"].post("/api/v1/grading/assessments", json={
            "assessment_type_id": at.json()["id"], "subject_id": subject["id"], "class_id": klass["id"],
            "session_id": academic_session["id"], "term_id": term["id"], "title": "Quiz",
            "max_score": 100, "assessment_date": "2099-09-05",
        })
        assert res.status_code == 403, res.text


# ============================================
# ATTENDANCE WORKFLOW
# ============================================

class TestAttendanceWorkflow:
    def test_mark_and_summarize_attendance(self, school, klass, academic_session, term, student):
        client = school["client"]
        mark = client.post("/api/v1/attendance/mark", json={
            "class_id": klass["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "attendance_date": "2099-09-03",
            "records": [{"student_id": student["id"], "status": "late", "minutes_late": 10}],
        })
        assert mark.status_code == 201, mark.text

        summary = client.get(
            f"/api/v1/attendance/summary/student/{student['id']}"
            f"?session_id={academic_session['id']}&term_id={term['id']}"
        )
        assert summary.status_code == 200, summary.text
        body = summary.json()
        assert body["days_late"] == 1
        assert body["attendance_percentage"] == 100.0

    def test_admin_can_view_class_attendance(self, school, klass, academic_session, term, student):
        client = school["client"]
        client.post("/api/v1/attendance/mark", json={
            "class_id": klass["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "attendance_date": "2099-09-04",
            "records": [{"student_id": student["id"], "status": "absent"}],
        })
        res = client.get(f"/api/v1/attendance/class/{klass['id']}/date/2099-09-04")
        assert res.status_code == 200, res.text
        assert res.json()["absent_count"] == 1


# ============================================
# REPORT CARD GENERATION (the pipeline built this session)
# ============================================

class TestReportCardGeneration:
    def test_generate_report_card_computes_real_grade_and_rank(
        self, school, teacher, klass, subject, academic_session, term, student
    ):
        client = school["client"]

        client.post("/api/v1/grading/grade-configs", json={
            "grade_letter": "A", "min_score": 70, "max_score": 100, "grade_point": 5.0,
        })
        client.post("/api/v1/grading/grade-configs", json={
            "grade_letter": "F", "min_score": 0, "max_score": 69.99, "grade_point": 0.0,
        })

        at = client.post("/api/v1/grading/assessment-types", json={
            "name": unique("Exam"), "code": unique("E")[:10].upper(), "weight_percentage": 100,
        })
        assert at.status_code == 201, at.text

        assess = client.post("/api/v1/grading/assessments", json={
            "assessment_type_id": at.json()["id"], "subject_id": subject["id"], "class_id": klass["id"],
            "session_id": academic_session["id"], "term_id": term["id"], "title": "Final",
            "max_score": 100, "assessment_date": "2099-09-06",
        })
        assert assess.status_code == 201, assess.text
        assessment_id = assess.json()["id"]

        publish = client.post(f"/api/v1/grading/assessments/{assessment_id}/publish")
        assert publish.status_code == 200, publish.text

        grade = client.post("/api/v1/grading/grades/bulk", json={
            "assessment_id": assessment_id, "grades": [{"student_id": student["id"], "score": 88}],
        })
        assert grade.status_code == 201, grade.text

        report = client.post("/api/v1/grading/report-cards/generate", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
        })
        assert report.status_code == 201, report.text
        body = report.json()
        assert body["average_score"] == 88.0
        assert body["overall_grade"] == "A"
        assert body["overall_position"] == 1
        assert body["class_size"] == 1

    def test_cannot_generate_duplicate_report_card(self, school, klass, academic_session, term, student):
        client = school["client"]
        first = client.post("/api/v1/grading/report-cards/generate", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
        })
        assert first.status_code == 201, first.text

        second = client.post("/api/v1/grading/report-cards/generate", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
        })
        assert second.status_code == 409, second.text


# ============================================
# FEES AND PAYMENTS
# ============================================

class TestFeesAndPayments:
    def test_fee_lifecycle_partial_then_full_payment(self, school, klass, academic_session, student):
        client = school["client"]

        category = client.post("/api/v1/fees/categories", json={
            "name": unique("Tuition"), "code": unique("TUI")[:10].upper(),
        })
        assert category.status_code == 201, category.text

        structure = client.post("/api/v1/fees/structures", json={
            "fee_category_id": category.json()["id"], "session_id": academic_session["id"],
            "class_id": klass["id"], "amount": "50000.00",
        })
        assert structure.status_code == 201, structure.text

        student_fee = client.post("/api/v1/fees/student-fees", json={
            "student_id": student["id"], "fee_structure_id": structure.json()["id"],
            "session_id": academic_session["id"], "amount": "50000.00", "final_amount": "50000.00",
        })
        assert student_fee.status_code == 201, student_fee.text
        fee_id = student_fee.json()["id"]

        partial = client.post("/api/v1/fees/payments", json={
            "student_id": student["id"], "payment_date": "2099-09-10", "amount": "20000.00",
            "payment_method": "cash",
            "fee_allocations": [{"student_fee_id": fee_id, "allocated_amount": "20000.00"}],
        })
        assert partial.status_code == 201, partial.text
        assert "receipt_number" in partial.json()

        after_partial = client.get(f"/api/v1/fees/student-fees?student_id={student['id']}")
        assert after_partial.json()[0]["status"] == "partial"
        # DECIMAL columns come back from Supabase as JSON strings, not
        # numbers - this bit the frontend for real (fees/payments/page.tsx
        # summed fee.balance directly, silently string-concatenating
        # instead of adding). float() here documents that the API
        # contract is "numeric string", which callers must convert.
        assert float(after_partial.json()[0]["balance"]) == 30000.0

        full = client.post("/api/v1/fees/payments", json={
            "student_id": student["id"], "payment_date": "2099-09-11", "amount": "30000.00",
            "payment_method": "cash",
            "fee_allocations": [{"student_fee_id": fee_id, "allocated_amount": "30000.00"}],
        })
        assert full.status_code == 201, full.text

        after_full = client.get(f"/api/v1/fees/student-fees?student_id={student['id']}")
        assert after_full.json()[0]["status"] == "paid"
        assert float(after_full.json()[0]["balance"]) == 0.0

    def test_bulk_assign_fee_to_class(self, school, klass, academic_session, student):
        """Regression test: bulk_assign_fees used to query a nonexistent
        'enrollments' table and crash with PGRST205."""
        client = school["client"]
        category = client.post("/api/v1/fees/categories", json={
            "name": unique("Sports"), "code": unique("SPT")[:10].upper(),
        })
        structure = client.post("/api/v1/fees/structures", json={
            "fee_category_id": category.json()["id"], "session_id": academic_session["id"],
            "class_id": klass["id"], "amount": "5000.00",
        })
        res = client.post(
            f"/api/v1/fees/student-fees/bulk-assign"
            f"?session_id={academic_session['id']}&class_id={klass['id']}",
            json=[structure.json()["id"]],
        )
        assert res.status_code == 200, res.text
        assert res.json()["fees_assigned"] >= 1


# ============================================
# PARENT-STUDENT LINKING
# ============================================

class TestParentStudentLinking:
    def test_link_parent_to_student(self, school, student):
        """Regression test: link_parent_to_student used to insert an
        updated_at column that doesn't exist on parent_student_links,
        so every single link attempt failed with a 500."""
        client = school["client"]
        email = f"{unique('parent')}@example.com"
        user = client.post("/api/v1/users", json={
            "email": email, "password": "PytestParent123!", "full_name": "Pytest Parent", "role": "parent",
        })
        assert user.status_code == 201, user.text

        parent = client.post("/api/v1/parents", json={
            "user_id": user.json()["id"], "first_name": "Pytest", "last_name": "Parent",
            "phone": "08000000001", "email": email,
        })
        assert parent.status_code == 201, parent.text
        parent_id = parent.json()["id"]

        link = client.post(f"/api/v1/parents/{parent_id}/children", json={
            "student_id": student["id"], "relationship": "Father", "is_primary": True,
        })
        assert link.status_code == 201, link.text

        children = client.get(f"/api/v1/parents/{parent_id}/children")
        assert children.status_code == 200, children.text
        assert children.json()[0]["student_id"] == student["id"]

        unlink = client.delete(f"/api/v1/parents/{parent_id}/children/{student['id']}")
        assert unlink.status_code == 200, unlink.text
        assert client.get(f"/api/v1/parents/{parent_id}/children").json() == []


# ============================================
# ADMIN / SYSTEM ADMIN OPERATIONS
# ============================================

class TestAdminOperations:
    def test_login_with_nonexistent_email_is_401_not_500(self):
        """Regression test: login used to try system_admins.email first,
        a column that doesn't exist on that table, before falling
        through to users. The failure was silently caught, but this
        pins the actual observable behavior at the API boundary."""
        with TestClient(app) as client:
            res = client.post("/api/v1/auth/login", json={
                "email": "no-such-admin@example.com", "password": "whatever",
            })
            assert res.status_code == 401, res.text

    def test_regular_admin_login_and_me(self, school):
        client = school["client"]
        me = client.get("/api/v1/auth/me")
        assert me.status_code == 200, me.text
        assert me.json()["email"] == school["admin_email"]
