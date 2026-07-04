-- =====================================================
-- Phase 4: Rollback Script (DESTRUCTIVE)
-- Only use this if you need to undo Phase 4 changes
-- =====================================================

\echo 'WARNING: This will DESTROY all Phase 4 data!'
\echo 'Rollback will delete:'
\echo '  - school_report_recipients'
\echo '  - school_reports'
\echo '  - student_remarks'
\echo '  - teacher_class_assignments'
\echo '  - grading_scheme_components'
\echo '  - grading_schemes'
\echo '  - class_subjects'
\echo ''

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS school_report_recipients CASCADE;
DROP TABLE IF EXISTS school_reports CASCADE;
DROP TABLE IF EXISTS student_remarks CASCADE;
DROP TABLE IF EXISTS teacher_class_assignments CASCADE;
DROP TABLE IF EXISTS grading_scheme_components CASCADE;
DROP TABLE IF EXISTS grading_schemes CASCADE;
DROP TABLE IF EXISTS class_subjects CASCADE;

\echo 'Phase 4 rollback complete!'
