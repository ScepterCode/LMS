-- =====================================================
-- Phase 4: Teacher Class Management Features
-- Nigerian School Management System
--
-- This schema adds form teacher management, configurable grading schemes,
-- class-subject relationships, and report capabilities.
--
-- Tables:
-- 1. class_subjects - Define curriculum per class per session
-- 2. grading_schemes - Configurable grading formats (20-20-60, etc.)
-- 3. grading_scheme_components - Components of each grading scheme
-- 4. teacher_class_assignments - Teacher to class/subject with form teacher flag
-- 5. student_remarks - Form teacher remarks on report cards
-- 6. school_reports - Report records
-- 7. school_report_recipients - Report delivery tracking
--
-- Total: 7 new tables
-- =====================================================

\echo 'Creating Phase 4: Teacher Class Management tables...'

-- =====================================================
-- PART 1: CLASS-SUBJECT RELATIONSHIPS
-- =====================================================

\echo 'Creating class_subjects table...'

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

-- =====================================================
-- PART 2: GRADING SCHEMES
-- =====================================================

\echo 'Creating grading_schemes table...'

CREATE TABLE IF NOT EXISTS grading_schemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,  -- "20-20-60", "20-20-20-40"
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

-- =====================================================
-- PART 3: GRADING SCHEME COMPONENTS
-- =====================================================

\echo 'Creating grading_scheme_components table...'

CREATE TABLE IF NOT EXISTS grading_scheme_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grading_scheme_id UUID NOT NULL REFERENCES grading_schemes(id) ON DELETE CASCADE,
    component_type VARCHAR(50) NOT NULL,  -- 'test', 'coursework', 'exam', 'assignment'
    component_name VARCHAR(100) NOT NULL,  -- e.g., "Test 1", "Coursework", "Final Exam"
    weight_percentage DECIMAL(5,2) NOT NULL CHECK (weight_percentage > 0 AND weight_percentage <= 100),
    max_score DECIMAL(10,2) DEFAULT 100,
    required BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(grading_scheme_id, component_name)
);

CREATE INDEX IF NOT EXISTS idx_grading_scheme_components_scheme ON grading_scheme_components(grading_scheme_id);

-- =====================================================
-- PART 4: TEACHER CLASS ASSIGNMENTS
-- =====================================================

\echo 'Creating teacher_class_assignments table...'

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

-- Constraint: Only one form teacher per class per session
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_form_teacher_per_class 
ON teacher_class_assignments(class_id, session_id) 
WHERE is_form_teacher = true;

-- =====================================================
-- PART 5: STUDENT REMARKS
-- =====================================================

\echo 'Creating student_remarks table...'

CREATE TABLE IF NOT EXISTS student_remarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    form_teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    remark_text TEXT NOT NULL,
    remarks_category VARCHAR(50) DEFAULT 'general',  -- 'conduct', 'academic', 'general', 'behavioral', 'performance'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_student_remarks_student ON student_remarks(student_id);
CREATE INDEX IF NOT EXISTS idx_student_remarks_class ON student_remarks(class_id);
CREATE INDEX IF NOT EXISTS idx_student_remarks_session_term ON student_remarks(session_id, term_id);
CREATE INDEX IF NOT EXISTS idx_student_remarks_teacher ON student_remarks(form_teacher_id);

-- =====================================================
-- PART 6: SCHOOL REPORTS
-- =====================================================

\echo 'Creating school_reports table...'

CREATE TABLE IF NOT EXISTS school_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL,  -- 'term_result', 'conduct', 'performance', 'special', 'attendance', 'behavioral'
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

-- =====================================================
-- PART 7: SCHOOL REPORT RECIPIENTS
-- =====================================================

\echo 'Creating school_report_recipients table...'

CREATE TABLE IF NOT EXISTS school_report_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES school_reports(id) ON DELETE CASCADE,
    parent_id UUID NOT NULL REFERENCES parents(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE SET NULL,
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    delivery_status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'sent', 'delivered', 'read'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_report_recipients_report ON school_report_recipients(report_id);
CREATE INDEX IF NOT EXISTS idx_report_recipients_parent ON school_report_recipients(parent_id);
CREATE INDEX IF NOT EXISTS idx_report_recipients_student ON school_report_recipients(student_id);
CREATE INDEX IF NOT EXISTS idx_report_recipients_status ON school_report_recipients(delivery_status);

-- =====================================================
-- PART 8: MIGRATE EXISTING DATA (if applicable)
-- =====================================================

\echo 'Phase 4 tables created successfully!'
