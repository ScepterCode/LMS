#!/usr/bin/env python3
"""
Add missing items to existing database without dropping tables.
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import bcrypt

# Load environment variables
load_dotenv('backend/.env')

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def main():
    print("=" * 60)
    print("ADDING MISSING DATABASE ITEMS")
    print("=" * 60)
    print()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in backend/.env")
        return
    
    print(f"📡 Connecting to: {supabase_url}")
    
    try:
        client = create_client(supabase_url, supabase_key)
        print("✅ Connected successfully!")
        print()
        
        # 1. Create campuses table if missing
        print("📋 Step 1: Creating campuses table...")
        print("   ⚠️  This needs to be done in Supabase SQL Editor")
        print("   Copy this SQL and run it in Supabase:")
        print()
        print("-" * 60)
        campuses_sql = """
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
"""
        print(campuses_sql)
        print("-" * 60)
        print()
        
        input("Press Enter after you've run the SQL in Supabase...")
        
        # 2. Add system admin account
        print("\n📋 Step 2: Adding system admin account...")
        
        # Check if system admin exists
        response = client.table('users').select('id').eq('email', 'admin@nigerianlms.com').execute()
        
        if response.data:
            print("   ℹ️  System admin already exists")
        else:
            # Create system admin
            password_hash = hash_password('Admin123!@#')
            
            admin_data = {
                'id': 'c520e1ba-8289-42b4-a242-85e501cfcc43',
                'email': 'admin@nigerianlms.com',
                'password_hash': password_hash,
                'full_name': 'System Administrator',
                'role': 'system_admin',
                'is_active': True,
                'email_verified': True
            }
            
            try:
                response = client.table('users').insert(admin_data).execute()
                print("   ✅ System admin created!")
                print(f"      Email: admin@nigerianlms.com")
                print(f"      Password: Admin123!@#")
                
                # Add to system_admins table
                try:
                    client.table('system_admins').insert({
                        'id': 'c520e1ba-8289-42b4-a242-85e501cfcc43',
                        'is_super_admin': True
                    }).execute()
                    print("   ✅ Added to system_admins table")
                except Exception as e:
                    print(f"   ⚠️  Could not add to system_admins: {e}")
                
            except Exception as e:
                print(f"   ❌ Failed to create system admin: {e}")
        
        # 3. Add Phase 1 subscription plans
        print("\n📋 Step 3: Adding Phase 1 subscription plans...")
        
        phase1_plans = [
            {
                'id': 'trial',
                'name': '14-Day Trial',
                'description': 'Free trial for new schools',
                'price_monthly': 0,
                'price_yearly': 0,
                'max_students': 50,
                'features': ["Basic Dashboard", "Up to 50 Students", "Email Support"],
                'is_active': True
            },
            {
                'id': 'basic',
                'name': 'Basic Plan',
                'description': 'For small schools',
                'price_monthly': 49.99,
                'price_yearly': 499.99,
                'max_students': 200,
                'features': ["All Trial Features", "Up to 200 Students", "Basic Reports", "Priority Support"],
                'is_active': True
            },
            {
                'id': 'standard',
                'name': 'Standard Plan',
                'description': 'For growing schools',
                'price_monthly': 99.99,
                'price_yearly': 999.99,
                'max_students': 500,
                'features': ["All Basic Features", "Up to 500 Students", "Advanced Analytics", "Phone Support"],
                'is_active': True
            },
            {
                'id': 'premium',
                'name': 'Premium Plan',
                'description': 'For large institutions',
                'price_monthly': 199.99,
                'price_yearly': 1999.99,
                'max_students': 2000,
                'features': ["All Standard Features", "Unlimited Students", "Custom Reports", "Dedicated Support", "API Access"],
                'is_active': True
            }
        ]
        
        for plan in phase1_plans:
            try:
                # Check if plan exists
                response = client.table('subscription_plans').select('id').eq('id', plan['id']).execute()
                
                if response.data:
                    print(f"   ℹ️  Plan '{plan['name']}' already exists")
                else:
                    client.table('subscription_plans').insert(plan).execute()
                    print(f"   ✅ Added plan: {plan['name']}")
            except Exception as e:
                print(f"   ⚠️  Could not add plan '{plan['name']}': {e}")
        
        # 4. Create Demo School
        print("\n📋 Step 4: Creating Demo School...")
        
        response = client.table('organizations').select('id').eq('email', 'demo@school-lagos.com').execute()
        
        if response.data:
            print("   ℹ️  Demo school already exists")
            demo_org_id = response.data[0]['id']
        else:
            demo_org = {
                'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                'name': 'Demo School Lagos',
                'slug': 'demo-school-lagos',
                'email': 'demo@school-lagos.com',
                'phone': '+234 801 234 5678',
                'address': '123 Education Street, Lagos',
                'subscription_plan_id': 'trial',
                'subscription_status': 'trial'
            }
            
            try:
                response = client.table('organizations').insert(demo_org).execute()
                print("   ✅ Demo school created!")
                demo_org_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
            except Exception as e:
                print(f"   ❌ Failed to create demo school: {e}")
                demo_org_id = None
        
        # 5. Create Demo School Admin
        if demo_org_id:
            print("\n📋 Step 5: Creating Demo School Admin...")
            
            response = client.table('users').select('id').eq('email', 'admin@demo-school.com').execute()
            
            if response.data:
                print("   ℹ️  Demo school admin already exists")
            else:
                password_hash = hash_password('Admin123!@#')
                
                demo_admin = {
                    'id': 'd1e2f3a4-b5c6-7890-def1-234567890abc',
                    'email': 'admin@demo-school.com',
                    'password_hash': password_hash,
                    'full_name': 'Demo School Admin',
                    'role': 'admin',
                    'school_id': demo_org_id,
                    'is_active': True,
                    'email_verified': True
                }
                
                try:
                    client.table('users').insert(demo_admin).execute()
                    print("   ✅ Demo school admin created!")
                    print(f"      Email: admin@demo-school.com")
                    print(f"      Password: Admin123!@#")
                except Exception as e:
                    print(f"   ❌ Failed to create demo admin: {e}")
        
        print()
        print("=" * 60)
        print("✅ SETUP COMPLETE!")
        print("=" * 60)
        print()
        print("📝 Default Accounts:")
        print("   System Admin:")
        print("     Email: admin@nigerianlms.com")
        print("     Password: Admin123!@#")
        print()
        print("   Demo School Admin:")
        print("     Email: admin@demo-school.com")
        print("     Password: Admin123!@#")
        print()
        print("🚀 Next Steps:")
        print("   1. cd backend")
        print("   2. uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
        print("   3. Open: http://127.0.0.1:8000/docs")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
