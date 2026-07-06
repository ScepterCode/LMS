-- =====================================================
-- Phase 5: Report Card Enhancements
-- Nigerian School Management System
--
-- This schema adds school branding (logo/motto) to organizations,
-- snapshots full attendance detail onto report cards, and adds an
-- admin-configurable list of psychomotor/affective skill traits that
-- form teachers rate per student per term.
--
-- Changes:
-- 1. organizations: + logo_url, motto
-- 2. report_cards: + days_excused, attendance_percentage, punctuality_percentage
-- 3. skill_categories - admin-configurable trait list (new table)
-- 4. student_skill_ratings - form-teacher-entered ratings (new table)
-- 5. Seed default trait list for existing organizations
-- =====================================================

\echo 'Creating Phase 5: Report Card Enhancements...'

-- =====================================================
-- PART 1: ORGANIZATION BRANDING
-- =====================================================

\echo 'Adding branding columns to organizations...'

ALTER TABLE organizations ADD COLUMN IF NOT EXISTS logo_url TEXT;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS motto VARCHAR(255);

-- =====================================================
-- PART 2: REPORT CARD ATTENDANCE DETAIL
-- =====================================================

\echo 'Adding attendance detail columns to report_cards...'

ALTER TABLE report_cards ADD COLUMN IF NOT EXISTS days_excused INTEGER DEFAULT 0;
ALTER TABLE report_cards ADD COLUMN IF NOT EXISTS attendance_percentage DECIMAL(5,2);
ALTER TABLE report_cards ADD COLUMN IF NOT EXISTS punctuality_percentage DECIMAL(5,2);

-- =====================================================
-- PART 3: SKILL CATEGORIES (admin-configurable trait list)
-- =====================================================

\echo 'Creating skill_categories table...'

CREATE TABLE IF NOT EXISTS skill_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    domain VARCHAR(20) NOT NULL DEFAULT 'psychomotor' CHECK (domain IN ('psychomotor', 'affective')),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, name)
);

CREATE INDEX IF NOT EXISTS idx_skill_categories_org ON skill_categories(organization_id);
CREATE INDEX IF NOT EXISTS idx_skill_categories_active ON skill_categories(organization_id, is_active);

-- =====================================================
-- PART 4: STUDENT SKILL RATINGS
-- =====================================================

\echo 'Creating student_skill_ratings table...'

CREATE TABLE IF NOT EXISTS student_skill_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    skill_category_id UUID NOT NULL REFERENCES skill_categories(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    rated_by UUID REFERENCES teachers(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, skill_category_id, term_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_student_skill_ratings_student ON student_skill_ratings(student_id);
CREATE INDEX IF NOT EXISTS idx_student_skill_ratings_category ON student_skill_ratings(skill_category_id);
CREATE INDEX IF NOT EXISTS idx_student_skill_ratings_session_term ON student_skill_ratings(session_id, term_id);

-- =====================================================
-- PART 5: SEED DEFAULT TRAITS FOR EXISTING ORGANIZATIONS
-- =====================================================

\echo 'Seeding default skill categories for existing organizations...'

INSERT INTO skill_categories (organization_id, name, domain, display_order)
SELECT o.id, t.name, t.domain, t.display_order
FROM organizations o
CROSS JOIN (
    VALUES
        ('Sports & Games', 'psychomotor', 1),
        ('Handling of Tools/Equipment', 'psychomotor', 2),
        ('Handwriting', 'psychomotor', 3),
        ('Musical Skills', 'psychomotor', 4),
        ('Punctuality', 'affective', 1),
        ('Neatness', 'affective', 2),
        ('Honesty', 'affective', 3)
) AS t(name, domain, display_order)
ON CONFLICT (organization_id, name) DO NOTHING;

\echo 'Phase 5 tables created and seeded successfully!'
