-- =====================================================
-- Phase 3A: Grading & Assessment System Schema
-- Learnlyf
-- =====================================================

-- Assessment Types (CA1, CA2, Midterm, Exam, etc.)
CREATE TABLE IF NOT EXISTS assessment_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- "First CA", "Second CA", "Midterm", "Exam"
    code VARCHAR(50) NOT NULL, -- "CA1", "CA2", "MID", "EXAM"
    description TEXT,
    max_score DECIMAL(5,2) NOT NULL DEFAULT 100.00,
    weight_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00, -- Contribution to total
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, code)
);

-- Assessments (Specific instances of assessment types)
CREATE TABLE IF NOT EXISTS assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    assessment_type_id UUID NOT NULL REFERENCES assessment_types(id) ON DELETE RESTRICT,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES teachers(id) ON DELETE SET NULL,
    
    title VARCHAR(200) NOT NULL,
    description TEXT,
    assessment_date DATE,
    max_score DECIMAL(5,2) NOT NULL DEFAULT 100.00,
    
    -- Status workflow
    status VARCHAR(20) DEFAULT 'draft', -- draft, published, graded, approved, locked
    published_at TIMESTAMP WITH TIME ZONE,
    graded_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    CONSTRAINT check_status CHECK (status IN ('draft', 'published', 'graded', 'approved', 'locked'))
);

-- Grade Configuration (A=90-100, B=80-89, etc.)
CREATE TABLE IF NOT EXISTS grade_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    grade_letter VARCHAR(5) NOT NULL, -- "A", "B", "C", "D", "E", "F"
    min_score DECIMAL(5,2) NOT NULL,
    max_score DECIMAL(5,2) NOT NULL,
    grade_point DECIMAL(3,2), -- GPA scale (e.g., 4.0, 3.5)
    remark VARCHAR(50), -- "Excellent", "Very Good", "Good", etc.
    color_code VARCHAR(10), -- Hex color for UI
    is_passing BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, grade_letter),
    CONSTRAINT check_score_range CHECK (min_score <= max_score),
    CONSTRAINT check_grade_point CHECK (grade_point >= 0 AND grade_point <= 5.0)
);

-- Student Grades
CREATE TABLE IF NOT EXISTS grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    
    score DECIMAL(5,2),
    grade_letter VARCHAR(5),
    grade_point DECIMAL(3,2),
    remark TEXT,
    
    -- Metadata
    is_absent BOOLEAN DEFAULT false,
    is_excused BOOLEAN DEFAULT false,
    submitted_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit trail
    entered_by UUID REFERENCES users(id) ON DELETE SET NULL,
    entered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    modified_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(assessment_id, student_id),
    CONSTRAINT check_score_valid CHECK (score IS NULL OR (score >= 0 AND score <= 999.99))
);

-- Subject Grades Summary (Aggregated per subject per term)
CREATE TABLE IF NOT EXISTS subject_grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    
    -- Calculated scores
    ca_total DECIMAL(5,2), -- Sum of all CA scores
    exam_score DECIMAL(5,2),
    total_score DECIMAL(5,2), -- CA + Exam
    average_score DECIMAL(5,2),
    
    -- Grade info
    grade_letter VARCHAR(5),
    grade_point DECIMAL(3,2),
    
    -- Position in class
    class_position INTEGER,
    class_size INTEGER,
    
    -- Teacher's remarks
    teacher_remark TEXT,
    teacher_id UUID REFERENCES teachers(id) ON DELETE SET NULL,
    
    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(student_id, subject_id, term_id, session_id)
);

-- Report Cards (Term reports for students)
CREATE TABLE IF NOT EXISTS report_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    
    -- Overall performance
    total_score DECIMAL(6,2),
    average_score DECIMAL(5,2),
    overall_grade VARCHAR(5),
    overall_position INTEGER, -- Position in class
    class_size INTEGER,
    
    -- Attendance summary
    days_present INTEGER DEFAULT 0,
    days_absent INTEGER DEFAULT 0,
    days_late INTEGER DEFAULT 0,
    total_school_days INTEGER DEFAULT 0,
    
    -- Remarks
    class_teacher_remark TEXT,
    principal_remark TEXT,
    
    -- Approval
    status VARCHAR(20) DEFAULT 'draft', -- draft, generated, approved, published
    generated_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Next term
    resumption_date DATE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(student_id, term_id, session_id),
    CONSTRAINT check_report_status CHECK (status IN ('draft', 'generated', 'approved', 'published'))
);

-- Grade Comments (Predefined remarks for teachers)
CREATE TABLE IF NOT EXISTS grade_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    comment_type VARCHAR(50) NOT NULL, -- 'teacher', 'principal', 'performance'
    grade_range VARCHAR(10), -- 'A', 'B', 'C', 'D', 'F' or 'excellent', 'good', 'poor'
    comment_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_assessments_org_subject ON assessments(organization_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_assessments_class_term ON assessments(class_id, term_id, session_id);
CREATE INDEX IF NOT EXISTS idx_assessments_teacher ON assessments(teacher_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);

CREATE INDEX IF NOT EXISTS idx_grades_assessment ON grades(assessment_id);
CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id);
CREATE INDEX IF NOT EXISTS idx_grades_org ON grades(organization_id);

CREATE INDEX IF NOT EXISTS idx_subject_grades_student ON subject_grades(student_id);
CREATE INDEX IF NOT EXISTS idx_subject_grades_term ON subject_grades(term_id, session_id);
CREATE INDEX IF NOT EXISTS idx_subject_grades_class ON subject_grades(class_id);

CREATE INDEX IF NOT EXISTS idx_report_cards_student ON report_cards(student_id);
CREATE INDEX IF NOT EXISTS idx_report_cards_term ON report_cards(term_id, session_id);
CREATE INDEX IF NOT EXISTS idx_report_cards_status ON report_cards(status);

-- Comments
COMMENT ON TABLE assessment_types IS 'Types of assessments (CA1, CA2, Exam, etc.)';
COMMENT ON TABLE assessments IS 'Individual assessment instances for subjects';
COMMENT ON TABLE grade_configs IS 'Grading scale configuration (A-F)';
COMMENT ON TABLE grades IS 'Student scores for assessments';
COMMENT ON TABLE subject_grades IS 'Aggregated subject grades per term';
COMMENT ON TABLE report_cards IS 'Student term report cards';
COMMENT ON TABLE grade_comments IS 'Predefined remarks for reports';
