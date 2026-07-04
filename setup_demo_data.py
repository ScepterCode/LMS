#!/usr/bin/env python3
"""
Setup demo data for Demo High School to enable onboarding workflow.
Creates: Session, Class, Subject, Student, Teacher, Parent
"""

import requests
import json
from datetime import date, datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"

# Demo High School admin credentials
ADMIN_EMAIL = "admin@demohighschool.edu.ng"
ADMIN_PASSWORD = "DemoSchool123!@#"
ORG_ID = "51a15349-47f9-4449-ae63-3daaf16de14e"

# ===========================
# LOGIN
# ===========================
print("=" * 70)
print("DEMO HIGH SCHOOL - DATA SETUP")
print("=" * 70)
print("\n[1/7] Logging in as school admin...")

login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
)
login_response.raise_for_status()
login_data = login_response.json()
token = login_data["access_token"]
user = login_data["user"]
school_id = user["school_id"]

print(f"✓ Logged in as: {user['email']} (Role: {user['role']})")
print(f"✓ School ID: {school_id}")

headers = {"Authorization": f"Bearer {token}"}

# ===========================
# 2. CREATE ACADEMIC SESSION
# ===========================
print("\n[2/7] Creating academic session (2024/2025)...")

session_response = requests.post(
    f"{BASE_URL}/sessions",
    headers=headers,
    json={
        "name": "2024/2025",
        "start_date": "2024-09-01",
        "end_date": "2025-07-31",
        "is_current": True
    }
)
if session_response.status_code == 201:
    session = session_response.json()
    session_id = session["id"]
    print(f"✓ Created session: {session['name']} (ID: {session_id})")
elif session_response.status_code == 500 and "already exists" in session_response.text:
    # Session already exists, retrieve it
    print(f"ℹ Session already exists, retrieving it...")
    list_response = requests.get(f"{BASE_URL}/sessions", headers=headers)
    if list_response.status_code == 200:
        sessions = list_response.json()
        session = next((s for s in sessions if s['name'] == '2024/2025'), None)
        if session:
            session_id = session["id"]
            print(f"✓ Using existing session: {session['name']} (ID: {session_id})")
        else:
            print(f"✗ Session exists but could not retrieve it")
            session_response.raise_for_status()
    else:
        print(f"✗ Error listing sessions: {list_response.status_code}")
        session_response.raise_for_status()
else:
    print(f"✗ Error creating session: {session_response.status_code}")
    print(f"  Response: {session_response.text}")
    session_response.raise_for_status()

# ===========================
# 3. CREATE TERM
# ===========================
print("\n[3/7] Creating first term...")

term_response = requests.post(
    f"{BASE_URL}/terms",
    headers=headers,
    json={
        "name": "First Term",
        "term_number": 1,
        "start_date": "2024-09-01",
        "end_date": "2024-11-30",
        "session_id": session_id,
        "is_current": True
    }
)
if term_response.status_code != 201:
    print(f"✗ Error creating term: {term_response.status_code}")
    print(f"  Response: {term_response.text}")
    term_response.raise_for_status()
term = term_response.json()
term_id = term["id"]
print(f"✓ Created term: {term['name']} (ID: {term_id})")

# ===========================
# 4. CREATE SUBJECT
# ===========================
print("\n[4/7] Creating subject (Mathematics)...")

subject_response = requests.post(
    f"{BASE_URL}/subjects",
    headers=headers,
    json={
        "code": "MTH",
        "name": "Mathematics",
        "description": "Core mathematics subject",
        "is_active": True
    }
)
if subject_response.status_code != 201:
    print(f"✗ Error creating subject: {subject_response.status_code}")
    print(f"  Response: {subject_response.text}")
    subject_response.raise_for_status()
subject = subject_response.json()
subject_id = subject["id"]
print(f"✓ Created subject: {subject['name']} (ID: {subject_id})")

# ===========================
# 5. CREATE CLASS
# ===========================
print("\n[5/7] Creating class (JSS1)...")

class_response = requests.post(
    f"{BASE_URL}/classes",
    headers=headers,
    json={
        "name": "Junior Secondary School 1",
        "level": "Junior",
        "section": "A",
        "capacity": 40,
        "session_id": session_id,
        "subject_ids": [subject_id] if 'subject_id' in locals() else []
    }
)
if class_response.status_code != 201:
    print(f"✗ Error creating class: {class_response.status_code}")
    print(f"  Response: {class_response.text}")
    class_response.raise_for_status()
class_obj = class_response.json()
class_id = class_obj["id"]
print(f"✓ Created class: {class_obj['name']} (ID: {class_id})")

# ===========================
# 6. CREATE STUDENT
# ===========================
print("\n[6/7] Creating student...")

student_response = requests.post(
    f"{BASE_URL}/students",
    headers=headers,
    json={
        "admission_number": "ADM/2024/001",
        "first_name": "Chioma",
        "last_name": "Okafor",
        "middle_name": "Blessing",
        "date_of_birth": "2009-05-15",
        "gender": "Female",
        "blood_group": "O+",
        "class_id": class_id,
        "session_id": session_id,
        "is_active": True
    }
)
if student_response.status_code != 201:
    print(f"✗ Error creating student: {student_response.status_code}")
    print(f"  Response: {student_response.text}")
    student_response.raise_for_status()
student = student_response.json()
student_id = student["id"]
print(f"✓ Created student: {student['first_name']} {student['last_name']} (ID: {student_id})")

# ===========================
# 7. CREATE TEACHER USER (for assignment)
# ===========================
print("\n[7/7] Creating teacher user account...")

import uuid
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
teacher_password = "Teacher123!@#"
teacher_id = str(uuid.uuid4())
password_hash = pwd_context.hash(teacher_password)

# Use Supabase client directly for user creation
from supabase import create_client
import os

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    teacher_user_data = {
        'id': teacher_id,
        'email': 'teacher@demohighschool.edu.ng',
        'password_hash': password_hash,
        'full_name': 'Mr. Kolade Adekunle',
        'role': 'teacher',
        'school_id': school_id,
        'is_active': True,
        'email_verified': True
    }
    
    teacher_result = supabase.table('users').insert(teacher_user_data).execute()
    if teacher_result.data:
        print(f"✓ Created teacher user: teacher@demohighschool.edu.ng")
        print(f"  Teacher ID: {teacher_id}")
        print(f"  Password: {teacher_password}")
    else:
        print(f"⚠ Could not create teacher user via Supabase")
else:
    print("⚠ Supabase credentials not available")

# ===========================
# SUMMARY
# ===========================
print("\n" + "=" * 70)
print("✓ SETUP COMPLETE")
print("=" * 70)
print(f"\nDemo Data Created:")
print(f"  • Academic Session: 2024/2025 ({session_id})")
print(f"  • First Term ({term_id})")
print(f"  • Subject: Mathematics ({subject_id})")
print(f"  • Class: JSS1 ({class_id})")
print(f"  • Student: Chioma Okafor ({student_id})")
print(f"  • Teacher User: teacher@demohighschool.edu.ng ({teacher_id})")
print(f"\nYou can now:")
print(f"  1. Create parent accounts")
print(f"  2. Link parents to students")
print(f"  3. Create teacher assignments")
print(f"  4. Mark attendance")
print(f"  5. Create assessments and grades")
print(f"  6. Generate report cards")
print("=" * 70)
