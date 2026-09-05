"""
Marking attendance best-effort emails parents once notify_parents_on_absence
/ on_late settings say to (_notify_attendance_parents in attendance.py). No
test mailbox and RESEND_API_KEY isn't set in test runs, so send_email() is a
logged no-op - these verify mark-attendance still succeeds end-to-end
(including the batched history-count and parent_student_links -> parents
queries) once a parent actually is linked, which is the path most likely to
break.
"""
from tests.conftest import unique


def _link_parent(school, student_id, relationship="Mother"):
    email = f"{unique('parent')}@example.com"
    user = school["client"].post("/api/v1/users", json={
        "email": email, "password": "PytestParent123!", "full_name": "Pytest Parent", "role": "parent",
    })
    assert user.status_code == 201, user.text

    parent = school["client"].post("/api/v1/parents", json={
        "user_id": user.json()["id"], "first_name": "Pytest", "last_name": "Parent",
        "phone": "08011111111", "email": email,
    })
    assert parent.status_code == 201, parent.text

    link = school["client"].post(f"/api/v1/parents/{parent.json()['id']}/children", json={
        "student_id": student_id, "relationship": relationship,
    })
    assert link.status_code == 201, link.text
    return parent.json()


def _assign_form_teacher(school, teacher, klass, subject, academic_session):
    res = school["client"].post("/api/v1/teacher-management/teacher-assignments", json={
        "teacher_id": teacher["teacher"]["id"], "class_id": klass["id"],
        "subject_id": subject["id"], "session_id": academic_session["id"],
        "is_form_teacher": True,
    })
    assert res.status_code == 201, res.text


class TestAttendanceNotify:
    def test_marking_absent_below_and_at_threshold_succeeds_with_linked_parent(
        self, school, teacher, klass, subject, academic_session, term, student
    ):
        # Ensure a settings row exists (lazily created on first GET) with the
        # documented defaults: notify on absence, threshold 3.
        settings = school["client"].get("/api/v1/attendance/settings")
        assert settings.status_code == 200, settings.text
        assert settings.json()["absence_threshold_notify"] == 3

        _assign_form_teacher(school, teacher, klass, subject, academic_session)
        _link_parent(school, student["id"])

        for i, mark_date in enumerate(["2099-09-01", "2099-09-02", "2099-09-03"], start=1):
            res = teacher["client"].post("/api/v1/attendance/mark", json={
                "class_id": klass["id"], "session_id": academic_session["id"], "term_id": term["id"],
                "attendance_date": mark_date,
                "records": [{"student_id": student["id"], "status": "absent"}],
            })
            assert res.status_code == 201, f"mark #{i} failed: {res.text}"

    def test_marking_late_succeeds_with_linked_parent_and_notify_on_late_enabled(
        self, school, teacher, klass, subject, academic_session, term, student
    ):
        settings = school["client"].put("/api/v1/attendance/settings", json={
            "notify_parents_on_late": True,
        })
        assert settings.status_code == 200, settings.text

        _assign_form_teacher(school, teacher, klass, subject, academic_session)
        _link_parent(school, student["id"])

        res = teacher["client"].post("/api/v1/attendance/mark", json={
            "class_id": klass["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "attendance_date": "2099-09-04",
            "records": [{"student_id": student["id"], "status": "late", "minutes_late": 10}],
        })
        assert res.status_code == 201, res.text

        # Restore the shared settings row so later tests in this run see the
        # documented default again.
        restore = school["client"].put("/api/v1/attendance/settings", json={
            "notify_parents_on_late": False,
        })
        assert restore.status_code == 200, restore.text

    def test_marking_absent_with_no_linked_parent_still_succeeds(
        self, school, teacher, klass, subject, academic_session, term, student
    ):
        _assign_form_teacher(school, teacher, klass, subject, academic_session)

        res = teacher["client"].post("/api/v1/attendance/mark", json={
            "class_id": klass["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "attendance_date": "2099-09-05",
            "records": [{"student_id": student["id"], "status": "absent"}],
        })
        assert res.status_code == 201, res.text
