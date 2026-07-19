#!/usr/bin/env python3
"""
Check current database state using Supabase client.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv('backend/.env')

def main():
    print("=" * 60)
    print("CHECKING DATABASE STATE")
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
        
        # Check each table
        tables = [
            'users',
            'organizations',
            'subscription_plans',
            'campuses',
            'system_admins'
        ]
        
        print("📊 Checking tables:")
        print()
        
        for table in tables:
            try:
                response = client.table(table).select('count', count='exact').limit(1).execute()
                count = response.count if hasattr(response, 'count') else 'unknown'
                print(f"  ✅ {table:20} - {count} records")
            except Exception as e:
                error_msg = str(e)
                if 'does not exist' in error_msg or 'relation' in error_msg:
                    print(f"  ❌ {table:20} - TABLE NOT FOUND")
                else:
                    print(f"  ⚠️  {table:20} - Error: {error_msg[:50]}")
        
        print()
        print("=" * 60)
        
        # Try to get system admin
        print("\n🔍 Checking for system admin account:")
        try:
            response = client.table('users').select('email, full_name, role').eq('email', 'admin@learnlyf.com').execute()
            if response.data:
                admin = response.data[0]
                print(f"  ✅ Found: {admin['full_name']} ({admin['email']})")
            else:
                print("  ❌ System admin not found")
        except Exception as e:
            print(f"  ⚠️  Could not check: {e}")
        
        # Check organizations
        print("\n🏫 Checking organizations:")
        try:
            response = client.table('organizations').select('name, email, subscription_status').execute()
            if response.data:
                for org in response.data:
                    print(f"  ✅ {org['name']} - {org['subscription_status']}")
            else:
                print("  ℹ️  No organizations found")
        except Exception as e:
            print(f"  ⚠️  Could not check: {e}")
        
        # Check subscription plans
        print("\n💳 Checking subscription plans:")
        try:
            response = client.table('subscription_plans').select('id, name, price_monthly').execute()
            if response.data:
                for plan in response.data:
                    print(f"  ✅ {plan['name']} (${plan['price_monthly']}/month)")
            else:
                print("  ℹ️  No subscription plans found")
        except Exception as e:
            print(f"  ⚠️  Could not check: {e}")
        
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    main()
