-- Phase 10: restore every missing foreign key across the schema.
--
-- A live audit (pg_constraint) showed that on nearly every table added
-- since the initial organizations/users/campuses setup, only the
-- organization_id/created_by/approved_by-style FKs (pointing at
-- organizations or users) actually exist. Every FK that should point at
-- students, subjects, classes, academic_sessions, terms, or teachers is
-- missing - 52 constraints across 16 tables, exactly matching what
-- phase3_grading_schema.sql, phase3_attendance_schema.sql,
-- phase3_fees_schema.sql, phase4_teacher_class_schema.sql, and
-- phase5_report_card_enhancements.sql define but which were apparently
-- never fully applied (or were dropped) on the live database.
--
-- This was invisible for a long time because PostgREST's schema cache
-- had been serving embedded-resource joins (e.g.
-- "report_cards?select=*,academic_sessions(name)") successfully anyway,
-- using a cached relationship graph from some earlier point. Once that
-- cache was reloaded (a NOTIFY pgrst prompted by an unrelated migration),
-- PostgREST re-introspected the real schema and started rejecting those
-- joins with PGRST200 "no relationship found" - exposing this real,
-- pre-existing gap rather than causing it. This affects live production
-- reads right now for every school on the platform, not just tests.
--
-- Safe to run as-is: each ALTER is wrapped so it never aborts the whole
-- script - EXCEPTION duplicate_object means it's already there (fine),
-- and EXCEPTION foreign_key_violation means some existing row's value
-- doesn't match anything in the parent table (orphaned data) and could
-- not be constrained - that specific ALTER is skipped with a NOTICE
-- naming it, and everything else still runs. If any NOTICEs appear,
-- come back to me with the exact table/column named and we'll look at
-- the orphaned rows together (likely a handful of stale test/deleted
-- records) before deciding whether to delete them or fix the data.
--
-- Run this, then reload the schema cache once more so PostgREST picks
-- up all the new relationships immediately:
--   NOTIFY pgrst, 'reload schema';

-- ============================================
-- assessments
-- ============================================
DO $$ BEGIN
    ALTER TABLE assessments ADD CONSTRAINT assessments_subject_id_fkey
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED assessments.subject_id -> subjects (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE assessments ADD CONSTRAINT assessments_class_id_fkey
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED assessments.class_id -> classes (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE assessments ADD CONSTRAINT assessments_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED assessments.session_id -> academic_sessions (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE assessments ADD CONSTRAINT assessments_term_id_fkey
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED assessments.term_id -> terms (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE assessments ADD CONSTRAINT assessments_teacher_id_fkey
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED assessments.teacher_id -> teachers (orphaned rows)';
END $$;

-- ============================================
-- grades
-- ============================================
DO $$ BEGIN
    ALTER TABLE grades ADD CONSTRAINT grades_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED grades.student_id -> students (orphaned rows)';
END $$;

-- ============================================
-- subject_grades
-- ============================================
DO $$ BEGIN
    ALTER TABLE subject_grades ADD CONSTRAINT subject_grades_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED subject_grades.student_id -> students (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE subject_grades ADD CONSTRAINT subject_grades_subject_id_fkey
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED subject_grades.subject_id -> subjects (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE subject_grades ADD CONSTRAINT subject_grades_class_id_fkey
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED subject_grades.class_id -> classes (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE subject_grades ADD CONSTRAINT subject_grades_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED subject_grades.session_id -> academic_sessions (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE subject_grades ADD CONSTRAINT subject_grades_term_id_fkey
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED subject_grades.term_id -> terms (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE subject_grades ADD CONSTRAINT subject_grades_teacher_id_fkey
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED subject_grades.teacher_id -> teachers (orphaned rows)';
END $$;

-- ============================================
-- report_cards
-- ============================================
DO $$ BEGIN
    ALTER TABLE report_cards ADD CONSTRAINT report_cards_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED report_cards.student_id -> students (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE report_cards ADD CONSTRAINT report_cards_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED report_cards.session_id -> academic_sessions (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE report_cards ADD CONSTRAINT report_cards_term_id_fkey
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED report_cards.term_id -> terms (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE report_cards ADD CONSTRAINT report_cards_class_id_fkey
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED report_cards.class_id -> classes (orphaned rows)';
END $$;

-- ============================================
-- student_fees
-- ============================================
DO $$ BEGIN
    ALTER TABLE student_fees ADD CONSTRAINT student_fees_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_fees.student_id -> students (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE student_fees ADD CONSTRAINT student_fees_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_fees.session_id -> academic_sessions (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE student_fees ADD CONSTRAINT student_fees_term_id_fkey
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_fees.term_id -> terms (orphaned rows)';
END $$;

-- ============================================
-- payments
-- ============================================
DO $$ BEGIN
    ALTER TABLE payments ADD CONSTRAINT payments_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED payments.student_id -> students (orphaned rows)';
END $$;

-- ============================================
-- attendance_records
-- ============================================
DO $$ BEGIN
    ALTER TABLE attendance_records ADD CONSTRAINT attendance_records_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED attendance_records.student_id -> students (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE attendance_records ADD CONSTRAINT attendance_records_class_id_fkey
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED attendance_records.class_id -> classes (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE attendance_records ADD CONSTRAINT attendance_records_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED attendance_records.session_id -> academic_sessions (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE attendance_records ADD CONSTRAINT attendance_records_term_id_fkey
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED attendance_records.term_id -> terms (orphaned rows)';
END $$;

-- ============================================
-- attendance_summaries
-- ============================================
DO $$ BEGIN
    ALTER TABLE attendance_summaries ADD CONSTRAINT attendance_summaries_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED attendance_summaries.student_id -> students (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE attendance_summaries ADD CONSTRAINT attendance_summaries_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED attendance_summaries.session_id -> academic_sessions (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE attendance_summaries ADD CONSTRAINT attendance_summaries_term_id_fkey
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED attendance_summaries.term_id -> terms (orphaned rows)';
END $$;

-- ============================================
-- leave_requests
-- ============================================
DO $$ BEGIN
    ALTER TABLE leave_requests ADD CONSTRAINT leave_requests_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED leave_requests.student_id -> students (orphaned rows)';
END $$;

-- ============================================
-- teacher_attendance
-- ============================================
DO $$ BEGIN
    ALTER TABLE teacher_attendance ADD CONSTRAINT teacher_attendance_teacher_id_fkey
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED teacher_attendance.teacher_id -> teachers (orphaned rows)';
END $$;

-- ============================================
-- class_subjects
-- ============================================
DO $$ BEGIN
    ALTER TABLE class_subjects ADD CONSTRAINT class_subjects_class_id_fkey
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED class_subjects.class_id -> classes (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE class_subjects ADD CONSTRAINT class_subjects_subject_id_fkey
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED class_subjects.subject_id -> subjects (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE class_subjects ADD CONSTRAINT class_subjects_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED class_subjects.session_id -> academic_sessions (orphaned rows)';
END $$;

-- ============================================
-- teacher_class_assignments
-- ============================================
DO $$ BEGIN
    ALTER TABLE teacher_class_assignments ADD CONSTRAINT teacher_class_assignments_teacher_id_fkey
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED teacher_class_assignments.teacher_id -> teachers (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE teacher_class_assignments ADD CONSTRAINT teacher_class_assignments_class_id_fkey
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED teacher_class_assignments.class_id -> classes (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE teacher_class_assignments ADD CONSTRAINT teacher_class_assignments_subject_id_fkey
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED teacher_class_assignments.subject_id -> subjects (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE teacher_class_assignments ADD CONSTRAINT teacher_class_assignments_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED teacher_class_assignments.session_id -> academic_sessions (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE teacher_class_assignments ADD CONSTRAINT teacher_class_assignments_term_id_fkey
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED teacher_class_assignments.term_id -> terms (orphaned rows)';
END $$;

-- ============================================
-- student_remarks
-- ============================================
DO $$ BEGIN
    ALTER TABLE student_remarks ADD CONSTRAINT student_remarks_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_remarks.student_id -> students (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE student_remarks ADD CONSTRAINT student_remarks_class_id_fkey
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_remarks.class_id -> classes (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE student_remarks ADD CONSTRAINT student_remarks_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_remarks.session_id -> academic_sessions (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE student_remarks ADD CONSTRAINT student_remarks_term_id_fkey
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_remarks.term_id -> terms (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE student_remarks ADD CONSTRAINT student_remarks_form_teacher_id_fkey
        FOREIGN KEY (form_teacher_id) REFERENCES teachers(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_remarks.form_teacher_id -> teachers (orphaned rows)';
END $$;

-- ============================================
-- school_reports
-- ============================================
DO $$ BEGIN
    ALTER TABLE school_reports ADD CONSTRAINT school_reports_class_id_fkey
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED school_reports.class_id -> classes (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE school_reports ADD CONSTRAINT school_reports_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED school_reports.session_id -> academic_sessions (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE school_reports ADD CONSTRAINT school_reports_term_id_fkey
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED school_reports.term_id -> terms (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE school_reports ADD CONSTRAINT school_reports_form_teacher_id_fkey
        FOREIGN KEY (form_teacher_id) REFERENCES teachers(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED school_reports.form_teacher_id -> teachers (orphaned rows)';
END $$;

-- ============================================
-- school_report_recipients
-- ============================================
DO $$ BEGIN
    ALTER TABLE school_report_recipients ADD CONSTRAINT school_report_recipients_parent_id_fkey
        FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED school_report_recipients.parent_id -> parents (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE school_report_recipients ADD CONSTRAINT school_report_recipients_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED school_report_recipients.student_id -> students (orphaned rows)';
END $$;

-- ============================================
-- student_skill_ratings
-- ============================================
DO $$ BEGIN
    ALTER TABLE student_skill_ratings ADD CONSTRAINT student_skill_ratings_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_skill_ratings.student_id -> students (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE student_skill_ratings ADD CONSTRAINT student_skill_ratings_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_skill_ratings.session_id -> academic_sessions (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE student_skill_ratings ADD CONSTRAINT student_skill_ratings_term_id_fkey
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_skill_ratings.term_id -> terms (orphaned rows)';
END $$;

DO $$ BEGIN
    ALTER TABLE student_skill_ratings ADD CONSTRAINT student_skill_ratings_rated_by_fkey
        FOREIGN KEY (rated_by) REFERENCES teachers(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN NULL;
    WHEN foreign_key_violation THEN RAISE NOTICE 'SKIPPED student_skill_ratings.rated_by -> teachers (orphaned rows)';
END $$;

NOTIFY pgrst, 'reload schema';
