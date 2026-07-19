#!/usr/bin/env python3
"""
Apply Phase 1 MVP database schema to Supabase.
Run this script to set up the minimal database structure.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment or user input"""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("⚠️  DATABASE_URL not found in .env file")
        print("\nPlease enter your Supabase database connection string:")
        print("Format: postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres")
        db_url = input("Database URL: ").strip()
        
        if not db_url:
            print("❌ No database URL provided. Exiting.")
            sys.exit(1)
    
    return db_url

def read_schema_file():
    """Read the SQL schema file"""
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'phase1_minimal_schema.sql')
    
    if not os.path.exists(schema_path):
        print(f"❌ Schema file not found: {schema_path}")
        sys.exit(1)
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return f.read()

def apply_schema():
    """Apply the schema to the database"""
    db_url = get_database_url()
    schema_sql = read_schema_file()
    
    print("🔧 Applying Phase 1 MVP database schema...")
    print(f"📁 Database: {db_url.split('@')[1] if '@' in db_url else db_url}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Split SQL into individual statements
        # Simple split on semicolons (not perfect but works for our schema)
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        # Execute each statement
        for i, stmt in enumerate(statements, 1):
            try:
                if stmt.upper().startswith('DROP') or stmt.upper().startswith('CREATE') or stmt.upper().startswith('INSERT') or stmt.upper().startswith('ALTER'):
                    print(f"  [{i}/{len(statements)}] Executing: {stmt[:50]}...")
                    cursor.execute(stmt)
                elif stmt.upper().startswith('SELECT'):
                    # For SELECT statements, execute and show results
                    cursor.execute(stmt)
                    results = cursor.fetchall()
                    if results:
                        print(f"  [{i}/{len(statements)}] Query results:")
                        for row in results:
                            print(f"    {row}")
            except Exception as e:
                print(f"  ⚠️  Warning on statement {i}: {e}")
                # Continue with next statement
        
        # Verify the schema was applied
        print("\n✅ Schema applied successfully!")
        print("\n📊 Verification queries:")
        
        # List tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"  Tables created: {', '.join([t[0] for t in tables])}")
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"  Total users: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM organizations")
        org_count = cursor.fetchone()[0]
        print(f"  Total organizations: {org_count}")
        
        # Show system admin
        cursor.execute("SELECT email, full_name, role FROM users WHERE role = 'system_admin'")
        sys_admin = cursor.fetchone()
        if sys_admin:
            print(f"  System admin: {sys_admin[1]} ({sys_admin[0]})")
        
        # Show demo school
        cursor.execute("SELECT name, email, subscription_status FROM organizations")
        orgs = cursor.fetchall()
        for org in orgs:
            print(f"  Organization: {org[0]} ({org[1]}) - Status: {org[2]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Database setup complete!")
        print("\n📝 Next steps:")
        print("  1. Start backend server: uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
        print("  2. Start frontend server: npm run dev")
        print("  3. Test login with: admin@learnlyf.com / Admin123!@#")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("  - Check your DATABASE_URL in .env file")
        print("  - Make sure Supabase project is running")
        print("  - Check if password is correct")
        print("  - Windows users: Try using 127.0.0.1 instead of localhost if having DNS issues")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("LEARNLYF - PHASE 1 MVP DATABASE SETUP")
    print("=" * 60)
    print()
    
    # Check if we should proceed
    response = input("This will DROP existing tables and create fresh ones. Continue? (y/N): ").strip().lower()
    
    if response not in ['y', 'yes']:
        print("Operation cancelled.")
        sys.exit(0)
    
    apply_schema()