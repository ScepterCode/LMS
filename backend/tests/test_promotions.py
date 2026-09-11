"""
Tests for end-of-session promotion / graduation
(app/api/v1/endpoints/promotions.py).
"""
import itertools
import random
import pytest

from tests.conftest import unique, make_teacher

# `school` is a session-scoped fixture shared by every test in the run, so
# every test's classes land in the same org. sequence_order only makes
# sense as a *globally unique* position within one org (that's how a real
# school sets it up once), so tests can't all reuse literal 1/2 without
# colliding and picking up each other's "next class" - hand out a fresh,
# never-repeated pair of numbers per test instead.
_sequence_counter = itertools.count(random.randint(100_000, 999_999))


def next_sequence_pair():
    return next(_sequence_counter), next(_sequence_counter)


@pytest.fixture
def promotion_session(school):
    """A session using the default policy: 3rd term only, 40% pass mark."""
    client = school["client"]
    res = client.post("/api/v1/sessions", json={
        "name": unique("2099/2100"), "start_date": "2099-09-01", "end_date": "2100-07-31",
        "is_current": True,
    })
    assert res.status_code == 201, res.text
    return res.json()


def make_term(school, session, term_number, name="3rd Term"):
    client = school["client"]
    res = client.post("/api/v1/terms", json={
        "session_id": session["id"], "name": name, "term_number": term_number,
        "start_date": "2100-01-01", "end_date": "2100-03-31", "is_current": term_number == 3,
    })
    assert res.status_code == 201, res.text
    return res.json()


def make_class(school, sequence_order=None, is_graduating_class=False):
    client = school["client"]
    payload = {"name": unique("Class"), "level": "Junior", "section": "A", "capacity": 40}
    if sequence_order is not None:
        payload["sequence_order"] = sequence_order
    if is_graduating_class:
        payload["is_graduating_class"] = True
    res = client.post("/api/v1/classes", json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def make_student(school, klass):
    client = school["client"]
    res = client.post("/api/v1/students", json={
        "admission_number": unique("ADM"), "first_name": "Test", "last_name": "Student",
        "date_of_birth": "2015-01-01", "gender": "Male", "current_class_id": klass["id"],
    })
    assert res.status_code == 201, res.text
    return res.json()


def make_report_card(supabase, org_id, student, session, term, klass, average_score):
    supabase.table("report_cards").insert({
        "organization_id": org_id,
        "student_id": student["id"],
        "session_id": session["id"],
        "term_id": term["id"],
        "class_id": klass["id"],
        "average_score": average_score,
    }).execute()


def test_preview_computes_promote_repeat_and_graduate(school, supabase, promotion_session):
    client = school["client"]
    org_id = school["org_id"]
    term3 = make_term(school, promotion_session, 3)

    seq1, seq2 = next_sequence_pair()
    junior = make_class(school, sequence_order=seq1)
    senior_graduating = make_class(school, sequence_order=seq2, is_graduating_class=True)

    passer = make_student(school, junior)
    repeater = make_student(school, junior)
    graduate = make_student(school, senior_graduating)

    make_report_card(supabase, org_id, passer, promotion_session, term3, junior, 65)
    make_report_card(supabase, org_id, repeater, promotion_session, term3, junior, 25)
    make_report_card(supabase, org_id, graduate, promotion_session, term3, senior_graduating, 70)

    res = client.get("/api/v1/promotions/preview", params={"session_id": promotion_session["id"]})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["promotion_basis"] == "third_term"
    assert body["default_pass_mark"] == 40.0

    rows_by_student = {r["student_id"]: r for r in body["rows"]}

    passer_row = rows_by_student[passer["id"]]
    assert passer_row["decision"] == "promoted"
    assert passer_row["to_class_id"] == senior_graduating["id"]
    assert passer_row["has_data"] is True

    repeater_row = rows_by_student[repeater["id"]]
    assert repeater_row["decision"] == "repeated"
    assert repeater_row["to_class_id"] is None

    graduate_row = rows_by_student[graduate["id"]]
    assert graduate_row["decision"] == "graduated"
    assert graduate_row["to_class_id"] is None


def test_preview_defaults_to_repeat_when_no_report_card(school, promotion_session):
    client = school["client"]
    make_term(school, promotion_session, 3)
    junior = make_class(school, sequence_order=1)
    student = make_student(school, junior)

    res = client.get("/api/v1/promotions/preview", params={"session_id": promotion_session["id"]})
    assert res.status_code == 200, res.text
    row = next(r for r in res.json()["rows"] if r["student_id"] == student["id"])
    assert row["has_data"] is False
    assert row["decision"] == "repeated"


def test_cumulative_basis_averages_all_terms(school, supabase):
    client = school["client"]
    org_id = school["org_id"]
    res = client.post("/api/v1/sessions", json={
        "name": unique("2099/2100"), "start_date": "2099-09-01", "end_date": "2100-07-31",
        "is_current": True, "promotion_basis": "cumulative", "promotion_pass_mark": 50,
    })
    assert res.status_code == 201, res.text
    session = res.json()
    assert session["promotion_basis"] == "cumulative"
    assert session["promotion_pass_mark"] == 50.0

    t1 = make_term(school, session, 1, "1st Term")
    t2 = make_term(school, session, 2, "2nd Term")
    t3 = make_term(school, session, 3, "3rd Term")
    klass = make_class(school, sequence_order=1)
    student = make_student(school, klass)

    # Average of 40/50/60 = 50, exactly meets the 50% pass mark.
    make_report_card(supabase, org_id, student, session, t1, klass, 40)
    make_report_card(supabase, org_id, student, session, t2, klass, 50)
    make_report_card(supabase, org_id, student, session, t3, klass, 60)

    res = client.get("/api/v1/promotions/preview", params={"session_id": session["id"]})
    assert res.status_code == 200, res.text
    row = next(r for r in res.json()["rows"] if r["student_id"] == student["id"])
    assert row["basis_score"] == 50.0
    assert row["decision"] == "promoted"


def test_commit_applies_decisions_and_records_history(school, supabase, promotion_session):
    client = school["client"]
    org_id = school["org_id"]
    term3 = make_term(school, promotion_session, 3)
    seq1, seq2 = next_sequence_pair()
    junior = make_class(school, sequence_order=seq1)
    senior_graduating = make_class(school, sequence_order=seq2, is_graduating_class=True)

    passer = make_student(school, junior)
    repeater = make_student(school, junior)
    graduate = make_student(school, senior_graduating)

    make_report_card(supabase, org_id, passer, promotion_session, term3, junior, 65)
    make_report_card(supabase, org_id, repeater, promotion_session, term3, junior, 25)
    make_report_card(supabase, org_id, graduate, promotion_session, term3, senior_graduating, 70)

    preview = client.get(
        "/api/v1/promotions/preview", params={"session_id": promotion_session["id"]}
    ).json()

    decisions = [
        {
            "student_id": r["student_id"], "decision": r["decision"],
            "to_class_id": r["to_class_id"], "basis_score": r["basis_score"],
        }
        for r in preview["rows"]
    ]

    res = client.post("/api/v1/promotions/commit", json={
        "session_id": promotion_session["id"], "decisions": decisions,
    })
    assert res.status_code == 200, res.text
    body = res.json()
    # The `school` fixture is session-scoped and shared with every other
    # test in the run, so other tests' leftover students (still "active",
    # no report card for *this* session) show up in the org-wide preview
    # too and default to "repeated" - assert on failure count and this
    # test's own three students rather than exact totals.
    assert body["failed"] == 0
    results_by_student = {r["student_id"]: r for r in body["results"]}
    assert results_by_student[passer["id"]] == {
        "student_id": passer["id"], "decision": "promoted", "success": True, "error": None,
    }
    assert results_by_student[repeater["id"]]["decision"] == "repeated"
    assert results_by_student[repeater["id"]]["success"] is True
    assert results_by_student[graduate["id"]]["decision"] == "graduated"
    assert results_by_student[graduate["id"]]["success"] is True

    passer_after = client.get(f"/api/v1/students/{passer['id']}").json()
    assert passer_after["current_class_id"] == senior_graduating["id"]

    repeater_after = client.get(f"/api/v1/students/{repeater['id']}").json()
    assert repeater_after["current_class_id"] == junior["id"]

    graduate_after = client.get(f"/api/v1/students/{graduate['id']}").json()
    assert graduate_after["status"] == "graduated"

    history = client.get(
        "/api/v1/promotions/history", params={"session_id": promotion_session["id"]}
    )
    assert history.status_code == 200, history.text
    decisions_by_student = {h["student_id"]: h["decision"] for h in history.json()}
    assert decisions_by_student[passer["id"]] == "promoted"
    assert decisions_by_student[repeater["id"]] == "repeated"
    assert decisions_by_student[graduate["id"]] == "graduated"


def test_commit_rerun_replaces_prior_decision(school, supabase, promotion_session):
    """Re-committing for the same session/student updates the record
    instead of erroring or duplicating it."""
    client = school["client"]
    org_id = school["org_id"]
    term3 = make_term(school, promotion_session, 3)
    junior = make_class(school, sequence_order=1)
    senior = make_class(school, sequence_order=2)
    student = make_student(school, junior)
    make_report_card(supabase, org_id, student, promotion_session, term3, junior, 25)

    first = client.post("/api/v1/promotions/commit", json={
        "session_id": promotion_session["id"],
        "decisions": [{"student_id": student["id"], "decision": "repeated"}],
    })
    assert first.status_code == 200 and first.json()["repeated"] == 1

    second = client.post("/api/v1/promotions/commit", json={
        "session_id": promotion_session["id"],
        "decisions": [{
            "student_id": student["id"], "decision": "promoted", "to_class_id": senior["id"],
            "override_reason": "Admin override after manual review",
        }],
    })
    assert second.status_code == 200 and second.json()["promoted"] == 1

    history = client.get(
        "/api/v1/promotions/history", params={"session_id": promotion_session["id"]}
    ).json()
    matching = [h for h in history if h["student_id"] == student["id"]]
    assert len(matching) == 1
    assert matching[0]["decision"] == "promoted"
    assert matching[0]["overridden"] is True


def test_commit_promoted_without_target_class_fails_that_row(school, supabase, promotion_session):
    client = school["client"]
    org_id = school["org_id"]
    term3 = make_term(school, promotion_session, 3)
    junior = make_class(school, sequence_order=1)
    student = make_student(school, junior)
    make_report_card(supabase, org_id, student, promotion_session, term3, junior, 65)

    res = client.post("/api/v1/promotions/commit", json={
        "session_id": promotion_session["id"],
        "decisions": [{"student_id": student["id"], "decision": "promoted"}],
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["failed"] == 1
    assert body["results"][0]["success"] is False


def test_teacher_cannot_access_promotions(school, promotion_session):
    teacher = make_teacher(school)
    res = teacher["client"].get(
        "/api/v1/promotions/preview", params={"session_id": promotion_session["id"]}
    )
    assert res.status_code == 403
