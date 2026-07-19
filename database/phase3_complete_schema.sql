-- =====================================================
-- Phase 3: Complete Schema - All High Priority Features
-- Learnlyf
-- 
-- This schema includes:
-- 1. Grading & Assessment System (8 tables)
-- 2. Attendance Management (6 tables)
-- 3. Fee Management (9 tables)
--
-- Total: 23 new tables
-- =====================================================

-- =====================================================
-- PART 1: GRADING & ASSESSMENT SYSTEM
-- =====================================================

\echo 'Creating Grading & Assessment tables...'

\i phase3_grading_schema.sql

-- =====================================================
-- PART 2: ATTENDANCE MANAGEMENT
-- =====================================================

\echo 'Creating Attendance Management tables...'

\i phase3_attendance_schema.sql

-- =====================================================
-- PART 3: FEE MANAGEMENT
-- =====================================================

\echo 'Creating Fee Management tables...'

\i phase3_fees_schema.sql

-- =====================================================
-- DEFAULT DATA SEEDING
-- =====================================================

\echo 'Seeding default data...'

-- Default Grade Configuration (Nigerian System)
INSERT INTO grade_configs (organization_id, grade_letter, min_score, max_score, grade_point, remark, color_code, is_passing, display_order)
SELECT 
    o.id as organization_id,
    grade_letter,
    min_score,
    max_score,
    grade_point,
    remark,
    color_code,
    is_passing,
    display_order
FROM organizations o
CROSS JOIN (VALUES
    ('A', 70.00, 100.00, 5.00, 'Excellent', '#10B981', true, 1),
    ('B', 60.00, 69.99, 4.00, 'Very Good', '#3B82F6', true, 2),
    ('C', 50.00, 59.99, 3.00, 'Good', '#F59E0B', true, 3),
    ('D', 45.00, 49.99, 2.00, 'Pass', '#EF4444', true, 4),
    ('E', 40.00, 44.99, 1.00, 'Poor', '#DC2626', true, 5),
    ('F', 0.00, 39.99, 0.00, 'Fail', '#991B1B', false, 6)
) AS grades(grade_letter, min_score, max_score, grade_point, remark, color_code, is_passing, display_order)
ON CONFLICT (organization_id, grade_letter) DO NOTHING;

-- Default Assessment Types
INSERT INTO assessment_types (organization_id, name, code, max_score, weight_percentage, display_order)
SELECT 
    o.id as organization_id,
    name,
    code,
    max_score,
    weight_percentage,
    display_order
FROM organizations o
CROSS JOIN (VALUES
    ('First Continuous Assessment', 'CA1', 20.00, 10.00, 1),
    ('Second Continuous Assessment', 'CA2', 20.00, 10.00, 2),
    ('Third Continuous Assessment', 'CA3', 20.00, 10.00, 3),
    ('Midterm Test', 'MID', 20.00, 10.00, 4),
    ('Examination', 'EXAM', 60.00, 60.00, 5)
) AS types(name, code, max_score, weight_percentage, display_order)
ON CONFLICT (organization_id, code) DO NOTHING;

-- Default Fee Categories
INSERT INTO fee_categories (organization_id, name, code, is_mandatory, display_order)
SELECT 
    o.id as organization_id,
    name,
    code,
    is_mandatory,
    display_order
FROM organizations o
CROSS JOIN (VALUES
    ('Tuition Fee', 'TUITION', true, 1),
    ('Development Levy', 'DEVELOPMENT', true, 2),
    ('PTA Dues', 'PTA', true, 3),
    ('Sports Fee', 'SPORTS', false, 4),
    ('Lesson Note', 'LESSON', false, 5),
    ('Uniform', 'UNIFORM', false, 6),
    ('Textbooks', 'BOOKS', false, 7),
    ('Transport', 'TRANSPORT', false, 8),
    ('Feeding', 'FEEDING', false, 9),
    ('ICT Fee', 'ICT', false, 10)
) AS categories(name, code, is_mandatory, display_order)
ON CONFLICT (organization_id, code) DO NOTHING;

-- Default Attendance Settings
INSERT INTO attendance_settings (organization_id, school_start_time, school_end_time, late_threshold_minutes)
SELECT 
    id as organization_id,
    '08:00:00'::time,
    '14:00:00'::time,
    15
FROM organizations
ON CONFLICT (organization_id) DO NOTHING;

-- Default Grade Comments
INSERT INTO grade_comments (organization_id, comment_type, grade_range, comment_text, is_active)
SELECT 
    o.id as organization_id,
    comment_type,
    grade_range,
    comment_text,
    true
FROM organizations o
CROSS JOIN (VALUES
    ('teacher', 'A', 'Excellent performance. Keep it up!'),
    ('teacher', 'B', 'Very good work. You can do even better.'),
    ('teacher', 'C', 'Good effort. Continue to work hard.'),
    ('teacher', 'D', 'Fair performance. More effort is needed.'),
    ('teacher', 'E', 'Poor performance. Serious attention required.'),
    ('teacher', 'F', 'Very poor performance. Urgent intervention needed.'),
    ('principal', 'excellent', 'An exemplary student. Well done!'),
    ('principal', 'good', 'Satisfactory performance. Keep improving.'),
    ('principal', 'poor', 'Performance needs significant improvement.')
) AS comments(comment_type, grade_range, comment_text);

\echo 'Phase 3 schema creation complete!'
\echo 'Tables created: 23'
\echo '  - Grading: 8 tables'
\echo '  - Attendance: 6 tables'
\echo '  - Fees: 9 tables'
