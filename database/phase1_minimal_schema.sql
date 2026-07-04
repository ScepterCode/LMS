-- ============================================
-- PHASE 1 MVP - MINIMAL DATABASE SCHEMA
-- ============================================

-- Clean up existing tables (if any)
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;
DROP TABLE IF EXISTS subscription_plans CASCADE;

-- ============================================
-- SUBSCRIPTION PLANS (Simple pricing)
-- ============================================
CREATE TABLE subscription_plans (
    id VARCHAR(50) PRIMARY KEY,  -- 'trial', 'basic', 'standard', 'premium'
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10,2) DEFAULT 0,
    price_yearly DECIMAL(10,2) DEFAULT 0,
    max_students INTEGER DEFAULT 50,
    features JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default plans
INSERT INTO subscription_plans (id, name, description, price_monthly, price_yearly, max_students, features) VALUES
('trial', '14-Day Trial', 'Free trial for new schools', 0, 0, 50, '["Basic Dashboard", "Up to 50 Students", "Email Support"]'),
('basic', 'Basic Plan', 'For small schools', 49.99, 499.99, 200, '["All Trial Features", "Up to 200 Students", "Basic Reports", "Priority Support"]'),
('standard', 'Standard Plan', 'For growing schools', 99.99, 999.99, 500, '["All Basic Features", "Up to 500 Students", "Advanced Analytics", "Phone Support"]'),
('premium', 'Premium Plan', 'For large institutions', 199.99, 1999.99, 2000, '["All Standard Features", "Unlimited Students", "Custom Reports", "Dedicated Support", "API Access"]');

-- ============================================
-- ORGANIZATIONS (Schools)
-- ============================================
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    
    -- Subscription
    subscription_plan_id VARCHAR(50) DEFAULT 'trial' REFERENCES subscription_plans(id),
    subscription_status VARCHAR(50) DEFAULT 'trial',  -- 'trial', 'active', 'suspended', 'cancelled'
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_test_account BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_email ON organizations(email);
CREATE INDEX idx_organizations_status ON organizations(subscription_status, is_active);

-- ============================================
-- USERS (All user accounts)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    
    -- Role and school association
    role VARCHAR(50) NOT NULL CHECK (role IN ('system_admin', 'admin', 'teacher', 'bursar', 'parent')),
    school_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    
    -- Contact info
    phone VARCHAR(50),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_school_id ON users(school_id);
CREATE INDEX idx_users_role_school ON users(role, school_id);

-- ============================================
-- SYSTEM ADMINS (Platform administrators)
-- ============================================
-- Note: system_admins are also in users table with role='system_admin'
-- This table is for additional system admin metadata if needed
CREATE TABLE system_admins (
    id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    is_super_admin BOOLEAN DEFAULT false,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- CAMPUSES (School branches - optional for Phase 1)
-- ============================================
CREATE TABLE campuses (
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

CREATE INDEX idx_campuses_organization ON campuses(organization_id);

-- ============================================
-- CREATE DEFAULT SYSTEM ADMIN
-- ============================================
-- Insert a default system admin user
-- Password: Admin123!@# (will be hashed by application)
INSERT INTO users (id, email, password_hash, full_name, role, is_active, email_verified) VALUES
(
    'c520e1ba-8289-42b4-a242-85e501cfcc43',
    'admin@nigerianlms.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- Admin123!@#
    'System Administrator',
    'system_admin',
    true,
    true
);

-- Add to system_admins table
INSERT INTO system_admins (id, is_super_admin) VALUES
('c520e1ba-8289-42b4-a242-85e501cfcc43', true);

-- ============================================
-- CREATE A TEST SCHOOL FOR DEMO
-- ============================================
INSERT INTO organizations (id, name, slug, email, phone, address, subscription_plan_id, subscription_status, trial_ends_at) VALUES
(
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'Demo School Lagos',
    'demo-school-lagos',
    'demo@school-lagos.com',
    '+234 801 234 5678',
    '123 Education Street, Lagos',
    'trial',
    'trial',
    NOW() + INTERVAL '14 days'
);

-- Create admin user for demo school
INSERT INTO users (id, email, password_hash, full_name, role, school_id, is_active, email_verified) VALUES
(
    'd1e2f3a4-b5c6-7890-def1-234567890abc',
    'admin@demo-school.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- Admin123!@#
    'Demo School Admin',
    'admin',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    true,
    true
);

-- Create main campus for demo school
INSERT INTO campuses (organization_id, name, campus_name, address, phone, email, is_main_campus) VALUES
(
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'Demo School Lagos Main Campus',
    'Main Campus',
    '123 Education Street, Lagos',
    '+234 801 234 5678',
    'demo@school-lagos.com',
    true
);

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS FOR EASIER QUERYING
-- ============================================

-- View for user details with organization info
CREATE VIEW user_details AS
SELECT 
    u.id,
    u.email,
    u.full_name,
    u.role,
    u.school_id,
    o.name as school_name,
    o.slug as school_slug,
    u.phone,
    u.is_active,
    u.email_verified,
    u.created_at,
    u.updated_at
FROM users u
LEFT JOIN organizations o ON u.school_id = o.id;

-- View for organization details with plan info
CREATE VIEW organization_details AS
SELECT 
    o.id,
    o.name,
    o.slug,
    o.email,
    o.phone,
    o.address,
    o.subscription_plan_id,
    sp.name as subscription_plan_name,
    sp.price_monthly,
    sp.price_yearly,
    sp.max_students,
    o.subscription_status,
    o.trial_ends_at,
    o.is_active,
    o.is_test_account,
    o.created_at,
    o.updated_at,
    (SELECT COUNT(*) FROM users WHERE school_id = o.id AND role = 'admin') as admin_count,
    (SELECT COUNT(*) FROM users WHERE school_id = o.id AND role = 'teacher') as teacher_count,
    (SELECT COUNT(*) FROM users WHERE school_id = o.id AND role = 'bursar') as bursar_count,
    (SELECT COUNT(*) FROM users WHERE school_id = o.id AND role = 'parent') as parent_count
FROM organizations o
LEFT JOIN subscription_plans sp ON o.subscription_plan_id = sp.id;

-- ============================================
-- GRANT PERMISSIONS (Adjust based on your Supabase setup)
-- ============================================
-- Note: In Supabase, RLS (Row Level Security) should be enabled
-- These are example policies:

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE campuses ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_admins ENABLE ROW LEVEL SECURITY;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check tables were created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'organizations', 'subscription_plans', 'campuses', 'system_admins')
ORDER BY table_name;

-- Check default data
SELECT 'System Admin:' as type, email, full_name, role FROM users WHERE role = 'system_admin'
UNION ALL
SELECT 'Demo School Admin:' as type, email, full_name, role FROM users WHERE role = 'admin'
UNION ALL
SELECT 'Subscription Plans:' as type, name, CONCAT('$', price_monthly::text), id FROM subscription_plans
UNION ALL
SELECT 'Organizations:' as type, name, subscription_status, '' FROM organizations;

-- Count records
SELECT 
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM organizations) as total_organizations,
    (SELECT COUNT(*) FROM subscription_plans) as total_plans,
    (SELECT COUNT(*) FROM campuses) as total_campuses;
