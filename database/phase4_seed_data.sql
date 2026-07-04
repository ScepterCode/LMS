-- =====================================================
-- Phase 4: Migrate & Seed Data
-- Seeding default grading schemes and migration helpers
-- =====================================================

\echo 'Seeding Phase 4 data...'

-- =====================================================
-- DEFAULT GRADING SCHEMES
-- =====================================================

\echo 'Creating default grading schemes...'

INSERT INTO grading_schemes (organization_id, session_id, name, description, is_active, is_default)
SELECT 
    o.id as organization_id,
    (SELECT id FROM academic_sessions WHERE organization_id = o.id ORDER BY created_at DESC LIMIT 1) as session_id,
    name,
    description,
    true,
    is_default
FROM organizations o
CROSS JOIN (VALUES
    ('20-20-60', 'Two tests (20% each) and one exam (60%)', false),
    ('20-20-20-40', 'Two tests (20% each), coursework (20%), and exam (40%)', true),
    ('20-40-40', 'One test (20%), coursework (40%), and exam (40%)', false),
    ('10-10-10-70', 'Three continuous assessments (10% each) and exam (70%)', false),
    ('100-Exam-Only', 'Single exam grading (100%)', false)
) AS schemes(name, description, is_default)
ON CONFLICT (organization_id, session_id, name) DO NOTHING;

-- =====================================================
-- GRADING SCHEME COMPONENTS (for 20-20-60)
-- =====================================================

\echo 'Creating grading scheme components for 20-20-60...'

INSERT INTO grading_scheme_components (grading_scheme_id, component_type, component_name, weight_percentage, max_score, required, display_order)
SELECT 
    gs.id,
    component_type,
    component_name,
    weight_percentage,
    max_score,
    required,
    display_order
FROM grading_schemes gs
CROSS JOIN (VALUES
    ('test', 'Test 1', 20.00, 20.00, true, 1),
    ('test', 'Test 2', 20.00, 20.00, true, 2),
    ('exam', 'Final Exam', 60.00, 60.00, true, 3)
) AS components(component_type, component_name, weight_percentage, max_score, required, display_order)
WHERE gs.name = '20-20-60'
ON CONFLICT (grading_scheme_id, component_name) DO NOTHING;

-- =====================================================
-- GRADING SCHEME COMPONENTS (for 20-20-20-40)
-- =====================================================

\echo 'Creating grading scheme components for 20-20-20-40...'

INSERT INTO grading_scheme_components (grading_scheme_id, component_type, component_name, weight_percentage, max_score, required, display_order)
SELECT 
    gs.id,
    component_type,
    component_name,
    weight_percentage,
    max_score,
    required,
    display_order
FROM grading_schemes gs
CROSS JOIN (VALUES
    ('test', 'Test 1', 20.00, 20.00, true, 1),
    ('test', 'Test 2', 20.00, 20.00, true, 2),
    ('coursework', 'Coursework', 20.00, 20.00, true, 3),
    ('exam', 'Final Exam', 40.00, 40.00, true, 4)
) AS components(component_type, component_name, weight_percentage, max_score, required, display_order)
WHERE gs.name = '20-20-20-40'
ON CONFLICT (grading_scheme_id, component_name) DO NOTHING;

-- =====================================================
-- GRADING SCHEME COMPONENTS (for 20-40-40)
-- =====================================================

\echo 'Creating grading scheme components for 20-40-40...'

INSERT INTO grading_scheme_components (grading_scheme_id, component_type, component_name, weight_percentage, max_score, required, display_order)
SELECT 
    gs.id,
    component_type,
    component_name,
    weight_percentage,
    max_score,
    required,
    display_order
FROM grading_schemes gs
CROSS JOIN (VALUES
    ('test', 'Test', 20.00, 20.00, true, 1),
    ('coursework', 'Coursework', 40.00, 40.00, true, 2),
    ('exam', 'Final Exam', 40.00, 40.00, true, 3)
) AS components(component_type, component_name, weight_percentage, max_score, required, display_order)
WHERE gs.name = '20-40-40'
ON CONFLICT (grading_scheme_id, component_name) DO NOTHING;

-- =====================================================
-- GRADING SCHEME COMPONENTS (for 10-10-10-70)
-- =====================================================

\echo 'Creating grading scheme components for 10-10-10-70...'

INSERT INTO grading_scheme_components (grading_scheme_id, component_type, component_name, weight_percentage, max_score, required, display_order)
SELECT 
    gs.id,
    component_type,
    component_name,
    weight_percentage,
    max_score,
    required,
    display_order
FROM grading_schemes gs
CROSS JOIN (VALUES
    ('assignment', 'Continuous Assessment 1', 10.00, 10.00, true, 1),
    ('assignment', 'Continuous Assessment 2', 10.00, 10.00, true, 2),
    ('assignment', 'Continuous Assessment 3', 10.00, 10.00, true, 3),
    ('exam', 'Final Exam', 70.00, 70.00, true, 4)
) AS components(component_type, component_name, weight_percentage, max_score, required, display_order)
WHERE gs.name = '10-10-10-70'
ON CONFLICT (grading_scheme_id, component_name) DO NOTHING;

-- =====================================================
-- POPULATE CLASS SUBJECTS FROM EXISTING DATA
-- =====================================================

\echo 'Populating class_subjects from existing subject_assignments...'

INSERT INTO class_subjects (class_id, subject_id, session_id, is_mandatory, display_order)
SELECT DISTINCT
    sa.class_id,
    sa.subject_id,
    sa.session_id,
    true,
    0
FROM subject_assignments sa
WHERE NOT EXISTS (
    SELECT 1 FROM class_subjects cs 
    WHERE cs.class_id = sa.class_id 
    AND cs.subject_id = sa.subject_id 
    AND cs.session_id = sa.session_id
)
ON CONFLICT (class_id, subject_id, session_id) DO NOTHING;

-- =====================================================
-- POPULATE TEACHER CLASS ASSIGNMENTS
-- =====================================================

\echo 'Migrating data to teacher_class_assignments...'

INSERT INTO teacher_class_assignments (teacher_id, class_id, subject_id, session_id, term_id, is_form_teacher)
SELECT
    sa.teacher_id,
    sa.class_id,
    sa.subject_id,
    sa.session_id,
    sa.term_id,
    (c.class_teacher_id = t.user_id) as is_form_teacher
FROM subject_assignments sa
JOIN classes c ON sa.class_id = c.id
JOIN teachers t ON sa.teacher_id = t.id
WHERE NOT EXISTS (
    SELECT 1 FROM teacher_class_assignments tca
    WHERE tca.teacher_id = sa.teacher_id
    AND tca.subject_id = sa.subject_id
    AND tca.class_id = sa.class_id
    AND tca.term_id = sa.term_id
)
ON CONFLICT (teacher_id, subject_id, class_id, term_id) DO NOTHING;

\echo 'Phase 4 data seeding complete!'
