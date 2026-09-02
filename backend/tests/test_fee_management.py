"""
Fee management endpoints beyond basic CRUD.

Same conventions as the other suites: real FastAPI app via TestClient
against the real Supabase project, no mocking. `school["client"]` is a
logged-in admin.
"""
from tests.conftest import make_registrar, unique


def _category(school):
    res = school["client"].post("/api/v1/fees/categories", json={
        "name": unique("Tuition"), "code": unique("TUI")[:12].upper(),
        "description": "test", "is_mandatory": True,
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


def _assign(school, student, structure, academic_session, amount=50000):
    res = school["client"].post("/api/v1/fees/student-fees", json={
        "student_id": student["id"], "fee_structure_id": structure["id"],
        "session_id": academic_session["id"], "amount": amount, "final_amount": amount,
    })
    assert res.status_code == 201, res.text
    return res.json()


class TestFeeStructureDetail:
    def test_detail_reports_assigned_students_and_totals(
        self, school, academic_session, klass, student
    ):
        category = _category(school)
        structure = _structure(school, category, academic_session, klass, amount=40000)
        _assign(school, student, structure, academic_session, amount=40000)

        res = school["client"].get(f"/api/v1/fees/structures/{structure['id']}/detail")
        assert res.status_code == 200, res.text
        body = res.json()

        assert body["structure"]["id"] == structure["id"]
        assert body["structure"]["category_name"] == category["name"]
        assert body["stats"]["student_count"] == 1
        assert body["stats"]["total_expected"] == 40000
        assert body["stats"]["total_collected"] == 0
        assert body["stats"]["total_outstanding"] == 40000
        assert len(body["students"]) == 1
        assert body["students"][0]["student_id"] == student["id"]
        assert body["students"][0]["balance"] == 40000

    def test_detail_empty_when_no_students_assigned(
        self, school, academic_session, klass
    ):
        category = _category(school)
        structure = _structure(school, category, academic_session, klass)

        res = school["client"].get(f"/api/v1/fees/structures/{structure['id']}/detail")
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["stats"]["student_count"] == 0
        assert body["students"] == []

    def test_detail_404_for_unknown_structure(self, school):
        res = school["client"].get(
            "/api/v1/fees/structures/00000000-0000-0000-0000-000000000000/detail"
        )
        assert res.status_code == 404, res.text

    def test_detail_rejected_for_non_finance_roles(
        self, school, academic_session, klass
    ):
        category = _category(school)
        structure = _structure(school, category, academic_session, klass)

        registrar = make_registrar(school)
        res = registrar["client"].get(f"/api/v1/fees/structures/{structure['id']}/detail")
        assert res.status_code == 403, res.text
