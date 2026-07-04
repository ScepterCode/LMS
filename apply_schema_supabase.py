#!/usr/bin/env python3
"""
Apply Phase 1 MVP database schema using Supabase client.
This version works better on Windows where DNS resolution may fail.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv('backend/.env')

def get_supabase_client():
    """Get Supabase client"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL or SUPABASE_SERVICE_KEY not found in backend/.env")
        sys.exit(1)
    
    return create_client(supabase_url, supabase_key)

def read_schema_file():
    """Read the SQL schema file"""
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'phase1_minimal_schema.sql')
    
    if not os.path.exists(schema_path):
        print(f"❌ Schema file not found: {schema_path}")
        sys.exit(1)
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return f.read()

def apply_schema():
    """Apply the schema using Supabase SQL editor"""
    print("🔧 Applying Phase 1 MVP database schema via Supabase...")
    
    try:
        client = get_supabase_client()
        schema_sql = read_schema_file()
        
        print("📝 Executing SQL schema...")
        
        # Use Supabase's RPC to execute raw SQL
        # Note: This requires the SQL to be executed via Supabase's SQL editor or API
        response = client.rpc('exec_sql', {'query': schema_sql}).execute()
        
        print("✅ Schema applied successfully!")
        
    except Exception as e:
        # If RPC doesn't work, provide manual instructions
        print(f"⚠️  Automatic execution not available: {e}")
        print("\n" + "="*60)
        print("MANUAL SETUP REQUIRED")
        print("="*60)
        print("\nPlease follow these steps:")
        print("\n1. Open your Supabase Dashboard:")
        print(f"   {os.getenv('SUPABASE_URL')}")
        print("\n2. Go to: SQL Editor (in left sidebar)")
        print("\n3. Click 'New Query'")
        print("\n4. Copy the SQL from: database/phase1_minimal_schema.sql")
        print("\n5. Paste it into the SQL editor")
        print("\n6. Click 'Run' (or press Ctrl+Enter)")
        print("\n7. Wait for execution to complete")
        print("\n8. You should see: 'Success. No rows returned'")
        print("\n" + "="*60)
        
        # Offer to open the file
        print("\n💡 I'll verify the schema after you run it in Supabase.")
        input("\nPress Enter after you've run the SQL in Supabase...")
        
        # Verify the schema was applied
        verify_schema(client)

def verify_schema(client):
    """Verify the schema was applied correctly"""
    print("\n🔍 Verifying database schema...")
    
    try:
        # Check if tables exist by querying them
        tables_to_check = [
            ('users', 'Users table'),
            ('organizations', 'Organizations table'),
            ('subscription_plans', 'Subscription plans table'),
            ('campuses', 'Campuses table'),
            ('system_admins', 'System admins table')
        ]
        
        all_exist = True
        for table_name, description in tables_to_check:
            try:
                response = client.table(table_name).select('count', count='exact').limit(1).execute()
                print(f"  ✅ {description} exists")
            except Exception as e:
                print(f"  ❌ {description} not found: {e}")
                all_exist = False
        
        if not all_exist:
            print("\n❌ Some tables are missing. Please run the SQL in Supabase.")
            return False
        
        # Check default data
        print("\n📊 Checking default data...")
        
        # Check system admin
        try:
            response = client.table('users').select('email, full_name, role').eq('email', 'admin@nigerianlms.com').execute()
            if response.data:
                print(f"  ✅ System admin: {response.data[0]['full_name']} ({response.data[0]['email']})")
            else:
                print("  ⚠️  System admin not found")
        except Exception as e:
            print(f"  ⚠️  Could not check system admin: {e}")
        
        # Check subscription plans
        try:
            response = client.table('subscription_plans').select('count', count='exact').execute()
            count = response.count if hasattr(response, 'count') else len(response.data)
            print(f"  ✅ Subscription plans: {count} plans")
        except Exception as e:
            print(f"  ⚠️  Could not check subscription plans: {e}")
        
        # Check organizations
        try:
            response = client.table('organizations').select('name, subscription_status').execute()
            if response.data:
                for org in response.data:
                    print(f"  ✅ Organization: {org['name']} (Status: {org['subscription_status']})")
            else:
                print("  ⚠️  No organizations found")
        except Exception as e:
            print(f"  ⚠️  Could not check organizations: {e}")
        
        print("\n🎉 Database setup complete!")
        print("\n📝 Next steps:")
        print("  1. Start backend server: cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
        print("  2. Open API docs: http://127.0.0.1:8000/docs")
        print("  3. Test login with: admin@nigerianlms.com / Admin123!@#")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("NIGERIAN LMS - PHASE 1 MVP DATABASE SETUP")
    print("(Supabase Client Version)")
    print("=" * 60)
    print()
    
    # Check if we should proceed
    response = input("This will DROP existing tables and create fresh ones. Continue? (y/N): ").strip().lower()
    
    if response not in ['y', 'yes']:
        print("Operation cancelled.")
        sys.exit(0)
    
    apply_schema()

if __name__ == "__main__":
    main()
