-- Phase 11: allow teachers.gender to be recorded as unknown.
--
-- Needed to reconstruct 48 teacher profile rows whose original teachers
-- table rows were lost in the data-loss incident (see project history) -
-- the surviving users table has name/email/phone but never stored
-- gender, so it can't be reconstructed and must be left NULL until each
-- school's admin fills it in. A CHECK constraint already allows this
-- ('Male'/'Female'/'Other' via IN (...) evaluates to NULL, not FALSE, for
-- a NULL value, so it doesn't need to change) - only the NOT NULL needs
-- to be dropped.
--
-- Safe to run as-is: does not touch any existing row.

ALTER TABLE teachers ALTER COLUMN gender DROP NOT NULL;
