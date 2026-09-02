# Fee Management — Roadmap

**Architecture decision (settled):** keep the two-level model — **Fee Categories**
(generic fee types: Tuition, Uniform, Books) + **Fee Structures** (specific amount
per class/level/session). Complexity is hidden behind wizards and bulk operations,
not removed. See "Rejected" at the bottom.

Last reconciled with the code: **2026-09-02**.

> Phases 2.2–3.5 plus session comparison and Excel export were built on branch
> `feature/fee-management-phases` (10 commits `ff87da2`..`a947070`). Backend
> tested in `backend/tests/test_fee_management.py` (20, green). Only Phase 4
> remains.

---

## Phase 1 — Core CRUD ✅ COMPLETE

| Feature | Backend | Frontend |
|---|---|---|
| Category create / list | ✅ | ✅ |
| Category update | ✅ `PUT /fees/categories/{id}` (admin/bursar, org-scoped) | ✅ edit modal |
| Category delete | ✅ `DELETE /fees/categories/{id}` — blocked if any structure uses it | ✅ delete button |
| Structure create / list | ✅ | ✅ |
| Structure update | ✅ `PUT /fees/structures/{id}` (amount, due_date, is_active, discount fields) | ✅ edit modal (commit `f53e744`) |
| Structure delete | ✅ `DELETE /fees/structures/{id}` — blocked if any student_fee references it | ✅ delete button |
| `fee_structures` FKs (`class_id`→classes, `session_id`→academic_sessions) | ✅ applied on live DB (`database/phase12_fee_structures_missing_fks.sql`) | — |

Note: `FeeStructureUpdate` deliberately does **not** accept
category/session/class/payment_frequency — changing those after students have fees
assigned is a data-integrity hazard, so the edit modal tells the user to delete +
recreate instead.

---

## Phase 2 — Smart UX ✅ COMPLETE

### 2.1 Quick Fee Setup Wizard ✅ (commit `475e20c`)
Single form creates category + structure together, optional immediate assignment.
Frontend modal in `frontend/app/dashboard/fees/page.tsx`.

### 2.2 Bulk Fee Creation ✅ (commit `3413f2a`)
`POST /fees/structures/bulk-create` — one structure per class in `items`, sharing
category/session/frequency/due-date. INSERT-only; verifies the category, session
and every class belong to the org; refuses the whole batch if any target class
already has a structure for that category+session. Frontend "Bulk Add" modal:
class checklist + per-class amount + fill-all shortcut.

### 2.3 Copy from Previous Session ✅ (commit `3413f2a`)
`POST /fees/structures/copy-session` — clones every active structure from one
session into another with an optional percentage/fixed adjustment. Skips any
(category, class, class_level) already in the target, so it's safe to re-run.
Frontend "Copy from Session" modal.

### 2.4 Structure Filtering & Search ✅ (commit `ff87da2`)
Client-side filter bar: text search (category/class), session / class / category
dropdowns, status, sort (amount / category). "X of Y" count + active-filter badge
+ Clear. URL persistence not done (state only).

---

## Phase 3 — Advanced ✅ COMPLETE (except templates/audit — see Phase 4)

- **3.1 Structure detail view** ✅ (`f45ae03`) — `GET /fees/structures/{id}/detail`
  (read-only, admin/bursar, org-scoped): the structure + every student_fee on it,
  with totals (expected / collected / outstanding), collection rate and a
  per-status breakdown. Frontend "Details" button + modal. ("Assign to students"
  shortcut from the modal not added.)
- **3.2 Structure bulk operations** ✅ (`a947070`) — row checkboxes + select-all,
  bulk activate / deactivate / delete (loops the existing per-row
  `PUT`/`DELETE` endpoints client-side; per-row failures reported, batch not
  aborted). Per-row **Duplicate** → `POST /fees/structures/{id}/duplicate`
  (INSERT-only, org-scoped, refuses if the target session already has one for
  that category+class, optional amount override).
- **3.3 Export** ✅ (`eea684b` CSV, `a947070` Excel) — client-side, honours the
  active filters. CSV (UTF-8 BOM, CRLF) and `.xls` (inline SpreadsheetML 2003, no
  library — amounts as real number cells). No backend export endpoint.
- **3.4 Enhanced validation** ✅ (`5ee8205`) — `POST /fees/structures` now
  verifies category/session/class belong to the org, rejects duplicates
  (category + session + scope) with 400, and caps `amount` at 1e9 (model-level,
  also applies to bulk-create). Create modal shows an inline duplicate warning
  and disables submit. Due-date-not-in-past deliberately **not** enforced
  (backdating / mid-year onboarding are legitimate).
- **3.5 Fee analytics** ✅ (`98a4ad5` breakdown, `86a3d86` comparison) — built
  onto the existing `/dashboard/fees/reports` page (not a new `/analytics`
  page): a "Structure Breakdown" view (count/active, average, highest, total fee
  value by category as bars, per-class table) and a "Session Comparison" view
  (two-session picker, per category+class amount diff with % change, New/Removed
  markers). Session selector on the page re-scopes both. Trend charts not done.

---

## Phase 4 — Future (only if needed)

- Fee templates ("apply standard setup") — needs a `fee_templates` table
- `fee_structure_history` audit table + "view history" UI — needs the table and
  hooks on every fee write

---

## Rejected

**Adding `class_id` + `amount` directly to `fee_categories`.** It makes categories
do two jobs, loses per-session tracking, and makes cross-class/cross-year reporting
hard. If a genuinely single-level UX is ever wanted, revisit as a real migration
with `session_id` included — but the Quick Setup Wizard already gives the
one-step feel without the schema change.

---

## Reference

- Endpoints: `backend/app/api/v1/endpoints/fees.py`
- Models: `backend/app/models/fees.py`
- Tests: `backend/tests/test_fee_management.py`
- Frontend: `frontend/app/dashboard/fees/page.tsx`, `.../fees/payments/page.tsx`,
  `.../fees/reports/page.tsx`
- Schema: `database/phase3_fees_schema.sql`, `database/phase12_fee_structures_missing_fks.sql`
