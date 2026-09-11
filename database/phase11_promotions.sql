-- Phase 11: End-of-session promotion / graduation.
--
-- Additive only. Run in the Supabase SQL Editor. Safe to run on the live
-- database - no existing rows are dropped or retyped, only new nullable/
-- defaulted columns and one new table are added.
--
-- What this enables:
--   - Each academic session carries its own pass mark and whether the
--     promotion decision is based on the 3rd term alone (the Nigerian
--     norm) or the average of all 3 terms.
--   - Each class carries an explicit position in the promotion sequence
--     and whether it's the school's terminal (graduating) class, since
--     naming schemes differ a lot between schools.
--   - promotion_records is a permanent audit trail of every promote /
--     repeat / graduate decision made at session end, including whether
--     an admin overrode the computed outcome.

-- ============================================
-- 1. Academic session promotion policy
-- ============================================

ALTER TABLE academic_sessions
    ADD COLUMN IF NOT EXISTS promotion_basis TEXT NOT NULL DEFAULT 'third_term',
    ADD COLUMN IF NOT EXISTS promotion_pass_mark NUMERIC(5,2) NOT NULL DEFAULT 40.00;

ALTER TABLE academic_sessions
    ADD CONSTRAINT academic_sessions_promotion_basis_check
        CHECK (promotion_basis IN ('third_term', 'cumulative'));

ALTER TABLE academic_sessions
    ADD CONSTRAINT academic_sessions_promotion_pass_mark_check
        CHECK (promotion_pass_mark >= 0 AND promotion_pass_mark <= 100);

COMMENT ON COLUMN academic_sessions.promotion_basis IS
    'third_term: only the 3rd term score decides promotion (Nigerian norm). cumulative: average of all 3 terms.';
COMMENT ON COLUMN academic_sessions.promotion_pass_mark IS
    'Percentage a student must meet or exceed (on promotion_basis) to be promoted rather than repeat.';

-- ============================================
-- 2. Class sequencing
-- ============================================

ALTER TABLE classes
    ADD COLUMN IF NOT EXISTS sequence_order INTEGER,
    ADD COLUMN IF NOT EXISTS is_graduating_class BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN classes.sequence_order IS
    'Position of this class in the promotion sequence (lower = earlier). Null = not part of an ordered sequence yet.';
COMMENT ON COLUMN classes.is_graduating_class IS
    'A student who passes this class leaves the school (graduates) instead of moving to a next class.';

CREATE INDEX IF NOT EXISTS idx_classes_sequence_order ON classes(organization_id, sequence_order);

-- ============================================
-- 3. Promotion records (audit trail)
-- ============================================

CREATE TABLE IF NOT EXISTS promotion_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    from_class_id UUID REFERENCES classes(id) ON DELETE SET NULL,
    to_class_id UUID REFERENCES classes(id) ON DELETE SET NULL,
    decision TEXT NOT NULL CHECK (decision IN ('promoted', 'repeated', 'graduated')),
    basis_score NUMERIC(6,2),
    pass_mark_used NUMERIC(5,2),
    overridden BOOLEAN NOT NULL DEFAULT false,
    override_reason TEXT,
    decided_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_promotion_records_org ON promotion_records(organization_id);
CREATE INDEX IF NOT EXISTS idx_promotion_records_session ON promotion_records(session_id);
CREATE INDEX IF NOT EXISTS idx_promotion_records_student ON promotion_records(student_id);

-- A student can only have one promotion decision per session.
CREATE UNIQUE INDEX IF NOT EXISTS uq_promotion_records_student_session
    ON promotion_records(student_id, session_id);
