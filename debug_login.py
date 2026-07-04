#!/usr/bin/env python3
"""
Debug login issue
"""

import os
import sys
sys.path.insert(0, 'backend')

from dotenv import load_dotenv
load_dotenv('backend/.env')

from app.core.database import get_supabase
from app.core.security import verify_password

def main():
    print("=" * 60)
    print("DEBUG LOGIN")
    print("=" * 60)
    print()
    
    # Get Supabase client
    supabase = get_supabase()
    if not supabase:
        print("❌ Could not get Supabase client")
        return
    
    print("✅ Supabase client created")
    print()
    
    # Query for user
    email = 'admin@nigerianlms.com'
    print(f"Querying for user: {email}")
    
    try:
        response = supabase.table('users').select('*').eq('email', email).execute()
        print(f"Response: {response}")
        print()
        
        if response.data:
            user = response.data[0]
            print(f"✅ Found user:")
            print(f"   ID: {user['id']}")
            print(f"   Email: {user['email']}")
            print(f"   Name: {user['full_name']}")
            print(f"   Role: {user['role']}")
            print(f"   Password hash: {user['password_hash']}")
            print()
            
            # Test password verification
            test_password = 'Admin123!@#'
            print(f"Testing password: {test_password}")
            
            result = verify_password(test_password, user['password_hash'])
            print(f"verify_password result: {result}")
            
            if result:
                print("✅ Password verification PASSED")
            else:
                print("❌ Password verification FAILED")
        else:
            print("❌ No user found")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
