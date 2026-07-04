"""
Comprehensive Test Suite for Phase 2 - All Features
Tests all medium and low priority features
"""

import requests
import json
from datetime import datetime, date

BASE_URL = "http://localhost:8000/api/v1"

# Global variables
access_token = None
organization_id = None
teacher_id = None
student_id = None
session_id = None
term_id = None
class_id = None
subject_id = None
guardian_id = None

def print_test(name):
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {name}")
    print('='*60)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def login():
    """Login and get access token"""
    global access_token, organization_id
    
    print_test("Login")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": "admin@demohighschool.edu.ng",
            "password": "DemoSchool123!@#"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        access_token = data['access_token']
        organization_id = data['user']['organization_id']
        print_success(f"Logged in as {data['user']['full_name']}")
        print_success(f"Organization ID: {organization_id}")
        return True
    else:
        print_error(f"Login failed: {response.text}")
        return False

def get_headers():
    """Get authorization headers"""
    return {"Authorization": f"Bearer {access_token}"}

def test_academic_sessions():
    """Test creating academic sessions"""
    global session_id
    
    print_test("Academic Sessions - Create Session")
    
    session_data = {
        "name": "2024/2025",
        "start_date": "2024-09-01",
        "end_date": "2025-08-31",
        "is_current": True
    }
    
    response = requests.post(
        f"{BASE_URL}/sessions",
        json=session_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        session_id = data['id']
        print_success(f"Created session: {data['name']} (ID: {session_id})")
        return True
    else:
        print_error(f"Failed to create session: {response.text}")
        return False

def test_terms():
    """Test creating terms"""
    global term_id
    
    print_test("Terms - Create Term")
    
    term_data = {
        "session_id": session_id,
        "name": "1st Term",
        "term_number": 1,
        "start_date": "2024-09-01",
        "end_date": "2024-12-20",
        "is_current": True
    }
    
    response = requests.post(
        f"{BASE_URL}/terms",
        json=term_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        term_id = data['id']
        print_success(f"Created term: {data['name']} (ID: {term_id})")
        return True
    else:
        print_error(f"Failed to create term: {response.text}")
        return False

def test_classes():
    """Test creating classes"""
    global class_id
    
    print_test("Classes - Create Class")
    
    class_data = {
        "name": "JSS 1",
        "level": "Junior",
        "section": "A",
        "capacity": 40
    }
    
    response = requests.post(
        f"{BASE_URL}/classes",
        json=class_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        class_id = data['id']
        print_success(f"Created class: {data['name']} (ID: {class_id})")
        print_success(f"Capacity: {data['capacity']}")
        return True
    else:
        print_error(f"Failed to create class: {response.text}")
        return False

def test_subjects():
    """Test creating subjects"""
    global subject_id
    
    print_test("Subjects - Create Subject")
    
    subject_data = {
        "name": "Mathematics",
        "code": "MATH101",
        "subject_type": "core",
        "description": "Basic mathematics"
    }
    
    response = requests.post(
        f"{BASE_URL}/subjects",
        json=subject_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        subject_id = data['id']
        print_success(f"Created subject: {data['name']} (ID: {subject_id})")
        print_success(f"Type: {data['subject_type']}")
        return True
    else:
        print_error(f"Failed to create subject: {response.text}")
        return False

def test_teacher_creation():
    """Test creating a teacher"""
    global teacher_id
    
    print_test("Teachers - Create Teacher")
    
    # First create a user account for the teacher
    user_data = {
        "email": "teacher.john@demohighschool.edu.ng",
        "password": "Teacher123!@#",
        "full_name": "John Teacher",
        "role": "teacher"
    }
    
    user_response = requests.post(
        f"{BASE_URL}/system-admin/users",
        json=user_data,
        headers=get_headers()
    )
    
    if user_response.status_code != 200:
        print_error(f"Failed to create user: {user_response.text}")
        return False
    
    user_id = user_response.json()['id']
    print_success(f"Created user account (ID: {user_id})")
    
    # Now create teacher profile
    teacher_data = {
        "user_id": user_id,
        "staff_number": "TCH/2024/001",
        "first_name": "John",
        "middle_name": "Paul",
        "last_name": "Teacher",
        "date_of_birth": "1985-05-15",
        "gender": "Male",
        "email": "teacher.john@demohighschool.edu.ng",
        "phone": "+234 803 111 2222",
        "address": "123 Teacher Street, Lagos",
        "state_of_origin": "Lagos",
        "lga": "Ikeja",
        "nationality": "Nigerian",
        "qualification": "B.Ed Mathematics",
        "specialization": "Mathematics",
        "employment_date": "2024-01-15",
        "employment_type": "full-time",
        "status": "active"
    }
    
    response = requests.post(
        f"{BASE_URL}/teachers",
        json=teacher_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        teacher_id = data['id']
        print_success(f"Created teacher: {data['first_name']} {data['last_name']}")
        print_success(f"Staff Number: {data['staff_number']}")
        print_success(f"Qualification: {data['qualification']}")
        return True
    else:
        print_error(f"Failed to create teacher: {response.text}")
        return False

def test_teacher_detail():
    """Test viewing teacher details"""
    print_test("Teachers - Get Teacher Detail")
    
    response = requests.get(
        f"{BASE_URL}/teachers/{teacher_id}",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Retrieved teacher: {data['first_name']} {data['last_name']}")
        print_success(f"Email: {data['email']}")
        print_success(f"Years of Service: {data.get('years_of_service', 0)}")
        print_success(f"Subject Count: {data.get('subject_count', 0)}")
        return True
    else:
        print_error(f"Failed to get teacher: {response.text}")
        return False

def test_teacher_update():
    """Test updating teacher"""
    print_test("Teachers - Update Teacher")
    
    update_data = {
        "qualification": "M.Ed Mathematics",
        "specialization": "Advanced Mathematics",
        "status": "active"
    }
    
    response = requests.put(
        f"{BASE_URL}/teachers/{teacher_id}",
        json=update_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Updated teacher qualification to: {data['qualification']}")
        return True
    else:
        print_error(f"Failed to update teacher: {response.text}")
        return False

def test_student_creation():
    """Test creating a student"""
    global student_id
    
    print_test("Students - Create Student")
    
    student_data = {
        "admission_number": "2024/001",
        "first_name": "Alice",
        "middle_name": "Grace",
        "last_name": "Johnson",
        "date_of_birth": "2010-03-15",
        "gender": "Female",
        "blood_group": "O+",
        "email": "alice.johnson@student.com",
        "phone": "+234 803 222 3333",
        "address": "456 Student Avenue, Lagos",
        "state_of_origin": "Lagos",
        "lga": "Ikeja",
        "nationality": "Nigerian",
        "religion": "Christianity",
        "current_class_id": class_id,
        "admission_date": "2024-09-01",
        "status": "active"
    }
    
    response = requests.post(
        f"{BASE_URL}/students",
        json=student_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        student_id = data['id']
        print_success(f"Created student: {data['full_name']}")
        print_success(f"Admission Number: {data['admission_number']}")
        print_success(f"Age: {data.get('age', 'N/A')}")
        return True
    else:
        print_error(f"Failed to create student: {response.text}")
        return False

def test_guardian_creation():
    """Test adding guardian to student"""
    global guardian_id
    
    print_test("Guardians - Add Guardian")
    
    guardian_data = {
        "guardian_type": "father",
        "title": "Mr",
        "first_name": "Robert",
        "last_name": "Johnson",
        "relationship": "Father",
        "phone": "+234 803 444 5555",
        "email": "robert.johnson@email.com",
        "occupation": "Engineer",
        "address": "456 Student Avenue, Lagos",
        "is_emergency_contact": True,
        "is_primary": True
    }
    
    response = requests.post(
        f"{BASE_URL}/students/{student_id}/guardians",
        json=guardian_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        guardian_id = data['id']
        print_success(f"Added guardian: {data['full_name']}")
        print_success(f"Relationship: {data['relationship']}")
        print_success(f"Primary: {data['is_primary']}")
        print_success(f"Emergency Contact: {data['is_emergency_contact']}")
        return True
    else:
        print_error(f"Failed to add guardian: {response.text}")
        return False

def test_guardian_update():
    """Test updating guardian"""
    print_test("Guardians - Update Guardian")
    
    update_data = {
        "occupation": "Senior Engineer",
        "email": "robert.johnson.new@email.com"
    }
    
    response = requests.put(
        f"{BASE_URL}/students/{student_id}/guardians/{guardian_id}",
        json=update_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Updated guardian occupation to: {data['occupation']}")
        print_success(f"Updated email to: {data['email']}")
        return True
    else:
        print_error(f"Failed to update guardian: {response.text}")
        return False

def test_subject_assignment():
    """Test assigning teacher to subject"""
    print_test("Assignments - Assign Teacher to Subject")
    
    assignment_data = {
        "teacher_id": teacher_id,
        "subject_id": subject_id,
        "class_id": class_id,
        "session_id": session_id,
        "term_id": term_id
    }
    
    response = requests.post(
        f"{BASE_URL}/assignments/subject",
        json=assignment_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Assigned teacher to subject successfully")
        print_success(f"Subject: {data.get('subject_name', 'N/A')}")
        print_success(f"Class: {data.get('class_name', 'N/A')}")
        print_success(f"Term: {data.get('term_name', 'N/A')}")
        return True
    else:
        print_error(f"Failed to assign teacher: {response.text}")
        return False

def test_teacher_assignments():
    """Test viewing teacher's assignments"""
    print_test("Assignments - Get Teacher Assignments")
    
    response = requests.get(
        f"{BASE_URL}/teachers/{teacher_id}/assignments",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Retrieved {len(data)} assignment(s)")
        for assignment in data:
            print_success(f"  - {assignment.get('subject_name')} in {assignment.get('class_name')}")
        return True
    else:
        print_error(f"Failed to get assignments: {response.text}")
        return False

def test_class_enrollment():
    """Test enrolling student in class"""
    print_test("Enrollments - Enroll Student in Class")
    
    enrollment_data = {
        "student_id": student_id,
        "class_id": class_id,
        "session_id": session_id
    }
    
    response = requests.post(
        f"{BASE_URL}/assignments/class-enrollment",
        json=enrollment_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Enrolled student in class successfully")
        print_success(f"Status: {data.get('status', 'N/A')}")
        return True
    else:
        print_error(f"Failed to enroll student: {response.text}")
        return False

def test_class_students():
    """Test viewing students in class"""
    print_test("Enrollments - Get Class Students")
    
    response = requests.get(
        f"{BASE_URL}/classes/{class_id}/students",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Class has {len(data)} student(s)")
        for student in data:
            print_success(f"  - {student.get('full_name', 'N/A')} ({student.get('admission_number', 'N/A')})")
        return True
    else:
        print_error(f"Failed to get class students: {response.text}")
        return False

def test_list_operations():
    """Test list operations with enriched data"""
    print_test("List Operations - Teachers with Counts")
    
    response = requests.get(
        f"{BASE_URL}/teachers",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Retrieved {len(data)} teacher(s)")
        for teacher in data:
            print_success(f"  - {teacher.get('first_name')} {teacher.get('last_name')}")
            print_success(f"    Subjects: {teacher.get('subject_count', 0)}, Years: {teacher.get('years_of_service', 0)}")
        return True
    else:
        print_error(f"Failed to list teachers: {response.text}")
        return False

def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "="*60)
    print("🚀 STARTING COMPREHENSIVE TEST SUITE")
    print("   Testing All Medium & Low Priority Features")
    print("="*60)
    
    tests = [
        ("Login", login),
        ("Academic Sessions", test_academic_sessions),
        ("Terms", test_terms),
        ("Classes", test_classes),
        ("Subjects", test_subjects),
        ("Teacher Creation", test_teacher_creation),
        ("Teacher Detail", test_teacher_detail),
        ("Teacher Update", test_teacher_update),
        ("Student Creation", test_student_creation),
        ("Guardian Creation", test_guardian_creation),
        ("Guardian Update", test_guardian_update),
        ("Subject Assignment", test_subject_assignment),
        ("Teacher Assignments", test_teacher_assignments),
        ("Class Enrollment", test_class_enrollment),
        ("Class Students", test_class_students),
        ("List Operations", test_list_operations),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_error(f"Test crashed: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! System is 100% functional!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the output above.")

if __name__ == "__main__":
    run_all_tests()
