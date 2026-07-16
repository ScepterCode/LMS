-- Phase 9: scope admission_number/staff_number uniqueness to organization_id.
--
-- Both students.admission_number and teachers.staff_number were created
-- with a plain (platform-wide) UNIQUE constraint. Admission numbers and
-- staff numbers are only meant to be unique within a school - a
-- multi-tenant platform where two independent schools can't both use
-- "ADM001" or "STAFF001" is broken. Confirmed live: two different schools
-- both registering admission_number "ADM001" hit
-- "duplicate key value violates unique constraint students_admission_number_key".
--
-- students.admission_number: the app-level duplicate check in
-- create_student (backend/app/api/v1/endpoints/students.py) was already
-- scoped to organization_id, but the DB constraint underneath it was not,
-- so it could still reject a valid cross-school registration.
--
-- teachers.staff_number: the app-level check was scoped to
-- organization_id by an earlier fix (commit a6da1ca, "Fix update-endpoint
-- crash and cross-tenant bugs on Term/Session/Teacher edit"), but that fix
-- only touched the app-level check - the DB constraint itself was never
-- migrated, so it has the identical live bug as admission_number.
--
-- Must be applied manually via the Supabase SQL Editor - direct Postgres
-- access (DATABASE_URL / asyncpg / run_migrations.py) does not resolve
-- from this environment, same as noted in PENDING_MIGRATION_APPLY_IN_SUPABASE.sql.
--
-- Constraint names below (students_admission_number_key,
-- teachers_staff_number_key) are Postgres's default naming for an inline
-- column UNIQUE - students_admission_number_key was confirmed directly
-- from the live error message; teachers_staff_number_key follows the same
-- naming convention and was not separately hit live.

ALTER TABLE students DROP CONSTRAINT IF EXISTS students_admission_number_key;
ALTER TABLE students ADD CONSTRAINT students_org_admission_number_key
    UNIQUE (organization_id, admission_number);

ALTER TABLE teachers DROP CONSTRAINT IF EXISTS teachers_staff_number_key;
ALTER TABLE teachers ADD CONSTRAINT teachers_org_staff_number_key
    UNIQUE (organization_id, staff_number);
