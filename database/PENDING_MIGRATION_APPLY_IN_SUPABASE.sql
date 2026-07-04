-- =====================================================
-- PENDING MIGRATION: paste this whole file into the
-- Supabase Dashboard -> SQL Editor -> New query -> Run
-- =====================================================
-- Generated during the July 2026 audit. Direct Postgres access
-- (DATABASE_URL / asyncpg / run_migrations.py) does not work from
-- this environment: db.gygzsasweryajcleolie.supabase.co does not
-- resolve via DNS here. This is the combined, verified-idempotent
-- content of database/phase3_attendance_schema.sql and
-- database/phase4_teacher_class_schema.sql (psql \echo lines
-- removed since the Supabase SQL Editor is not psql).
--
-- Confirmed against the live DB on 2026-07-04: every table below is
-- currently MISSING. Confirmed against the live DB: 'users' table
-- has no 'organization_id' column (only 'school_id') and
-- 'students.user_id' already exists (from add_student_user_id.sql,
-- already applied - do not need to re-run that one).
--
-- Safe to run: every statement is CREATE TABLE/INDEX IF NOT EXISTS.
-- =====================================================


-- =====================================================
-- Phase 3B: Attendance Management Schema
-- =====================================================

CREATE TABLE IF NOT EXISTS attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,

    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,

    check_in_time TIME,
    check_out_time TIME,
    minutes_late INTEGER DEFAULT 0,

    reason TEXT,
    notes TEXT,

    marked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    marked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(student_id, attendance_date),
    CONSTRAINT check_attendance_status CHECK (status IN ('present', 'absent', 'late', 'excused'))
);

CREATE TABLE IF NOT EXISTS attendance_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,

    days_present INTEGER DEFAULT 0,
    days_absent INTEGER DEFAULT 0,
    days_late INTEGER DEFAULT 0,
    days_excused INTEGER DEFAULT 0,
    total_school_days INTEGER DEFAULT 0,

    attendance_percentage DECIMAL(5,2),
    punctuality_percentage DECIMAL(5,2),

    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(student_id, term_id, session_id)
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    leave_type VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,

    attachment_url TEXT,

    status VARCHAR(20) DEFAULT 'pending',
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,

    submitted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_leave_dates CHECK (end_date >= start_date),
    CONSTRAINT check_leave_status CHECK (status IN ('pending', 'approved', 'rejected')),
    CONSTRAINT check_leave_type CHECK (leave_type IN ('sick', 'family', 'emergency', 'other'))
);

CREATE TABLE IF NOT EXISTS attendance_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    school_start_time TIME NOT NULL DEFAULT '08:00:00',
    school_end_time TIME NOT NULL DEFAULT '14:00:00',
    late_threshold_minutes INTEGER DEFAULT 15,

    auto_mark_absent BOOLEAN DEFAULT false,
    auto_mark_time TIME,

    notify_parents_on_absence BOOLEAN DEFAULT true,
    notify_parents_on_late BOOLEAN DEFAULT false,
    absence_threshold_notify INTEGER DEFAULT 3,

    working_days JSONB DEFAULT '["monday","tuesday","wednesday","thursday","friday"]'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(organization_id)
);

CREATE TABLE IF NOT EXISTS holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    session_id UUID REFERENCES academic_sessions(id) ON DELETE CASCADE,

    holiday_name VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    holiday_type VARCHAR(50) DEFAULT 'public',
    description TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_holiday_dates CHECK (end_date >= start_date),
    CONSTRAINT check_holiday_type CHECK (holiday_type IN ('public', 'school', 'term_break'))
);

CREATE TABLE IF NOT EXISTS teacher_attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,

    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,

    check_in_time TIME,
    check_out_time TIME,
    hours_worked DECIMAL(4,2),

    reason TEXT,
    notes TEXT,

    marked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    marked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(teacher_id, attendance_date),
    CONSTRAINT check_teacher_status CHECK (status IN ('present', 'absent', 'late', 'on_leave'))
);

CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance_records(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_records(attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_class ON attendance_records(class_id);
CREATE INDEX IF NOT EXISTS idx_attendance_org_date ON attendance_records(organization_id, attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_term ON attendance_records(term_id, session_id);

CREATE INDEX IF NOT EXISTS idx_attendance_summary_student ON attendance_summaries(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_summary_term ON attendance_summaries(term_id, session_id);

CREATE INDEX IF NOT EXISTS idx_leave_requests_student ON leave_requests(student_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status);
CREATE INDEX IF NOT EXISTS idx_leave_requests_dates ON leave_requests(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_holidays_org ON holidays(organization_id);
CREATE INDEX IF NOT EXISTS idx_holidays_dates ON holidays(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_teacher_attendance_teacher ON teacher_attendance(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_attendance_date ON teacher_attendance(attendance_date);

COMMENT ON TABLE attendance_records IS 'Daily student attendance tracking';
COMMENT ON TABLE attendance_summaries IS 'Aggregated attendance statistics per term';
COMMENT ON TABLE leave_requests IS 'Student leave/absence requests from parents';
COMMENT ON TABLE attendance_settings IS 'School-wide attendance configuration';
COMMENT ON TABLE holidays IS 'School holidays and non-working days';
COMMENT ON TABLE teacher_attendance IS 'Teacher/staff attendance tracking';


-- =====================================================
-- Phase 4: Teacher Class Management Features
-- =====================================================

CREATE TABLE IF NOT EXISTS class_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    is_mandatory BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(class_id, subject_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_class_subjects_class ON class_subjects(class_id);
CREATE INDEX IF NOT EXISTS idx_class_subjects_subject ON class_subjects(subject_id);
CREATE INDEX IF NOT EXISTS idx_class_subjects_session ON class_subjects(session_id);

CREATE TABLE IF NOT EXISTS grading_schemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, session_id, name)
);

CREATE INDEX IF NOT EXISTS idx_grading_schemes_org ON grading_schemes(organization_id);
CREATE INDEX IF NOT EXISTS idx_grading_schemes_session ON grading_schemes(session_id);
CREATE INDEX IF NOT EXISTS idx_grading_schemes_active ON grading_schemes(is_active, is_default);

CREATE TABLE IF NOT EXISTS grading_scheme_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grading_scheme_id UUID NOT NULL REFERENCES grading_schemes(id) ON DELETE CASCADE,
    component_type VARCHAR(50) NOT NULL,
    component_name VARCHAR(100) NOT NULL,
    weight_percentage DECIMAL(5,2) NOT NULL CHECK (weight_percentage > 0 AND weight_percentage <= 100),
    max_score DECIMAL(10,2) DEFAULT 100,
    required BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(grading_scheme_id, component_name)
);

CREATE INDEX IF NOT EXISTS idx_grading_scheme_components_scheme ON grading_scheme_components(grading_scheme_id);

CREATE TABLE IF NOT EXISTS teacher_class_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id) ON DELETE CASCADE,
    is_form_teacher BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(teacher_id, subject_id, class_id, term_id)
);

CREATE INDEX IF NOT EXISTS idx_teacher_class_assignments_teacher ON teacher_class_assignments(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_class_assignments_class ON teacher_class_assignments(class_id);
CREATE INDEX IF NOT EXISTS idx_teacher_class_assignments_subject ON teacher_class_assignments(subject_id);
CREATE INDEX IF NOT EXISTS idx_teacher_class_assignments_session ON teacher_class_assignments(session_id);
CREATE INDEX IF NOT EXISTS idx_teacher_class_assignments_form_teacher ON teacher_class_assignments(is_form_teacher) WHERE is_form_teacher = true;

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_form_teacher_per_class
ON teacher_class_assignments(class_id, session_id)
WHERE is_form_teacher = true;

CREATE TABLE IF NOT EXISTS student_remarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    form_teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    remark_text TEXT NOT NULL,
    remarks_category VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_student_remarks_student ON student_remarks(student_id);
CREATE INDEX IF NOT EXISTS idx_student_remarks_class ON student_remarks(class_id);
CREATE INDEX IF NOT EXISTS idx_student_remarks_session_term ON student_remarks(session_id, term_id);
CREATE INDEX IF NOT EXISTS idx_student_remarks_teacher ON student_remarks(form_teacher_id);

CREATE TABLE IF NOT EXISTS school_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL,
    form_teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_school_reports_org ON school_reports(organization_id);
CREATE INDEX IF NOT EXISTS idx_school_reports_class ON school_reports(class_id);
CREATE INDEX IF NOT EXISTS idx_school_reports_session_term ON school_reports(session_id, term_id);
CREATE INDEX IF NOT EXISTS idx_school_reports_teacher ON school_reports(form_teacher_id);
CREATE INDEX IF NOT EXISTS idx_school_reports_type ON school_reports(report_type);

CREATE TABLE IF NOT EXISTS school_report_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES school_reports(id) ON DELETE CASCADE,
    parent_id UUID NOT NULL REFERENCES parents(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE SET NULL,
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    delivery_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_report_recipients_report ON school_report_recipients(report_id);
CREATE INDEX IF NOT EXISTS idx_report_recipients_parent ON school_report_recipients(parent_id);
CREATE INDEX IF NOT EXISTS idx_report_recipients_student ON school_report_recipients(student_id);
CREATE INDEX IF NOT EXISTS idx_report_recipients_status ON school_report_recipients(delivery_status);
