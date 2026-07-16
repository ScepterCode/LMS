-- ============================================
-- NIGERIAN LMS - PHASE 2 DATABASE SCHEMA
-- Core School Management Tables
-- ============================================

-- Drop tables if they exist (for development only)
DROP TABLE IF EXISTS parent_student_links CASCADE;
DROP TABLE IF EXISTS parents CASCADE;
DROP TABLE IF EXISTS class_enrollments CASCADE;
DROP TABLE IF EXISTS subject_assignments CASCADE;
DROP TABLE IF EXISTS teachers CASCADE;
DROP TABLE IF EXISTS student_guardians CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS subjects CASCADE;
DROP TABLE IF EXISTS classes CASCADE;
DROP TABLE IF EXISTS terms CASCADE;
DROP TABLE IF EXISTS academic_sessions CASCADE;

-- ============================================
-- ACADEMIC STRUCTURE
-- ============================================

-- Academic Sessions (School Years)
CREATE TABLE academic_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,  -- "2024/2025"
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, name)
);

-- Terms/Semesters
CREATE TABLE terms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,  -- "1st Term", "2nd Term", "3rd Term"
    term_number INTEGER NOT NULL CHECK (term_number BETWEEN 1 AND 3),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, term_number)
);

-- Classes (Grade levels with sections)
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,  -- "JSS 1", "SS 2"
    level VARCHAR(50) NOT NULL,  -- "Junior", "Senior", "Primary"
    section VARCHAR(10),  -- "A", "B", "C" (optional)
    capacity INTEGER DEFAULT 40 CHECK (capacity > 0),
    class_teacher_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subjects
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),  -- "MATH101", "ENG102"
    subject_type VARCHAR(20) DEFAULT 'core' CHECK (subject_type IN ('core', 'elective')),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, code)
);

-- ============================================
-- STUDENTS
-- ============================================

-- Student Records
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    admission_number VARCHAR(50) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    blood_group VARCHAR(5),  -- "A+", "O-", etc.
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    state_of_origin VARCHAR(100),
    lga VARCHAR(100),  -- Local Government Area
    nationality VARCHAR(100) DEFAULT 'Nigerian',
    religion VARCHAR(50),
    photo_url VARCHAR(500),
    medical_conditions TEXT,
    allergies TEXT,
    current_class_id UUID REFERENCES classes(id) ON DELETE SET NULL,
    admission_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'graduated', 'suspended', 'withdrawn', 'transferred')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    -- Admission numbers are only meant to be unique within a school, not
    -- platform-wide - two schools independently using "ADM001" is a normal
    -- collision, not a data error.
    UNIQUE(organization_id, admission_number)
);

-- Student Guardians/Parents (denormalized for quick access)
CREATE TABLE student_guardians (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    guardian_type VARCHAR(20) NOT NULL CHECK (guardian_type IN ('father', 'mother', 'guardian', 'other')),
    title VARCHAR(10),  -- "Mr", "Mrs", "Dr", "Chief"
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    relationship VARCHAR(50),  -- "Father", "Mother", "Uncle", "Aunt"
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    occupation VARCHAR(100),
    address TEXT,
    is_emergency_contact BOOLEAN DEFAULT true,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TEACHERS
-- ============================================

-- Teacher Records (linked to users table)
CREATE TABLE teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    staff_number VARCHAR(50) NOT NULL,
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
    qualification VARCHAR(200),  -- "B.Ed Mathematics", "M.Ed Physics"
    specialization VARCHAR(200),  -- "Mathematics", "Physics and Chemistry"
    employment_date DATE DEFAULT CURRENT_DATE,
    employment_type VARCHAR(20) DEFAULT 'full-time' CHECK (employment_type IN ('full-time', 'part-time', 'contract')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'on-leave', 'terminated', 'retired')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    -- Staff numbers are only meant to be unique within a school, not
    -- platform-wide - see the matching note on students.admission_number.
    UNIQUE(organization_id, staff_number)
);

-- ============================================
-- ASSIGNMENTS
-- ============================================

-- Teacher Subject Assignments (who teaches what to which class)
CREATE TABLE subject_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(teacher_id, subject_id, class_id, term_id)
);

-- Student Class Enrollments (which class is student in)
CREATE TABLE class_enrollments (
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

-- ============================================
-- PARENTS
-- ============================================

-- Parent Accounts (linked to users table)
CREATE TABLE parents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(10),  -- "Mr", "Mrs", "Dr"
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    occupation VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Link Parents to Students
CREATE TABLE parent_student_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL REFERENCES parents(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    relationship VARCHAR(50) NOT NULL,  -- "Father", "Mother", "Guardian"
    is_primary BOOLEAN DEFAULT false,  -- Primary guardian for communications
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(parent_id, student_id)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Academic Sessions
CREATE INDEX idx_sessions_org_current ON academic_sessions(organization_id, is_current);

-- Terms
CREATE INDEX idx_terms_session ON terms(session_id);
CREATE INDEX idx_terms_current ON terms(is_current);

-- Classes
CREATE INDEX idx_classes_org ON classes(organization_id);
CREATE INDEX idx_classes_teacher ON classes(class_teacher_id);

-- Subjects
CREATE INDEX idx_subjects_org ON subjects(organization_id);

-- Students
CREATE INDEX idx_students_org ON students(organization_id);
CREATE INDEX idx_students_class ON students(current_class_id);
CREATE INDEX idx_students_status ON students(status);
CREATE INDEX idx_students_admission ON students(admission_number);

-- Student Guardians
CREATE INDEX idx_guardians_student ON student_guardians(student_id);
CREATE INDEX idx_guardians_primary ON student_guardians(is_primary);

-- Teachers
CREATE INDEX idx_teachers_org ON teachers(organization_id);
CREATE INDEX idx_teachers_user ON teachers(user_id);
CREATE INDEX idx_teachers_status ON teachers(status);
CREATE INDEX idx_teachers_staff ON teachers(staff_number);

-- Subject Assignments
CREATE INDEX idx_assignments_teacher ON subject_assignments(teacher_id);
CREATE INDEX idx_assignments_subject ON subject_assignments(subject_id);
CREATE INDEX idx_assignments_class ON subject_assignments(class_id);
CREATE INDEX idx_assignments_session ON subject_assignments(session_id);

-- Class Enrollments
CREATE INDEX idx_enrollments_student ON class_enrollments(student_id);
CREATE INDEX idx_enrollments_class ON class_enrollments(class_id);
CREATE INDEX idx_enrollments_session ON class_enrollments(session_id);

-- Parents
CREATE INDEX idx_parents_org ON parents(organization_id);
CREATE INDEX idx_parents_user ON parents(user_id);

-- Parent-Student Links
CREATE INDEX idx_parent_links_parent ON parent_student_links(parent_id);
CREATE INDEX idx_parent_links_student ON parent_student_links(student_id);

-- ============================================
-- ROW LEVEL SECURITY (RLS) - ENABLE LATER
-- ============================================

-- Enable RLS on all tables
-- ALTER TABLE academic_sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE terms ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE classes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE students ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE student_guardians ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE subject_assignments ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE class_enrollments ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE parents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE parent_student_links ENABLE ROW LEVEL SECURITY;

-- ============================================
-- SAMPLE DATA (Optional for testing)
-- ============================================

COMMENT ON TABLE academic_sessions IS 'School academic years (e.g., 2024/2025)';
COMMENT ON TABLE terms IS 'Academic terms/semesters within a session';
COMMENT ON TABLE classes IS 'Class/grade levels with optional sections';
COMMENT ON TABLE subjects IS 'Subject catalog for the school';
COMMENT ON TABLE students IS 'Student records with personal and academic info';
COMMENT ON TABLE student_guardians IS 'Guardian/parent information for students';
COMMENT ON TABLE teachers IS 'Teacher records linked to user accounts';
COMMENT ON TABLE subject_assignments IS 'Maps teachers to subjects and classes';
COMMENT ON TABLE class_enrollments IS 'Tracks which students are in which classes';
COMMENT ON TABLE parents IS 'Parent user accounts';
COMMENT ON TABLE parent_student_links IS 'Links parent accounts to student records';

-- ============================================
-- SCHEMA VERSION TRACKING
-- ============================================

-- Track schema versions
CREATE TABLE IF NOT EXISTS schema_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO schema_versions (version, description) 
VALUES ('2.0.0', 'Phase 2 - Core School Management Tables');

-- ============================================
-- COMPLETION MESSAGE
-- ============================================

-- Schema created successfully!
SELECT 'Phase 2 database schema created successfully!' AS status;
