# Learnlyf

School-administration platform for Nigerian schools. Multi-tenant: one backend
serves many schools. Handles admissions, staff, classes/subjects/sessions/terms,
attendance, grading and report cards, fees and payments, and a parent portal.

Despite the "LMS" in the repo name, there is **no learning content** (lessons,
coursework, study material) — this is administration, not courseware.

---

## Stack

| | |
|---|---|
| Backend | FastAPI (Python 3.11), Supabase Postgres via the `supabase` client (service-role key) |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4 (CSS-first `@theme`) |
| Auth | JWT in an httpOnly cookie; 8 roles (system_admin, admin, dean, registrar, bursar, teacher, parent, student) |
| Email | Resend (`app/core/email.py`) — password reset, welcome, and notification triggers |
| Deploy | Backend on Render (`render.yaml`); `master` auto-deploys. Frontend deployed separately. No staging. |

---

## Running locally

**Backend**

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, JWT_SECRET
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev                 # http://localhost:3000, proxies /api/v1/* to :8000
```

Or `./START_BOTH_SERVERS.ps1` from the repo root (Windows).

API docs at `http://127.0.0.1:8000/docs` when `DEBUG=true`.

---

## Database

Schema lives in `database/*.sql`, applied **by hand in the Supabase SQL Editor**
in filename order (`phase1_*` … `phase12_*`, then the standalone ones). There is
no migration tool and no applied-state tracking — to see what production actually
has, query it. `database/backup_export.py` dumps every table to timestamped JSON
(the only backup mechanism on the current Supabase plan — run it periodically).

---

## Tests

```bash
cd backend
python -m pytest            # ~156 tests, ~15 min
```

The suite hits the **real Supabase project** (no test database) — every fixture
creates a throwaway organization and deletes it afterward. Runs are flaky when
the network is; email is forced into a no-op during tests. There is no CI that
runs the full suite; a lightweight GitHub Actions workflow runs typecheck, build,
lint, and backend import/collection checks on push.

Frontend: `npx tsc --noEmit`, `npx next build`, `npx eslint .`.

---

## Layout

```
backend/app/
  api/v1/endpoints/   one file per domain (auth, students, teachers, classes,
                     subjects, sessions, terms, attendance, grading, fees,
                     teacher_management, parents, users, system_admin, skills)
  core/              config, database, security, email, rate_limit, permissions
  models/            Pydantic request/response models
  tests/             pytest, real-Supabase integration style
frontend/app/
  dashboard/         the school app (per-role pages)
  system-admin/      platform operator console
  login, forgot-password, reset-password, register-school
frontend/components/ DashboardLayout, Sidebar, ProtectedRoute, ui/*
database/            *.sql migrations + backup_export.py
```

---

## Known gaps

- **No payment gateway** — payments are recorded manually by the bursar.
- **No Row-Level Security** — tenant isolation is enforced only by
  `.eq("organization_id", …)` filters in application code (the service-role key
  bypasses RLS). Parked pending a Supabase plan upgrade.
- **Client-side route protection only** — `ProtectedRoute` redirects after
  render; the API is the real gate. `requiredRole` is wired only on
  `/system-admin`.
- **`email_verified`** exists but is informational — not enforced at login.
- ESLint has a large backlog (mostly `no-explicit-any` and React-hooks rules);
  `tsc` is clean and `next build` passes.
