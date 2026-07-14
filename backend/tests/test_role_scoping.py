"""
Integration tests for the class/relationship scoping added to previously
over-broad teacher/parent permissions:

- Students & guardians: a teacher may only create/edit students (and
  their guardians) in a class they are the form teacher of, not any
  student org-wide.
- Leave requests: creation is scoped to an actual relationship with the
  student (admin unrestricted, teacher must be the student's form
  teacher, parent must be linked to the student); approval is scoped to
  the student's form teacher, not any teacher org-wide.

Same conventions as the other test files: real FastAPI app via
TestClient against the real Supabase project, no mocking.
"""
from tests.conftest import make_teacher, unique


def _assign_form_teacher(school, teacher, klass, subject, academic_session):
    res = school["client"].post("/api/v1/teacher-management/teacher-assignments", json={
        "teacher_id": teacher["teacher"]["id"], "class_id": klass["id"],
        "subject_id": subject["id"], "session_id": academic_session["id"],
        "is_form_teacher": True,
    })
    assert res.status_code == 201, res.text


def _make_second_class(school):
    res = school["client"].post("/api/v1/classes", json={
        "name": unique("SS"), "level": "Senior", "section": "B", "capacity": 40
    })
    assert res.status_code == 201, res.text
    return res.json()


def _make_parent(school, student_id, relationship="Mother"):
    """Creates a parent user + parent profile + link to student_id, and
    returns a logged-in TestClient for that parent."""
    admin_client = school["client"]
    email = f"{unique('parent')}@example.com"
    password = "PytestParent123!"

    user_res = admin_client.post("/api/v1/users", json={
        "email": email, "password": password, "full_name": "Pytest Parent", "role": "parent"
    })
    assert user_res.status_code == 201, user_res.text
    user = user_res.json()

    parent_res = admin_client.post("/api/v1/parents", json={
        "user_id": user["id"], "first_name": "Pytest", "last_name": "Parent",
        "phone": "08011111111", "email": email,
    })
    assert parent_res.status_code == 201, parent_res.text
    parent = parent_res.json()

    link_res = admin_client.post(f"/api/v1/parents/{parent['id']}/children", json={
        "student_id": student_id, "relationship": relationship,
    })
    assert link_res.status_code == 201, link_res.text

    from fastapi.testclient import TestClient
    from app.main import app
    parent_client = TestClient(app)
    login = parent_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text

    return {"user": user, "parent": parent, "client": parent_client}


# ============================================
# STUDENT / GUARDIAN CLASS SCOPING
# ============================================

class TestStudentClassScoping:
    def test_form_teacher_can_create_student_in_own_class(
        self, school, teacher, klass, subject, academic_session
    ):
        _assign_form_teacher(school, teacher, klass, subject, academic_session)

        res = teacher["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Own", "last_name": "Class",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
        })
        assert res.status_code == 201, res.text

    def test_teacher_cannot_create_student_in_unassigned_class(
        self, school, teacher, klass, subject, academic_session
    ):
        _assign_form_teacher(school, teacher, klass, subject, academic_session)
        other_class = _make_second_class(school)

        res = teacher["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Other", "last_name": "Class",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": other_class["id"],
        })
        assert res.status_code == 403, res.text

    def test_teacher_cannot_create_student_with_no_class(self, school, teacher):
        res = teacher["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "No", "last_name": "Class",
            "date_of_birth": "2015-01-01", "gender": "Male",
        })
        assert res.status_code == 403, res.text

    def test_form_teacher_can_update_student_in_own_class(
        self, school, teacher, klass, subject, academic_session, student
    ):
        _assign_form_teacher(school, teacher, klass, subject, academic_session)

        res = teacher["client"].put(f"/api/v1/students/{student['id']}", json={
            "phone": "08099999999",
        })
        assert res.status_code == 200, res.text

    def test_teacher_cannot_update_student_in_other_class(
        self, school, teacher, klass, subject, academic_session, student
    ):
        # teacher is form teacher of a *different* class than the student's
        other_class = _make_second_class(school)
        _assign_form_teacher(school, teacher, other_class, subject, academic_session)

        res = teacher["client"].put(f"/api/v1/students/{student['id']}", json={
            "phone": "08099999999",
        })
        assert res.status_code == 403, res.text

    def test_admin_can_create_and_update_student_in_any_class(self, school, klass):
        client = school["client"]
        create = client.post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Admin", "last_name": "Created",
            "date_of_birth": "2015-01-01", "gender": "Female", "current_class_id": klass["id"],
        })
        assert create.status_code == 201, create.text

        update = client.put(f"/api/v1/students/{create.json()['id']}", json={"phone": "08022222222"})
        assert update.status_code == 200, update.text


class TestGuardianClassScoping:
    def test_form_teacher_can_add_guardian_for_own_class_student(
        self, school, teacher, klass, subject, academic_session, student
    ):
        _assign_form_teacher(school, teacher, klass, subject, academic_session)

        res = teacher["client"].post(f"/api/v1/students/{student['id']}/guardians", json={
            "guardian_type": "father", "first_name": "Guardian", "last_name": "One",
            "relationship": "Father", "phone": "08033333333",
        })
        assert res.status_code == 201, res.text

    def test_teacher_cannot_add_guardian_for_other_class_student(
        self, school, teacher, klass, subject, academic_session, student
    ):
        other_class = _make_second_class(school)
        _assign_form_teacher(school, teacher, other_class, subject, academic_session)

        res = teacher["client"].post(f"/api/v1/students/{student['id']}/guardians", json={
            "guardian_type": "father", "first_name": "Guardian", "last_name": "Two",
            "relationship": "Father", "phone": "08044444444",
        })
        assert res.status_code == 403, res.text


# ============================================
# LEAVE REQUEST RELATIONSHIP SCOPING
# ============================================

class TestLeaveRequestScoping:
    def test_admin_can_create_leave_request_for_any_student(self, school, student):
        res = school["client"].post("/api/v1/attendance/leave-requests", json={
            "student_id": student["id"], "start_date": "2099-10-01", "end_date": "2099-10-02",
            "leave_type": "sick", "reason": "Fever",
        })
        assert res.status_code == 201, res.text

    def test_form_teacher_can_create_leave_request_for_own_class_student(
        self, school, teacher, klass, subject, academic_session, student
    ):
        _assign_form_teacher(school, teacher, klass, subject, academic_session)

        res = teacher["client"].post("/api/v1/attendance/leave-requests", json={
            "student_id": student["id"], "start_date": "2099-10-01", "end_date": "2099-10-02",
            "leave_type": "family", "reason": "Family event",
        })
        assert res.status_code == 201, res.text

    def test_non_form_teacher_cannot_create_leave_request(self, school, teacher, student):
        # teacher exists but has no form-teacher assignment to student's class at all
        res = teacher["client"].post("/api/v1/attendance/leave-requests", json={
            "student_id": student["id"], "start_date": "2099-10-01", "end_date": "2099-10-02",
            "leave_type": "other", "reason": "Unrelated teacher",
        })
        assert res.status_code == 403, res.text

    def test_parent_can_create_leave_request_for_linked_child(self, school, student):
        parent = _make_parent(school, student["id"])

        res = parent["client"].post("/api/v1/attendance/leave-requests", json={
            "student_id": student["id"], "start_date": "2099-10-01", "end_date": "2099-10-02",
            "leave_type": "sick", "reason": "Linked child",
        })
        assert res.status_code == 201, res.text

    def test_parent_cannot_create_leave_request_for_unlinked_student(self, school, klass):
        # a second student this parent has no link to
        other_student = school["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Unlinked", "last_name": "Student",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
        })
        assert other_student.status_code == 201, other_student.text

        # parent linked to a *different* student
        linked_student = school["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Linked", "last_name": "Student",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
        })
        assert linked_student.status_code == 201, linked_student.text
        parent = _make_parent(school, linked_student.json()["id"])

        res = parent["client"].post("/api/v1/attendance/leave-requests", json={
            "student_id": other_student.json()["id"], "start_date": "2099-10-01", "end_date": "2099-10-02",
            "leave_type": "sick", "reason": "Should be rejected",
        })
        assert res.status_code == 403, res.text

    def test_form_teacher_can_approve_leave_request_for_own_class(
        self, school, teacher, klass, subject, academic_session, student
    ):
        _assign_form_teacher(school, teacher, klass, subject, academic_session)

        create = school["client"].post("/api/v1/attendance/leave-requests", json={
            "student_id": student["id"], "start_date": "2099-10-01", "end_date": "2099-10-02",
            "leave_type": "sick", "reason": "To be approved",
        })
        assert create.status_code == 201, create.text

        res = teacher["client"].put(
            f"/api/v1/attendance/leave-requests/{create.json()['id']}/approve",
            json={"status": "approved"},
        )
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "approved"

    def test_non_form_teacher_cannot_approve_leave_request(self, school, teacher, student):
        create = school["client"].post("/api/v1/attendance/leave-requests", json={
            "student_id": student["id"], "start_date": "2099-10-01", "end_date": "2099-10-02",
            "leave_type": "sick", "reason": "Should not be approvable",
        })
        assert create.status_code == 201, create.text

        # teacher has no form-teacher assignment to student's class
        res = teacher["client"].put(
            f"/api/v1/attendance/leave-requests/{create.json()['id']}/approve",
            json={"status": "approved"},
        )
        assert res.status_code == 403, res.text


# ============================================
# STUDENT ROSTER SCOPING (parent data leak fix)
# ============================================
# GET /students and GET /students/{id} previously had no role check at
# all beyond "belongs to this school" - any parent could list or fetch
# every student in the org, not just their own linked children.

class TestStudentRosterScoping:
    def test_parent_list_students_only_returns_linked_children(self, school, klass):
        linked = school["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Linked", "last_name": "Kid",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
        })
        assert linked.status_code == 201, linked.text
        other = school["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Other", "last_name": "Kid",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
        })
        assert other.status_code == 201, other.text

        parent = _make_parent(school, linked.json()["id"])

        res = parent["client"].get("/api/v1/students", params={"limit": 500})
        assert res.status_code == 200, res.text
        returned_ids = {s["id"] for s in res.json()}
        assert linked.json()["id"] in returned_ids
        assert other.json()["id"] not in returned_ids

    def test_parent_with_no_linked_children_gets_empty_list(self, school):
        email = f"{unique('lonely-parent')}@example.com"
        password = "PytestParent123!"
        user = school["client"].post("/api/v1/users", json={
            "email": email, "password": password, "full_name": "No Kids", "role": "parent"
        })
        assert user.status_code == 201, user.text

        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, login.text

        res = client.get("/api/v1/students", params={"limit": 500})
        assert res.status_code == 200, res.text
        assert res.json() == []

    def test_parent_can_get_linked_student_by_id(self, school, student):
        parent = _make_parent(school, student["id"])
        res = parent["client"].get(f"/api/v1/students/{student['id']}")
        assert res.status_code == 200, res.text

    def test_parent_cannot_get_unlinked_student_by_id(self, school, klass):
        unlinked = school["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Not", "last_name": "Mine",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
        })
        assert unlinked.status_code == 201, unlinked.text
        linked = school["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Is", "last_name": "Mine",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
        })
        assert linked.status_code == 201, linked.text
        parent = _make_parent(school, linked.json()["id"])

        res = parent["client"].get(f"/api/v1/students/{unlinked.json()['id']}")
        assert res.status_code == 403, res.text

    def test_teacher_list_students_still_sees_whole_roster(self, school, teacher, student):
        # Teachers are not scoped by the parent fix - unchanged behavior.
        res = teacher["client"].get("/api/v1/students", params={"limit": 500})
        assert res.status_code == 200, res.text
        assert any(s["id"] == student["id"] for s in res.json())


# ============================================
# PARENT RECORD SCOPING
# ============================================
# GET /parents/{id} and GET /parents/{id}/children previously let any
# authenticated user in the org view any parent's record - including
# another parent's.

class TestParentRecordScoping:
    def test_parent_cannot_view_another_parents_record(self, school, student):
        parent_a = _make_parent(school, student["id"])

        other_student = school["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Second", "last_name": "Kid",
            "date_of_birth": "2015-01-01", "gender": "Female",
        })
        assert other_student.status_code == 201, other_student.text
        parent_b = _make_parent(school, other_student.json()["id"])

        res = parent_a["client"].get(f"/api/v1/parents/{parent_b['parent']['id']}")
        assert res.status_code == 403, res.text

    def test_parent_cannot_view_another_parents_children_list(self, school, student):
        parent_a = _make_parent(school, student["id"])

        other_student = school["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Third", "last_name": "Kid",
            "date_of_birth": "2015-01-01", "gender": "Female",
        })
        assert other_student.status_code == 201, other_student.text
        parent_b = _make_parent(school, other_student.json()["id"])

        res = parent_a["client"].get(f"/api/v1/parents/{parent_b['parent']['id']}/children")
        assert res.status_code == 403, res.text

    def test_get_my_children_returns_own_linked_children_only(self, school, student):
        parent = _make_parent(school, student["id"], relationship="Mother")

        res = parent["client"].get("/api/v1/parents/me/children")
        assert res.status_code == 200, res.text
        body = res.json()
        assert len(body) == 1
        assert body[0]["student_id"] == student["id"]
        assert body[0]["relationship"] == "Mother"

    def test_get_my_children_rejects_non_parent_roles(self, school):
        res = school["client"].get("/api/v1/parents/me/children")
        assert res.status_code == 403, res.text

    def test_parent_cannot_list_parent_directory(self, school, student):
        parent = _make_parent(school, student["id"])
        res = parent["client"].get("/api/v1/parents")
        assert res.status_code == 403, res.text


# ============================================
# STUDENT -> PARENT LINK VISIBILITY
# ============================================
# GET /students/{id}/parents is the reverse of GET /parents/{id}/children -
# it's what the "Add Guardian" UI uses to show already-linked parent
# accounts on a student's own page.

class TestStudentParentsEndpoint:
    def test_admin_sees_linked_parent_on_student(self, school, student):
        parent = _make_parent(school, student["id"], relationship="Father")

        res = school["client"].get(f"/api/v1/students/{student['id']}/parents")
        assert res.status_code == 200, res.text
        body = res.json()
        assert len(body) == 1
        assert body[0]["parent_id"] == parent["parent"]["id"]
        assert body[0]["relationship"] == "Father"

    def test_parent_can_see_own_link_on_their_linked_student(self, school, student):
        parent = _make_parent(school, student["id"])

        res = parent["client"].get(f"/api/v1/students/{student['id']}/parents")
        assert res.status_code == 200, res.text

    def test_parent_cannot_see_parents_of_unlinked_student(self, school, klass):
        unlinked = school["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Fourth", "last_name": "Kid",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
        })
        assert unlinked.status_code == 201, unlinked.text
        linked = school["client"].post("/api/v1/students", json={
            "admission_number": unique("ADM"), "first_name": "Fifth", "last_name": "Kid",
            "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
        })
        assert linked.status_code == 201, linked.text
        parent = _make_parent(school, linked.json()["id"])

        res = parent["client"].get(f"/api/v1/students/{unlinked.json()['id']}/parents")
        assert res.status_code == 403, res.text
