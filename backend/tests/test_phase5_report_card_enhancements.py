"""
Integration tests for Phase 5: report card enhancements - school branding
(logo/motto/address), admin-configurable skill categories, form-teacher
skill ratings, and the new attendance-detail fields on report cards.

Same conventions as test_phase4_features.py: real FastAPI app via
TestClient against the real Supabase project, no mocking.
"""
import base64

from tests.conftest import make_teacher, unique

# A minimal valid 1x1 PNG, reused for logo upload tests.
_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8A"
    "AQUBAScY42YAAAAASUVORK5CYII="
)


# ============================================
# ORGANIZATION BRANDING
# ============================================

class TestOrganizationBranding:
    def test_admin_can_update_school_details(self, school):
        client = school["client"]
        res = client.patch(f"/api/v1/organizations/{school['org_id']}", json={
            "motto": "Excellence Through Diligence",
            "address": "12 Unity Road, Ikeja, Lagos",
            "phone": "+2348012345678",
        })
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["motto"] == "Excellence Through Diligence"
        assert body["address"] == "12 Unity Road, Ikeja, Lagos"

    def test_teacher_cannot_update_school_details(self, school, teacher):
        res = teacher["client"].patch(f"/api/v1/organizations/{school['org_id']}", json={
            "motto": "Should not be allowed",
        })
        assert res.status_code == 403, res.text

    def test_admin_can_upload_logo(self, school):
        client = school["client"]
        res = client.post(
            f"/api/v1/organizations/{school['org_id']}/logo",
            files={"file": ("logo.png", _PNG_BYTES, "image/png")},
        )
        assert res.status_code == 200, res.text
        assert res.json()["logo_url"].startswith("http")

    def test_logo_upload_rejects_non_image_content_type(self, school):
        client = school["client"]
        res = client.post(
            f"/api/v1/organizations/{school['org_id']}/logo",
            files={"file": ("notes.txt", b"not an image", "text/plain")},
        )
        assert res.status_code == 422, res.text

    def test_logo_upload_rejects_oversized_file(self, school):
        client = school["client"]
        oversized = b"0" * (2 * 1024 * 1024 + 1)
        res = client.post(
            f"/api/v1/organizations/{school['org_id']}/logo",
            files={"file": ("big.png", oversized, "image/png")},
        )
        assert res.status_code == 422, res.text

    def test_teacher_cannot_upload_logo(self, school, teacher):
        res = teacher["client"].post(
            f"/api/v1/organizations/{school['org_id']}/logo",
            files={"file": ("logo.png", _PNG_BYTES, "image/png")},
        )
        assert res.status_code == 403, res.text


# ============================================
# SKILL CATEGORIES (admin-configurable trait list)
# ============================================

class TestSkillCategories:
    def test_admin_can_create_and_list_category(self, school):
        client = school["client"]
        name = unique("Sports & Games")
        create = client.post("/api/v1/skills/categories", json={
            "name": name, "domain": "psychomotor", "display_order": 1,
        })
        assert create.status_code == 201, create.text
        assert create.json()["domain"] == "psychomotor"

        listed = client.get("/api/v1/skills/categories")
        assert listed.status_code == 200, listed.text
        assert any(c["name"] == name for c in listed.json())

    def test_teacher_cannot_create_category(self, school, teacher):
        res = teacher["client"].post("/api/v1/skills/categories", json={
            "name": unique("Handwriting"), "domain": "psychomotor",
        })
        assert res.status_code == 403, res.text

    def test_duplicate_category_name_rejected(self, school):
        client = school["client"]
        name = unique("Punctuality")
        first = client.post("/api/v1/skills/categories", json={"name": name, "domain": "affective"})
        assert first.status_code == 201, first.text

        second = client.post("/api/v1/skills/categories", json={"name": name, "domain": "affective"})
        assert second.status_code == 422, second.text

    def test_invalid_domain_rejected(self, school):
        client = school["client"]
        res = client.post("/api/v1/skills/categories", json={
            "name": unique("Bad Domain"), "domain": "not-a-real-domain",
        })
        assert res.status_code == 422, res.text

    def test_deactivated_category_excluded_from_default_list(self, school):
        client = school["client"]
        create = client.post("/api/v1/skills/categories", json={
            "name": unique("Neatness"), "domain": "affective",
        })
        assert create.status_code == 201, create.text
        category_id = create.json()["id"]

        deactivate = client.patch(f"/api/v1/skills/categories/{category_id}", json={"is_active": False})
        assert deactivate.status_code == 200, deactivate.text
        assert deactivate.json()["is_active"] is False

        active_only = client.get("/api/v1/skills/categories").json()
        assert not any(c["id"] == category_id for c in active_only)

        including_inactive = client.get("/api/v1/skills/categories?include_inactive=true").json()
        assert any(c["id"] == category_id for c in including_inactive)


# ============================================
# DEFAULT SKILL CATEGORY SEEDING
# ============================================
# A one-time migration originally seeded the 7 default traits, but only for
# organizations that existed at the time it ran - every school registered
# afterwards got an empty, unconfigured skills list. seed_default_skill_categories()
# now runs at org-creation time instead (both register_school and the
# system-admin assisted onboarding path).

class TestDefaultSkillCategorySeeding:
    def test_freshly_registered_school_has_default_categories(self, school):
        client = school["client"]
        res = client.get("/api/v1/skills/categories")
        assert res.status_code == 200, res.text
        names = {c["name"] for c in res.json()}
        domains = {c["name"]: c["domain"] for c in res.json()}

        expected = {
            "Sports & Games": "psychomotor",
            "Handling of Tools/Equipment": "psychomotor",
            "Handwriting": "psychomotor",
            "Musical Skills": "psychomotor",
            "Punctuality": "affective",
            "Neatness": "affective",
            "Honesty": "affective",
        }
        for name, domain in expected.items():
            assert name in names, f"missing default trait {name!r}"
            assert domains[name] == domain


# ============================================
# STUDENT SKILL RATINGS (form-teacher permission)
# ============================================

class TestSkillRatings:
    def _assign_form_teacher(self, school, teacher, klass, subject, academic_session):
        res = school["client"].post("/api/v1/teacher-management/teacher-assignments", json={
            "teacher_id": teacher["teacher"]["id"], "class_id": klass["id"],
            "subject_id": subject["id"], "session_id": academic_session["id"],
            "is_form_teacher": True,
        })
        assert res.status_code == 201, res.text

    def test_form_teacher_can_submit_ratings_for_own_class(
        self, school, teacher, klass, subject, academic_session, term, student
    ):
        self._assign_form_teacher(school, teacher, klass, subject, academic_session)

        category = school["client"].post("/api/v1/skills/categories", json={
            "name": unique("Sports & Games"), "domain": "psychomotor",
        })
        assert category.status_code == 201, category.text

        res = teacher["client"].post("/api/v1/skills/ratings/bulk", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "ratings": [{"skill_category_id": category.json()["id"], "rating": 5}],
        })
        assert res.status_code == 201, res.text
        assert res.json()["ratings"][0]["rating"] == 5

    def test_non_form_teacher_cannot_submit_ratings(
        self, school, teacher, klass, academic_session, term, student
    ):
        """The exact permission check verified manually earlier: a teacher who
        isn't the form teacher of the student's class must be rejected."""
        category = school["client"].post("/api/v1/skills/categories", json={
            "name": unique("Handling of Tools"), "domain": "psychomotor",
        })
        assert category.status_code == 201, category.text

        res = teacher["client"].post("/api/v1/skills/ratings/bulk", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "ratings": [{"skill_category_id": category.json()["id"], "rating": 3}],
        })
        assert res.status_code == 403, res.text

    def test_admin_can_submit_ratings_for_any_class(
        self, school, klass, subject, academic_session, term, student
    ):
        client = school["client"]
        category = client.post("/api/v1/skills/categories", json={
            "name": unique("Honesty"), "domain": "affective",
        })
        assert category.status_code == 201, category.text

        res = client.post("/api/v1/skills/ratings/bulk", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "ratings": [{"skill_category_id": category.json()["id"], "rating": 4}],
        })
        assert res.status_code == 201, res.text

    def test_get_student_ratings_enriched_with_category_name_and_domain(
        self, school, klass, academic_session, term, student
    ):
        client = school["client"]
        category = client.post("/api/v1/skills/categories", json={
            "name": unique("Musical Skills"), "domain": "psychomotor",
        })
        assert category.status_code == 201, category.text

        submit = client.post("/api/v1/skills/ratings/bulk", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "ratings": [{"skill_category_id": category.json()["id"], "rating": 2}],
        })
        assert submit.status_code == 201, submit.text

        res = client.get(
            f"/api/v1/skills/student/{student['id']}"
            f"?session_id={academic_session['id']}&term_id={term['id']}"
        )
        assert res.status_code == 200, res.text
        ratings = res.json()
        assert len(ratings) == 1
        assert ratings[0]["category_name"] == category.json()["name"]
        assert ratings[0]["domain"] == "psychomotor"
        assert ratings[0]["rating"] == 2


# ============================================
# REPORT CARD ENHANCED FIELDS
# ============================================

class TestReportCardEnhancedFields:
    def test_generated_report_card_includes_attendance_detail_fields(
        self, school, klass, academic_session, term, student
    ):
        client = school["client"]
        res = client.post("/api/v1/grading/report-cards/generate", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
        })
        assert res.status_code == 201, res.text
        body = res.json()
        # No attendance was marked for this student/term, so these should
        # default sanely rather than being absent or raising a KeyError.
        assert body["days_excused"] == 0
        assert body["attendance_percentage"] is None
        assert body["punctuality_percentage"] is None

    def test_report_card_reflects_marked_attendance_percentages(
        self, school, klass, academic_session, term, student
    ):
        client = school["client"]
        mark = client.post("/api/v1/attendance/mark", json={
            "class_id": klass["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "attendance_date": "2099-09-10",
            "records": [{"student_id": student["id"], "status": "present"}],
        })
        assert mark.status_code == 201, mark.text

        res = client.post("/api/v1/grading/report-cards/generate", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
        })
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["days_present"] == 1
        assert float(body["attendance_percentage"]) == 100.0
        assert float(body["punctuality_percentage"]) == 100.0

    def test_get_report_card_includes_skill_ratings(
        self, school, klass, academic_session, term, student
    ):
        client = school["client"]
        category = client.post("/api/v1/skills/categories", json={
            "name": unique("Drawing"), "domain": "psychomotor",
        })
        assert category.status_code == 201, category.text

        generate = client.post("/api/v1/grading/report-cards/generate", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
        })
        assert generate.status_code == 201, generate.text
        report_card_id = generate.json()["id"]

        submit = client.post("/api/v1/skills/ratings/bulk", json={
            "student_id": student["id"], "session_id": academic_session["id"], "term_id": term["id"],
            "ratings": [{"skill_category_id": category.json()["id"], "rating": 5}],
        })
        assert submit.status_code == 201, submit.text

        res = client.get(f"/api/v1/grading/report-cards/{report_card_id}")
        assert res.status_code == 200, res.text
        skill_ratings = res.json()["skill_ratings"]
        assert len(skill_ratings) == 1
        assert skill_ratings[0]["category_name"] == category.json()["name"]
        assert skill_ratings[0]["rating"] == 5
