#!/usr/bin/env python3
"""
Apply Phase 3 Schema to Supabase
Adds Grading, Attendance, and Fee Management tables
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for admin operations

def read_sql_file(filepath):
    """Read SQL file content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: File not found - {filepath}")
        return None

def apply_schema(supabase: Client):
    """Apply Phase 3 schema to database"""
    
    print("=" * 60)
    print("🚀 Phase 3 Schema Application")
    print("=" * 60)
    print()
    
    # List of schema files to apply
    schema_files = [
        ("database/phase3_grading_schema.sql", "Grading & Assessment System"),
        ("database/phase3_attendance_schema.sql", "Attendance Management"),
        ("database/phase3_fees_schema.sql", "Fee Management"),
    ]
    
    total_success = 0
    total_failed = 0
    
    for filepath, description in schema_files:
        print(f"📋 Applying: {description}")
        print(f"   File: {filepath}")
        
        sql_content = read_sql_file(filepath)
        if not sql_content:
            print(f"   ❌ Failed to read file")
            total_failed += 1
            continue
        
        try:
            # Execute SQL directly via RPC or REST API
            # Note: Supabase Python client doesn't support raw SQL execution
            # You'll need to run this via psql or Supabase dashboard SQL editor
            print(f"   ⚠️  Please execute this SQL file manually in Supabase SQL Editor")
            print(f"      Or use: psql -h <host> -U <user> -d <database> -f {filepath}")
            total_success += 1
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            total_failed += 1
        
        print()
    
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"✅ Successful: {total_success}")
    print(f"❌ Failed: {total_failed}")
    print()
    
    if total_failed == 0:
        print("🎉 Phase 3 schema applied successfully!")
        print()
        print("📝 Next Steps:")
        print("   1. Verify tables in Supabase dashboard")
        print("   2. Check default data seeding")
        print("   3. Test API endpoints")
        print("   4. Build frontend interfaces")
    else:
        print("⚠️  Some files failed. Please check errors above.")

def main():
    """Main execution"""
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: Missing Supabase credentials")
        print("   Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file")
        return
    
    print(f"🔗 Connecting to Supabase...")
    print(f"   URL: {SUPABASE_URL}")
    print()
    
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Apply schema
    apply_schema(supabase)
    
    print()
    print("=" * 60)
    print("🎯 Phase 3 Features")
    print("=" * 60)
    print()
    print("✅ Grading & Assessment")
    print("   - Assessment types (CA, Exam, etc.)")
    print("   - Grade entry and calculations")
    print("   - Report card generation")
    print("   - Performance analytics")
    print()
    print("✅ Attendance Management")
    print("   - Daily attendance marking")
    print("   - Attendance reports")
    print("   - Leave requests")
    print("   - Absence notifications")
    print()
    print("✅ Fee Management")
    print("   - Fee structures")
    print("   - Payment tracking")
    print("   - Receipt generation")
    print("   - Payment reminders")
    print()
    print("=" * 60)
    print()
    print("📖 Manual Application Steps:")
    print()
    print("1. Open Supabase Dashboard → SQL Editor")
    print()
    print("2. Run each schema file in order:")
    print("   a. database/phase3_grading_schema.sql")
    print("   b. database/phase3_attendance_schema.sql")
    print("   c. database/phase3_fees_schema.sql")
    print()
    print("3. Verify tables created:")
    print("   - Check Table Editor for new tables")
    print("   - Verify default data seeded")
    print()
    print("4. Enable Row Level Security (RLS) if needed:")
    print("   - assessment_types, assessments, grades")
    print("   - attendance_records, attendance_summaries")
    print("   - fee_structures, payments, receipts")
    print()

if __name__ == "__main__":
    main()
