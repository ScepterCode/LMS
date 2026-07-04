-- Create campuses table for Phase 1 MVP
-- Run this in Supabase SQL Editor

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

ALTER TABLE campuses ENABLE ROW LEVEL SECURITY;

-- Verify table was created
SELECT 'Campuses table created successfully!' as message;
