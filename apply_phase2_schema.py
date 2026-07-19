"""
Apply Phase 2 Database Schema to Supabase
This script reads the Phase 2 SQL schema and applies it to your Supabase database.
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

def apply_phase2_schema():
    """Apply Phase 2 database schema to Supabase."""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in backend/.env")
        sys.exit(1)
    
    print("=" * 60)
    print("LEARNLYF - PHASE 2 SCHEMA APPLICATION")
    print("=" * 60)
    print(f"Supabase URL: {supabase_url}")
    print()
    
    # Read SQL schema file
    try:
        with open('database/phase2_schema.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print("✅ Phase 2 schema file loaded successfully")
    except FileNotFoundError:
        print("❌ Error: database/phase2_schema.sql not found")
        sys.exit(1)
    
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
    
    print()
    print("=" * 60)
    print("IMPORTANT: Execute SQL Directly in Supabase SQL Editor")
    print("=" * 60)
    print()
    print("The Supabase Python client doesn't support executing DDL statements.")
    print("Please follow these steps:")
    print()
    print("1. Go to: https://supabase.com/dashboard/project/gygzsasweryajcleolie/sql/new")
    print("2. Copy the entire contents of 'database/phase2_schema.sql'")
    print("3. Paste it into the SQL Editor")
    print("4. Click 'Run' to execute")
    print()
    print("Alternatively, use the PostgreSQL connection string with psql:")
    print()
    database_url = os.getenv('DATABASE_URL', '')
    if database_url:
        print(f"   psql \"{database_url}\" < database/phase2_schema.sql")
    print()
    print("=" * 60)
    print()
    
    # Show summary of what will be created
    print("📋 TABLES THAT WILL BE CREATED:")
    print("=" * 60)
    tables = [
        "academic_sessions - School years (2024/2025)",
        "terms - Terms/semesters (1st, 2nd, 3rd)",
        "classes - Class levels with sections (JSS 1A, SS 2B)",
        "subjects - Subject catalog (Mathematics, English)",
        "students - Student records with full details",
        "student_guardians - Guardian/parent information",
        "teachers - Teacher records linked to users",
        "subject_assignments - Teacher-subject-class mapping",
        "class_enrollments - Student class assignments",
        "parents - Parent user accounts",
        "parent_student_links - Parent-student relationships",
    ]
    
    for idx, table in enumerate(tables, 1):
        print(f"  {idx:2d}. {table}")
    
    print()
    print("=" * 60)
    print()
    
    # Offer to open the SQL file
    print("📄 SQL File Location: database/phase2_schema.sql")
    print()
    
    response = input("Would you like to open the SQL file now? (y/n): ").strip().lower()
    if response == 'y':
        import platform
        import subprocess
        
        file_path = os.path.abspath('database/phase2_schema.sql')
        
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', file_path])
            else:  # Linux
                subprocess.call(['xdg-open', file_path])
            print("✅ SQL file opened")
        except Exception as e:
            print(f"⚠️  Could not open file automatically: {e}")
            print(f"   Please open manually: {file_path}")
    
    print()
    print("=" * 60)
    print("✅ PHASE 2 SCHEMA PREPARATION COMPLETE")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. Execute the SQL in Supabase SQL Editor")
    print("2. Verify tables were created in Supabase Table Editor")
    print("3. Run 'python verify_phase2_schema.py' to verify")
    print()

if __name__ == '__main__':
    try:
        apply_phase2_schema()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
