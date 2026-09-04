"""
Publishing a report card best-effort emails linked parents
(_notify_parents_report_published in grading.py). No test mailbox and
RESEND_API_KEY isn't set in test runs, so send_email() is a logged no-op -
this only verifies the endpoint still succeeds end-to-end (including the
parent_student_links -> parents embed query) when a parent actually is
linked, which is the path most likely to blow up.
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


class TestReportCardPublishNotifiesLinkedParent:
    def test_publish_succeeds_with_a_linked_parent(
        self, school, klass, subject, academic_session, term, student
    ):
        _link_parent(school, student["id"])

        report = school["client"].post("/api/v1/grading/report-cards/generate", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
        })
        assert report.status_code == 201, report.text

        publish = school["client"].post(f"/api/v1/grading/report-cards/{report.json()['id']}/publish")
        assert publish.status_code == 200, publish.text

    def test_publish_succeeds_with_no_linked_parent(
        self, school, klass, subject, academic_session, term, student
    ):
        report = school["client"].post("/api/v1/grading/report-cards/generate", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
        })
        assert report.status_code == 201, report.text

        publish = school["client"].post(f"/api/v1/grading/report-cards/{report.json()['id']}/publish")
        assert publish.status_code == 200, publish.text
