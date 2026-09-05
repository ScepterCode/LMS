"""
_sweep_overdue_fees (fees.py) best-effort emails parents of any fee it
flips to overdue on this call (see the docstring on that function for why
a row can only be caught by the sweep once). No test mailbox and
RESEND_API_KEY isn't set in test runs, so send_email() is a logged no-op -
this verifies the read that triggers the sweep still succeeds end-to-end,
including the batched category/parent lookups, when a fee actually is
overdue and has a linked parent.
"""
from datetime import date, timedelta

from tests.conftest import unique


def _category(school):
    res = school["client"].post("/api/v1/fees/categories", json={
        "name": unique("Tuition"), "code": unique("TUI")[:12].upper(), "is_mandatory": True,
    })
    assert res.status_code == 201, res.text
    return res.json()


def _structure(school, category, academic_session, klass, amount=50000):
    res = school["client"].post("/api/v1/fees/structures", json={
        "fee_category_id": category["id"], "session_id": academic_session["id"],
        "class_id": klass["id"], "amount": amount, "payment_frequency": "termly",
    })
    assert res.status_code == 201, res.text
    return res.json()


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


class TestFeeOverdueNotify:
    def test_reading_student_fees_flips_and_notifies_with_linked_parent(
        self, school, klass, subject, academic_session, student, caplog
    ):
        category = _category(school)
        structure = _structure(school, category, academic_session, klass)
        _link_parent(school, student["id"])

        past_due = (date.today() - timedelta(days=1)).isoformat()
        assign = school["client"].post("/api/v1/fees/student-fees", json={
            "student_id": student["id"], "fee_structure_id": structure["id"],
            "session_id": academic_session["id"], "amount": 50000, "final_amount": 50000,
            "due_date": past_due,
        })
        assert assign.status_code == 201, assign.text
        assert assign.json()["status"] == "pending"

        # Any read of student-fees triggers the sweep. _notify_parents_fees_overdue
        # logs an error on any exception in its own try/except - assert none
        # fired, so a silent failure inside the notify path (not just the
        # outer request, which the try/except protects regardless) shows up.
        caplog.clear()
        res = school["client"].get(
            "/api/v1/fees/student-fees", params={"student_id": student["id"]}
        )
        assert res.status_code == 200, res.text
        assert "Failed to send fee-overdue notification" not in caplog.text
        fees = [f for f in res.json() if f["id"] == assign.json()["id"]]
        assert len(fees) == 1
        assert fees[0]["status"] == "overdue"

        # A second read must not error either (this is the "already overdue,
        # no longer matches the sweep's WHERE clause" case).
        res2 = school["client"].get(
            "/api/v1/fees/student-fees", params={"student_id": student["id"]}
        )
        assert res2.status_code == 200, res2.text

    def test_reading_student_fees_flips_fine_with_no_linked_parent(
        self, school, klass, subject, academic_session, student
    ):
        category = _category(school)
        structure = _structure(school, category, academic_session, klass)

        past_due = (date.today() - timedelta(days=1)).isoformat()
        assign = school["client"].post("/api/v1/fees/student-fees", json={
            "student_id": student["id"], "fee_structure_id": structure["id"],
            "session_id": academic_session["id"], "amount": 30000, "final_amount": 30000,
            "due_date": past_due,
        })
        assert assign.status_code == 201, assign.text

        res = school["client"].get(
            "/api/v1/fees/student-fees", params={"student_id": student["id"]}
        )
        assert res.status_code == 200, res.text
