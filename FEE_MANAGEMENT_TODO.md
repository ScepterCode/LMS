# Fee Management — Roadmap

**Architecture decision (settled):** keep the two-level model — **Fee Categories**
(generic fee types: Tuition, Uniform, Books) + **Fee Structures** (specific amount
per class/level/session). Complexity is hidden behind wizards and bulk operations,
not removed. See "Rejected" at the bottom.

Last reconciled with the code: **2026-09-02**.

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

## Phase 2 — Smart UX (partially started)

### 2.1 Quick Fee Setup Wizard ✅ DONE (commit `475e20c`)
Single form creates category + structure together, optional immediate assignment.
Frontend: modal in `frontend/app/dashboard/fees/page.tsx`.

### 2.2 Bulk Fee Creation — NOT BUILT
Apply one category to multiple classes at once, per-class amounts, "same amount for
all" shortcut. Backend: extend `POST /fees/structures/bulk-assign` or add
`bulk-create`. Frontend: checkbox+amount list modal. ~3–4 h.

### 2.3 Copy from Previous Session — NOT BUILT
`POST /fees/structures/copy-session` (source/target session, % or fixed adjustment,
optional class filter). Frontend: modal with old-vs-new preview. ~3–4 h.

### 2.4 Structure Filtering & Search — NOT BUILT
Filter panel (session / class / category / status), search, sort, URL-persisted
filters, active-filter badge. Frontend only. ~2–3 h.

---

## Phase 3 — Advanced (not started)

- **3.1 Structure detail view** — per-structure: assigned students, expected vs
  collected, % paid/pending/overdue, "assign to students" shortcut. ~1–2 h.
- **3.2 Structure bulk operations** — row checkboxes, bulk activate/deactivate/
  delete, per-row "duplicate to another session". `PATCH …/bulk-toggle-active`,
  `POST …/{id}/duplicate`. ~3–4 h.
- **3.3 Export** — `GET /fees/structures/export?format=csv|excel`, honours active
  filters. ~2–3 h.
- **3.4 Enhanced validation** — block duplicate (category+class+session), amount
  sanity cap, due-date-not-in-past, overlap warnings, inline field errors. ~1–2 h.
- **3.5 Fee analytics dashboard** — `/dashboard/fees/analytics`: expected-revenue
  cards, fees-by-category / distribution / trend charts, year-over-year table. ~4–5 h.

---

## Phase 4 — Future (only if needed)

- Fee templates ("apply standard setup")
- `fee_structure_history` audit table + "view history" UI
- Fee comparison tool (side-by-side across sessions)

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
- Frontend: `frontend/app/dashboard/fees/page.tsx`, `.../fees/payments/page.tsx`
- Schema: `database/phase3_fees_schema.sql`, `database/phase12_fee_structures_missing_fks.sql`
