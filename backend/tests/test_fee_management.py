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


def _class(school, name_prefix="CLS"):
    res = school["client"].post("/api/v1/classes", json={
        "name": unique(name_prefix), "level": "Junior", "section": "A", "capacity": 40,
    })
    assert res.status_code == 201, res.text
    return res.json()


def _session(school):
    res = school["client"].post("/api/v1/sessions", json={
        "name": unique("2098/2099"), "start_date": "2098-09-01", "end_date": "2099-07-31",
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


class TestFeeStructureValidation:
    def test_duplicate_structure_rejected(self, school, academic_session, klass):
        category = _category(school)
        _structure(school, category, academic_session, klass)

        res = school["client"].post("/api/v1/fees/structures", json={
            "fee_category_id": category["id"], "session_id": academic_session["id"],
            "class_id": klass["id"], "amount": 99999, "payment_frequency": "termly",
        })
        assert res.status_code == 400, res.text

    def test_foreign_category_rejected(self, school, academic_session, klass):
        res = school["client"].post("/api/v1/fees/structures", json={
            "fee_category_id": "00000000-0000-0000-0000-000000000000",
            "session_id": academic_session["id"], "class_id": klass["id"], "amount": 50000,
        })
        assert res.status_code == 404, res.text

    def test_absurd_amount_rejected(self, school, academic_session, klass):
        category = _category(school)
        res = school["client"].post("/api/v1/fees/structures", json={
            "fee_category_id": category["id"], "session_id": academic_session["id"],
            "class_id": klass["id"], "amount": 5_000_000_000,
        })
        assert res.status_code == 422, res.text


class TestBulkCreateFeeStructures:
    def test_creates_one_structure_per_class(self, school, academic_session):
        category = _category(school)
        c1, c2, c3 = _class(school), _class(school), _class(school)

        res = school["client"].post("/api/v1/fees/structures/bulk-create", json={
            "fee_category_id": category["id"], "session_id": academic_session["id"],
            "payment_frequency": "termly",
            "items": [
                {"class_id": c1["id"], "amount": 50000},
                {"class_id": c2["id"], "amount": 55000},
                {"class_id": c3["id"], "amount": 60000},
            ],
        })
        assert res.status_code == 201, res.text
        assert res.json()["created"] == 3

        listed = school["client"].get(
            f"/api/v1/fees/structures?session_id={academic_session['id']}"
        ).json()
        amounts = sorted(float(s["amount"]) for s in listed if s["fee_category_id"] == category["id"])
        assert amounts == [50000, 55000, 60000]

    def test_rejects_batch_if_a_class_already_has_a_structure(self, school, academic_session, klass):
        category = _category(school)
        _structure(school, category, academic_session, klass, amount=1000)
        other = _class(school)

        res = school["client"].post("/api/v1/fees/structures/bulk-create", json={
            "fee_category_id": category["id"], "session_id": academic_session["id"],
            "items": [
                {"class_id": klass["id"], "amount": 50000},
                {"class_id": other["id"], "amount": 50000},
            ],
        })
        assert res.status_code == 400, res.text
        # nothing from the batch should have been created
        listed = school["client"].get(
            f"/api/v1/fees/structures?session_id={academic_session['id']}"
        ).json()
        assert not any(s["class_id"] == other["id"] for s in listed)

    def test_foreign_class_rejected(self, school, academic_session):
        category = _category(school)
        res = school["client"].post("/api/v1/fees/structures/bulk-create", json={
            "fee_category_id": category["id"], "session_id": academic_session["id"],
            "items": [{"class_id": "00000000-0000-0000-0000-000000000000", "amount": 50000}],
        })
        assert res.status_code == 404, res.text

    def test_non_finance_role_rejected(self, school, academic_session):
        category = _category(school)
        c1 = _class(school)
        registrar = make_registrar(school)
        res = registrar["client"].post("/api/v1/fees/structures/bulk-create", json={
            "fee_category_id": category["id"], "session_id": academic_session["id"],
            "items": [{"class_id": c1["id"], "amount": 50000}],
        })
        assert res.status_code == 403, res.text


class TestCopyFeeStructuresToSession:
    def test_copies_active_structures_with_percentage_adjustment(self, school, academic_session):
        category = _category(school)
        c1, c2 = _class(school), _class(school)
        school["client"].post("/api/v1/fees/structures/bulk-create", json={
            "fee_category_id": category["id"], "session_id": academic_session["id"],
            "items": [
                {"class_id": c1["id"], "amount": 100000},
                {"class_id": c2["id"], "amount": 200000},
            ],
        })
        target = _session(school)

        res = school["client"].post("/api/v1/fees/structures/copy-session", json={
            "source_session_id": academic_session["id"],
            "target_session_id": target["id"],
            "adjustment_type": "percentage", "adjustment_value": 10,
        })
        assert res.status_code == 201, res.text
        assert res.json()["created"] == 2

        listed = school["client"].get(
            f"/api/v1/fees/structures?session_id={target['id']}"
        ).json()
        amounts = sorted(round(float(s["amount"])) for s in listed if s["fee_category_id"] == category["id"])
        assert amounts == [110000, 220000]

    def test_second_run_is_idempotent(self, school, academic_session):
        category = _category(school)
        c1 = _class(school)
        _structure(school, category, academic_session, c1, amount=50000)
        target = _session(school)

        first = school["client"].post("/api/v1/fees/structures/copy-session", json={
            "source_session_id": academic_session["id"], "target_session_id": target["id"],
        })
        assert first.json()["created"] == 1

        second = school["client"].post("/api/v1/fees/structures/copy-session", json={
            "source_session_id": academic_session["id"], "target_session_id": target["id"],
        })
        assert second.status_code == 201, second.text
        assert second.json()["created"] == 0
        assert second.json()["skipped"] == 1

    def test_same_source_and_target_rejected(self, school, academic_session):
        res = school["client"].post("/api/v1/fees/structures/copy-session", json={
            "source_session_id": academic_session["id"],
            "target_session_id": academic_session["id"],
        })
        assert res.status_code == 400, res.text
