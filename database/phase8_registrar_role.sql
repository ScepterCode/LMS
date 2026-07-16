-- Phase 8: add the "registrar" (front desk) role.
--
-- Registrar covers admissions intake and enrollment records only:
-- students, class enrollments, and parent/guardian contact records
-- (they may create parent login accounts as part of registering a new
-- student's guardian, same as a dean can for teacher/parent accounts -
-- see users.py). Registrar does NOT get classes/subjects/sessions/terms
-- (academic setup), teacher management, grading/assessments, fees, or
-- school-wide settings.
--
-- Must be applied manually via the Supabase SQL Editor, same as
-- phase7_dean_role.sql - the constraint name was confirmed as
-- users_role_check while testing that migration.

ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check
    CHECK (role IN ('system_admin', 'admin', 'dean', 'registrar', 'teacher', 'bursar', 'parent'));
