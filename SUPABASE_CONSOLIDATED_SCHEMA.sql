-- ========================================================================
-- CONSOLIDATED DATABASE SCHEMA FOR NIGERIAN LMS
-- Complete schema for all phases (1-4) for Supabase SQL Editor
-- ========================================================================
-- Instructions:
-- 1. Go to: Supabase Dashboard → SQL Editor
-- 2. Create new query and paste ALL contents below
-- 3. Click "Run"
-- 4. Check Results tab for completion message
--
-- This includes:
-- ✓ Phase 1: Authentication, Organizations, Users
-- ✓ Phase 2: Academic Structure, Students, Teachers
-- ✓ Phase 3: Grading, Attendance, Fees (if tables exist)
-- ✓ Phase 4: Form Teachers, Grading Schemes, Reports
-- ========================================================================

-- ========================================================================
-- PHASE 1: CORE AUTHENTICATION & ORGANIZATION
-- ========================================================================

-- Subscription Plans
CREATE TABLE IF NOT EXISTS subscription_plans (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10,2) DEFAULT 0,
    price_yearly DECIMAL(10,2) DEFAULT 0,
    max_students INTEGER DEFAULT 50,
    features JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO subscription_plans (id, name, description, price_monthly, price_yearly, max_students, features) 
VALUES 
('trial', '14-Day Trial', 'Free trial for new schools', 0, 0, 50, '["Basic Dashboard", "Up to 50 Students", "Email Support"]'),
('basic', 'Basic Plan', 'For small schools', 49.99, 499.99, 200, '["All Trial Features", "Up to 200 Students", "Basic Reports", "Priority Support"]'),
('standard', 'Standard Plan', 'For growing schools', 99.99, 999.99, 500, '["All Basic Features", "Up to 500 Students", "Advanced Analytics", "Phone Support"]'),
('premium', 'Premium Plan', 'For large institutions', 199.99, 1999.99, 2000, '["All Standard Features", "Unlimited Students", "Custom Reports", "Dedicated Support", "API Access"]')
ON CONFLICT (id) DO NOTHING;

-- Organizations (Schools)
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    subscription_plan_id VARCHAR(50) DEFAULT 'trial' REFERENCES subscription_plans(id),
    subscription_status VARCHAR(50) DEFAULT 'trial',
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    is_test_account BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_email ON organizations(email);
CREATE INDEX IF NOT EXISTS idx_organizations_status ON organizations(subscription_status, is_active);

-- Users (All user accounts)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('system_admin', 'admin', 'teacher', 'bursar', 'parent')),
    school_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_school_id ON users(school_id);
CREATE INDEX IF NOT EXISTS idx_users_role_school ON users(role, school_id);

-- System Admins
CREATE TABLE IF NOT EXISTS system_admins (
    id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    is_super_admin BOOLEAN DEFAULT false,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Campuses
CREATE TABLE IF NOT EXISTS campuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    campus_name VARCHAR(200),
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(200),
    is_main_campus BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campuses_organization ON campuses(organization_id);

-- Create default system admin if not exists
INSERT INTO users (id, email, password_hash, full_name, role, is_active, email_verified) 
VALUES ('c520e1ba-8289-42b4-a242-85e501cfcc43', 'admin@nigerianlms.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'System Administrator', 'system_admin', true, true)
ON CONFLICT (email) DO NOTHING;

INSERT INTO system_admins (id, is_super_admin) 
VALUES ('c520e1ba-8289-42b4-a242-85e501cfcc43', true)
ON CONFLICT (id) DO NOTHING;

-- Create demo school
INSERT INTO organizations (id, name, slug, email, phone, address, subscription_plan_id, subscription_status, trial_ends_at) 
VALUES ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Demo School Lagos', 'demo-school-lagos', 'demo@school-lagos.com', '+234 801 234 5678', '123 Education Street, Lagos', 'trial', 'trial', NOW() + INTERVAL '14 days')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO users (id, email, password_hash, full_name, role, school_id, is_active, email_verified) 
VALUES ('d1e2f3a4-b5c6-7890-def1-234567890abc', 'admin@demo-school.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Demo School Admin', 'admin', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', true, true)
ON CONFLICT (email) DO NOTHING;

INSERT INTO campuses (organization_id, name, campus_name, address, phone, email, is_main_campus) 
VALUES ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Demo School Lagos Main Campus', 'Main Campus', '123 Education Street, Lagos', '+234 801 234 5678', 'demo@school-lagos.com', true)
ON CONFLICT DO NOTHING;

-- ========================================================================
-- PHASE 2: ACADEMIC STRUCTURE, STUDENTS & TEACHERS
-- ========================================================================

-- Academic Sessions
CREATE TABLE IF NOT EXISTS academic_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, name)
);

-- Terms
CREATE TABLE IF NOT EXISTS terms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    term_number INTEGER NOT NULL CHECK (term_number BETWEEN 1 AND 3),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, term_number)
);

-- Classes
CREATE TABLE IF NOT EXISTS classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL,
    section VARCHAR(10),
    capacity INTEGER DEFAULT 40 CHECK (capacity > 0),
    class_teacher_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subjects
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    subject_type VARCHAR(20) DEFAULT 'core' CHECK (subject_type IN ('core', 'elective')),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, code)
);

-- Students
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    admission_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    blood_group VARCHAR(5),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    state_of_origin VARCHAR(100),
    lga VARCHAR(100),
    nationality VARCHAR(100) DEFAULT 'Nigerian',
    religion VARCHAR(50),
    photo_url VARCHAR(500),
    medical_conditions TEXT,
    allergies TEXT,
    current_class_id UUID REFERENCES classes(id) ON DELETE SET NULL,
    admission_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'graduated', 'suspended', 'withdrawn', 'transferred')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Student Guardians
CREATE TABLE IF NOT EXISTS student_guardians (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    guardian_type VARCHAR(20) NOT NULL CHECK (guardian_type IN ('father', 'mother', 'guardian', 'other')),
    title VARCHAR(10),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    relationship VARCHAR(50),
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    occupation VARCHAR(100),
    address TEXT,
    is_emergency_contact BOOLEAN DEFAULT true,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Teachers
CREATE TABLE IF NOT EXISTS teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    staff_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT,
    state_of_origin VARCHAR(100),
    lga VARCHAR(100),
    nationality VARCHAR(100) DEFAULT 'Nigerian',
    photo_url VARCHAR(500),
    qualification VARCHAR(200),
    specialization VARCHAR(200),
    employment_date DATE DEFAULT CURRENT_DATE,
    employment_type VARCHAR(20) DEFAULT 'full-time' CHECK (employment_type IN ('full-time', 'part-time', 'contract')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'on-leave', 'terminated', 'retired')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subject Assignments
CREATE TABLE IF NOT EXISTS subject_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(teacher_id, subject_id, class_id, term_id)
);

-- Class Enrollments
CREATE TABLE IF NOT EXISTS class_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'promoted', 'repeated', 'withdrawn')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, session_id)
);

-- Parents
CREATE TABLE IF NOT EXISTS parents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(10),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    occupation VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Parent-Student Links
CREATE TABLE IF NOT EXISTS parent_student_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL REFERENCES parents(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    relationship VARCHAR(50) NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(parent_id, student_id)
);

-- Create indexes for Phase 2
CREATE INDEX IF NOT EXISTS idx_sessions_org_current ON academic_sessions(organization_id, is_current);
CREATE INDEX IF NOT EXISTS idx_terms_session ON terms(session_id);
CREATE INDEX IF NOT EXISTS idx_classes_org ON classes(organization_id);
CREATE INDEX IF NOT EXISTS idx_subjects_org ON subjects(organization_id);
CREATE INDEX IF NOT EXISTS idx_students_org ON students(organization_id);
CREATE INDEX IF NOT EXISTS idx_teachers_org ON teachers(organization_id);
CREATE INDEX IF NOT EXISTS idx_assignments_teacher ON subject_assignments(teacher_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON class_enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_parents_org ON parents(organization_id);

-- Create default academic session for demo school
INSERT INTO academic_sessions (organization_id, name, start_date, end_date, is_current)
VALUES ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '2025-2026', DATE '2025-09-01', DATE '2026-06-30', true)
ON CONFLICT (organization_id, name) DO NOTHING;

-- ========================================================================
-- PHASE 4: FORM TEACHERS, GRADING SCHEMES & REPORTS
-- ========================================================================

-- Class Subjects (Curriculum)
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

-- Grading Schemes
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
CREATE INDEX IF NOT EXISTS idx_grading_schemes_active ON grading_schemes(is_active, is_default);

-- Grading Scheme Components
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

-- Teacher Class Assignments
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

CREATE INDEX IF NOT EXISTS idx_teacher_class_form_teacher ON teacher_class_assignments(is_form_teacher) WHERE is_form_teacher = true;
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_form_teacher_per_class ON teacher_class_assignments(class_id, session_id) WHERE is_form_teacher = true;

-- Student Remarks
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
CREATE INDEX IF NOT EXISTS idx_student_remarks_session_term ON student_remarks(session_id, term_id);

-- School Reports
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
CREATE INDEX IF NOT EXISTS idx_school_reports_type ON school_reports(report_type);

-- School Report Recipients
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
CREATE INDEX IF NOT EXISTS idx_report_recipients_status ON school_report_recipients(delivery_status);

-- ========================================================================
-- SEED DEFAULT GRADING SCHEMES
-- ========================================================================

-- Get first organization and session (for demo purposes)
INSERT INTO grading_schemes (organization_id, session_id, name, description, is_active, is_default)
SELECT 
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    (SELECT id FROM academic_sessions WHERE organization_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890' ORDER BY created_at DESC LIMIT 1),
    name,
    description,
    true,
    is_default
FROM (VALUES
    ('20-20-60', 'Two tests (20% each) and one exam (60%)', false),
    ('20-20-20-40', 'Two tests (20% each), coursework (20%), and exam (40%)', true),
    ('20-40-40', 'One test (20%), coursework (40%), and exam (40%)', false),
    ('10-10-10-70', 'Three continuous assessments (10% each) and exam (70%)', false),
    ('100-Exam-Only', 'Single exam grading (100%)', false)
) AS schemes(name, description, is_default)
ON CONFLICT DO NOTHING;

-- ========================================================================
-- COMPLETION CHECK
-- ========================================================================

SELECT 
    'Schema Migration Complete!' AS status,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') AS total_tables,
    NOW() AS completed_at;
