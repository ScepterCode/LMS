-- =====================================================
-- Phase 6: System Admin Platform Dashboard
-- Learnlyf
--
-- Adds platform-level audit logging so system-admin actions that cross
-- organization boundaries (suspending a school, editing/deactivating a
-- user in another school, changing subscription plans, impersonating
-- an admin, etc.) leave a traceable record.
--
-- This is purely additive: one new table, no changes to any existing
-- table/column. Safe to run against the live production database -
-- CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS throughout,
-- matching the convention established in phase4/phase5.
-- =====================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Who performed the action. ON DELETE SET NULL (not CASCADE) so
    -- deleting a user account never deletes the trail of what they did.
    actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    actor_email VARCHAR(200),
    actor_role VARCHAR(50),

    -- What happened, e.g. "organization.status_changed",
    -- "user.deactivated", "subscription_plan.created",
    -- "impersonation.started".
    action VARCHAR(100) NOT NULL,

    -- What it was done to. target_type is a free-text label
    -- ("organization", "user", "subscription_plan") rather than an FK
    -- since targets span multiple tables.
    target_type VARCHAR(50),
    target_id UUID,

    -- Which school this action concerns, when applicable, so a
    -- school's own history can be filtered independently of who else
    -- was affected platform-wide.
    target_organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,

    -- Free-form structured detail (old/new values, reason, etc.)
    details JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_target_org ON audit_logs(target_organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
