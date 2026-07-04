#!/usr/bin/env python3
"""Create demo data directly via Supabase client"""

from supabase import create_client
import os
from datetime import datetime

# Get Supabase credentials from environment or use defaults
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://gygzsasweryajcleolie.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5Z3pzYXN3ZXJ5YWpjbGVvbGllIiwicm9sZSI6ImFub24iLCJpYXQiOjE2NzE4NzE4NzcsImV4cCI6MTk4NzQ0Nzg3N30.FTymkEsmfKheFOHo7J0Uz3L-r0cLbBgqpf9xE9RD8vA')

ORG_ID = "51a15349-47f9-4449-ae63-3daaf16de14e"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("DEMO HIGH SCHOOL - DIRECT DATA SETUP VIA SUPABASE")
print("=" * 70)

# Check existing sessions
print("\n[1] Checking existing sessions...")
sessions = supabase.table('academic_sessions').select('*').eq('organization_id', ORG_ID).execute()
print(f"Found {len(sessions.data)} existing sessions")
for s in sessions.data:
    print(f"  - {s['name']} (ID: {s['id']}, is_current: {s['is_current']})")

# Create session
print("\n[2] Creating academic session (2024/2025)...")
session_data = {
    'organization_id': ORG_ID,
    'name': '2024/2025',
    'start_date': '2024-09-01',
    'end_date': '2025-07-31',
    'is_current': True,
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}

try:
    result = supabase.table('academic_sessions').insert(session_data).execute()
    if result.data:
        session = result.data[0]
        session_id = session['id']
        print(f"✓ Created session: {session['name']} (ID: {session_id})")
    else:
        print(f"✗ No data returned from insert")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Create term
print("\n[3] Creating first term...")
term_data = {
    'organization_id': ORG_ID,
    'session_id': session_id,
    'name': 'First Term',
    'start_date': '2024-09-01',
    'end_date': '2024-11-30',
    'is_current': True,
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}

try:
    result = supabase.table('terms').insert(term_data).execute()
    if result.data:
        term = result.data[0]
        term_id = term['id']
        print(f"✓ Created term: {term['name']} (ID: {term_id})")
    else:
        print(f"✗ No data returned from insert")
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"   This might be because terms table needs different schema")

# Create subject
print("\n[4] Creating subject (Mathematics)...")
subject_data = {
    'organization_id': ORG_ID,
    'code': 'MTH',
    'name': 'Mathematics',
    'description': 'Core mathematics subject',
    'is_active': True,
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}

try:
    result = supabase.table('subjects').insert(subject_data).execute()
    if result.data:
        subject = result.data[0]
        subject_id = subject['id']
        print(f"✓ Created subject: {subject['name']} (ID: {subject_id})")
    else:
        print(f"✗ No data returned from insert")
except Exception as e:
    print(f"✗ Error: {e}")

# Create class
print("\n[5] Creating class (JSS1)...")
class_data = {
    'organization_id': ORG_ID,
    'session_id': session_id,
    'code': 'JSS1',
    'name': 'Junior Secondary School 1',
    'capacity': 40,
    'is_active': True,
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}

try:
    result = supabase.table('classes').insert(class_data).execute()
    if result.data:
        class_obj = result.data[0]
        class_id = class_obj['id']
        print(f"✓ Created class: {class_obj['name']} (ID: {class_id})")
    else:
        print(f"✗ No data returned from insert")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 70)
print("✓ FOUNDATIONAL DATA CREATED")
print("=" * 70)
