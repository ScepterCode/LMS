"""
Verify Phase 2 Database Schema
Checks if all Phase 2 tables were created successfully in Supabase.
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

def verify_phase2_schema():
    """Verify that Phase 2 tables exist in Supabase."""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in backend/.env")
        sys.exit(1)
    
    print("=" * 60)
    print("PHASE 2 SCHEMA VERIFICATION")
    print("=" * 60)
    print()
    
    # Create Supabase client
    try:
        supabase = create_client(
            supabase_url=supabase_url,
            supabase_key=supabase_service_key
        )
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        sys.exit(1)
    
    # Tables to check
    phase2_tables = [
        'academic_sessions',
        'terms',
        'classes',
        'subjects',
        'students',
        'student_guardians',
        'teachers',
        'subject_assignments',
        'class_enrollments',
        'parents',
        'parent_student_links',
    ]
    
    print()
    print("Checking Phase 2 tables...")
    print("-" * 60)
    
    results = []
    for table in phase2_tables:
        try:
            # Try to query the table (will fail if table doesn't exist)
            response = supabase.table(table).select('count', count='exact').limit(0).execute()
            count = response.count if hasattr(response, 'count') else 0
            results.append((table, True, count))
            print(f"✅ {table:25s} - EXISTS (rows: {count})")
        except Exception as e:
            results.append((table, False, str(e)))
            print(f"❌ {table:25s} - MISSING")
    
    print()
    print("=" * 60)
    
    # Summary
    existing_tables = [r for r in results if r[1]]
    missing_tables = [r for r in results if not r[1]]
    
    print(f"Summary: {len(existing_tables)}/{len(phase2_tables)} tables exist")
    print()
    
    if len(existing_tables) == len(phase2_tables):
        print("🎉 SUCCESS! All Phase 2 tables are created!")
        print()
        print("You can now:")
        print("  1. Start building Phase 2A backend APIs")
        print("  2. Test table relationships")
        print("  3. Add sample data for testing")
        return True
    else:
        print("⚠️  Some tables are missing!")
        print()
        print("Missing tables:")
        for table, _, _ in missing_tables:
            print(f"  - {table}")
        print()
        print("Please execute the Phase 2 schema SQL:")
        print("  1. Open: https://supabase.com/dashboard")
        print("  2. Go to SQL Editor")
        print("  3. Run: database/phase2_schema.sql")
        return False

if __name__ == '__main__':
    try:
        success = verify_phase2_schema()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        sys.exit(1)
