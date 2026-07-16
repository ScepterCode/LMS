-- Phase 7: add the "dean" role.
--
-- Dean has the same academic/staff/student management access as admin
-- (classes, teachers, students, subjects, sessions/terms, teacher
-- assignments, grading schemes, class-subjects, report-card skills,
-- parents) but NOT fees/payments/financial reports, school branding or
-- subscription settings, or the system-admin platform. Deans may create
-- and deactivate teacher and parent login accounts, but not admin,
-- bursar, dean, or system_admin accounts.
--
-- users.role has a CHECK constraint (from phase1_minimal_schema.sql) that
-- must be widened before any user row can have role='dean'. This must be
-- applied manually via the Supabase SQL Editor, same as every other
-- schema (DDL) change this project has needed - the application code in
-- this same change is already written to allow 'dean' the moment this
-- runs, so apply it before creating any dean account.
--
-- If the constraint name below doesn't match what's actually in your
-- database (it may differ if the table was created differently from
-- phase1_minimal_schema.sql), first run:
--   SELECT conname FROM pg_constraint
--   WHERE conrelid = 'users'::regclass AND contype = 'c';
-- and substitute the real name for users_role_check below.

ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check
    CHECK (role IN ('system_admin', 'admin', 'dean', 'teacher', 'bursar', 'parent'));
