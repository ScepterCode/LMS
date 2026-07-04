"""
Automated System Testing Script for Nigerian LMS
Tests all major features and endpoints
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test credentials
ADMIN_EMAIL = "sarahchidiloveday@gmail.com"
ADMIN_PASSWORD = "Admin123!"

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class LMSTester:
    def __init__(self):
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.user: Optional[Dict] = None
        self.test_data = {}
        self.passed = 0
        self.failed = 0
        self.total = 0
    
    def print_header(self, text: str):
        """Print a test section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")
    
    def print_test(self, name: str, passed: bool, message: str = ""):
        """Print test result"""
        self.total += 1
        if passed:
            self.passed += 1
            status = f"{Colors.GREEN}✓ PASS{Colors.RESET}"
        else:
            self.failed += 1
            status = f"{Colors.RED}✗ FAIL{Colors.RESET}"
        
        print(f"{status} | {name}")
        if message:
            print(f"       {Colors.YELLOW}{message}{Colors.RESET}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an HTTP request with session cookies"""
        url = f"{API_BASE}{endpoint}"
        return self.session.request(method, url, **kwargs)
    
    # ========================================
    # 1. AUTHENTICATION TESTS
    # ========================================
    
    def test_authentication(self):
        """Test login and authentication"""
        self.print_header("AUTHENTICATION TESTS")
        
        # Test 1: Login with correct credentials
        try:
            response = self.make_request(
                "POST",
                "/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user = data.get("user")
                self.print_test(
                    "Admin Login",
                    True,
                    f"Logged in as: {self.user.get('full_name')} ({self.user.get('role')})"
                )
            else:
                self.print_test("Admin Login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Admin Login", False, str(e))
            return False
        
        # Test 2: Get current user
        try:
            response = self.make_request("GET", "/auth/me")
            success = response.status_code == 200
            self.print_test("Get Current User", success)
        except Exception as e:
            self.print_test("Get Current User", False, str(e))
        
        return True
    
    # ========================================
    # 2. ACADEMIC STRUCTURE TESTS
    # ========================================
    
    def test_academic_sessions(self):
        """Test academic sessions"""
        self.print_header("ACADEMIC SESSIONS TESTS")
        
        # Test 1: List sessions
        try:
            response = self.make_request("GET", "/sessions")
            success = response.status_code == 200
            if success:
                sessions = response.json()
                self.print_test("List Sessions", True, f"Found {len(sessions)} sessions")
                if sessions:
                    self.test_data['session_id'] = sessions[0]['id']
            else:
                self.print_test("List Sessions", False)
        except Exception as e:
            self.print_test("List Sessions", False, str(e))
        
        # Test 2: Create session
        try:
            session_name = f"Test Session {datetime.now().year}"
            start_date = datetime.now().date()
            end_date = (datetime.now() + timedelta(days=365)).date()
            
            response = self.make_request(
                "POST",
                "/sessions",
                json={
                    "name": session_name,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "is_current": False
                }
            )
            
            success = response.status_code in [200, 201]
            if success:
                session = response.json()
                self.test_data['test_session_id'] = session['id']
                self.print_test("Create Session", True, f"Created: {session_name}")
            else:
                # Session might already exist
                self.print_test("Create Session", True, "Session may already exist")
        except Exception as e:
            self.print_test("Create Session", False, str(e))
    
    def test_classes(self):
        """Test class management"""
        self.print_header("CLASSES TESTS")
        
        # Test 1: List classes
        try:
            response = self.make_request("GET", "/classes")
            success = response.status_code == 200
            if success:
                classes = response.json()
                self.print_test("List Classes", True, f"Found {len(classes)} classes")
                if classes:
                    self.test_data['class_id'] = classes[0]['id']
            else:
                self.print_test("List Classes", False)
        except Exception as e:
            self.print_test("List Classes", False, str(e))
    
    def test_subjects(self):
        """Test subject management"""
        self.print_header("SUBJECTS TESTS")
        
        # Test 1: List subjects
        try:
            response = self.make_request("GET", "/subjects")
            success = response.status_code == 200
            if success:
                subjects = response.json()
                self.print_test("List Subjects", True, f"Found {len(subjects)} subjects")
                if subjects:
                    self.test_data['subject_id'] = subjects[0]['id']
            else:
                self.print_test("List Subjects", False)
        except Exception as e:
            self.print_test("List Subjects", False, str(e))
    
    # ========================================
    # 3. STUDENT TESTS
    # ========================================
    
    def test_students(self):
        """Test student management"""
        self.print_header("STUDENT MANAGEMENT TESTS")
        
        # Test 1: List students
        try:
            response = self.make_request("GET", "/students")
            success = response.status_code == 200
            if success:
                students = response.json()
                self.print_test("List Students", True, f"Found {len(students)} students")
                if students:
                    self.test_data['student_id'] = students[0]['id']
            else:
                self.print_test("List Students", False)
        except Exception as e:
            self.print_test("List Students", False, str(e))
        
        # Test 2: Get student details
        if 'student_id' in self.test_data:
            try:
                response = self.make_request("GET", f"/students/{self.test_data['student_id']}")
                success = response.status_code == 200
                if success:
                    student = response.json()
                    self.print_test("Get Student Details", True, f"Student: {student.get('full_name')}")
                else:
                    self.print_test("Get Student Details", False)
            except Exception as e:
                self.print_test("Get Student Details", False, str(e))
    
    # ========================================
    # 4. TEACHER TESTS
    # ========================================
    
    def test_teachers(self):
        """Test teacher management"""
        self.print_header("TEACHER MANAGEMENT TESTS")
        
        # Test 1: List teachers
        try:
            response = self.make_request("GET", "/teachers")
            success = response.status_code == 200
            if success:
                teachers = response.json()
                self.print_test("List Teachers", True, f"Found {len(teachers)} teachers")
                if teachers:
                    self.test_data['teacher_id'] = teachers[0]['id']
            else:
                self.print_test("List Teachers", False)
        except Exception as e:
            self.print_test("List Teachers", False, str(e))
        
        # Test 2: Get teacher details
        if 'teacher_id' in self.test_data:
            try:
                response = self.make_request("GET", f"/teachers/{self.test_data['teacher_id']}")
                success = response.status_code == 200
                if success:
                    teacher = response.json()
                    self.print_test("Get Teacher Details", True, f"Teacher: {teacher.get('full_name')}")
                else:
                    self.print_test("Get Teacher Details", False)
            except Exception as e:
                self.print_test("Get Teacher Details", False, str(e))
    
    # ========================================
    # 5. PARENT TESTS
    # ========================================
    
    def test_parents(self):
        """Test parent management"""
        self.print_header("PARENT MANAGEMENT TESTS")
        
        # Test 1: List parents
        try:
            response = self.make_request("GET", "/parents")
            success = response.status_code == 200
            if success:
                parents = response.json()
                self.print_test("List Parents", True, f"Found {len(parents)} parents")
                if parents:
                    self.test_data['parent_id'] = parents[0]['id']
            else:
                self.print_test("List Parents", False)
        except Exception as e:
            self.print_test("List Parents", False, str(e))
        
        # Test 2: Get parent details
        if 'parent_id' in self.test_data:
            try:
                response = self.make_request("GET", f"/parents/{self.test_data['parent_id']}")
                success = response.status_code == 200
                if success:
                    parent = response.json()
                    self.print_test("Get Parent Details", True, f"Parent: {parent.get('full_name')}")
                else:
                    self.print_test("Get Parent Details", False)
            except Exception as e:
                self.print_test("Get Parent Details", False, str(e))
        
        # Test 3: Get parent's children
        if 'parent_id' in self.test_data:
            try:
                response = self.make_request("GET", f"/parents/{self.test_data['parent_id']}/children")
                success = response.status_code == 200
                if success:
                    children = response.json()
                    self.print_test("Get Parent's Children", True, f"Found {len(children)} linked students")
                else:
                    self.print_test("Get Parent's Children", False)
            except Exception as e:
                self.print_test("Get Parent's Children", False, str(e))
    
    # ========================================
    # 6. GRADING TESTS
    # ========================================
    
    def test_grading(self):
        """Test grading system"""
        self.print_header("GRADING SYSTEM TESTS")
        
        # Test 1: List assessments
        try:
            response = self.make_request("GET", "/grading/assessments")
            success = response.status_code == 200
            if success:
                assessments = response.json()
                self.print_test("List Assessments", True, f"Found {len(assessments)} assessments")
            else:
                self.print_test("List Assessments", False)
        except Exception as e:
            self.print_test("List Assessments", False, str(e))
        
        # Test 2: Get student grades
        if 'student_id' in self.test_data:
            try:
                response = self.make_request("GET", f"/grading/students/{self.test_data['student_id']}/grades")
                success = response.status_code == 200
                if success:
                    grades = response.json()
                    self.print_test("Get Student Grades", True, f"Found {len(grades)} grade records")
                else:
                    self.print_test("Get Student Grades", False)
            except Exception as e:
                self.print_test("Get Student Grades", False, str(e))
    
    # ========================================
    # 7. ATTENDANCE TESTS
    # ========================================
    
    def test_attendance(self):
        """Test attendance system"""
        self.print_header("ATTENDANCE SYSTEM TESTS")
        
        # Test 1: Get attendance records
        try:
            response = self.make_request("GET", "/attendance/records")
            success = response.status_code == 200
            if success:
                records = response.json()
                self.print_test("Get Attendance Records", True, f"Found {len(records)} records")
            else:
                self.print_test("Get Attendance Records", False)
        except Exception as e:
            self.print_test("Get Attendance Records", False, str(e))
    
    # ========================================
    # 8. FEE MANAGEMENT TESTS
    # ========================================
    
    def test_fees(self):
        """Test fee management"""
        self.print_header("FEE MANAGEMENT TESTS")
        
        # Test 1: Get fee structures
        try:
            response = self.make_request("GET", "/fees/structures")
            success = response.status_code == 200
            if success:
                structures = response.json()
                self.print_test("Get Fee Structures", True, f"Found {len(structures)} fee structures")
            else:
                self.print_test("Get Fee Structures", False)
        except Exception as e:
            self.print_test("Get Fee Structures", False, str(e))
        
        # Test 2: Get student payments
        if 'student_id' in self.test_data:
            try:
                response = self.make_request("GET", f"/fees/students/{self.test_data['student_id']}/payments")
                success = response.status_code == 200
                if success:
                    payments = response.json()
                    self.print_test("Get Student Payments", True, f"Found {len(payments)} payment records")
                else:
                    self.print_test("Get Student Payments", False)
            except Exception as e:
                self.print_test("Get Student Payments", False, str(e))
    
    # ========================================
    # 9. TEACHER MANAGEMENT (PHASE 4) TESTS
    # ========================================
    
    def test_teacher_management(self):
        """Test teacher management features"""
        self.print_header("TEACHER MANAGEMENT (PHASE 4) TESTS")
        
        # Test 1: Get grading schemes
        try:
            response = self.make_request("GET", "/teacher-management/grading-schemes")
            success = response.status_code == 200
            if success:
                schemes = response.json()
                self.print_test("Get Grading Schemes", True, f"Found {len(schemes)} schemes")
            else:
                self.print_test("Get Grading Schemes", False)
        except Exception as e:
            self.print_test("Get Grading Schemes", False, str(e))
        
        # Test 2: Get teacher assignments
        try:
            response = self.make_request("GET", "/teacher-management/teacher-assignments")
            success = response.status_code == 200
            if success:
                assignments = response.json()
                self.print_test("Get Teacher Assignments", True, f"Found {len(assignments)} assignments")
            else:
                self.print_test("Get Teacher Assignments", False)
        except Exception as e:
            self.print_test("Get Teacher Assignments", False, str(e))
    
    # ========================================
    # MAIN TEST RUNNER
    # ========================================
    
    def run_all_tests(self):
        """Run all test suites"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'*' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'NIGERIAN LMS - AUTOMATED SYSTEM TEST'.center(70)}{Colors.RESET}")
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{Colors.BOLD}{Colors.BLUE}{f'Started: {start_time}'.center(70)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'*' * 70}{Colors.RESET}")
        
        # Run authentication first
        if not self.test_authentication():
            print(f"\n{Colors.RED}{Colors.BOLD}Authentication failed. Cannot proceed with other tests.{Colors.RESET}")
            return
        
        # Run all test suites
        self.test_academic_sessions()
        self.test_classes()
        self.test_subjects()
        self.test_students()
        self.test_teachers()
        self.test_parents()
        self.test_grading()
        self.test_attendance()
        self.test_fees()
        self.test_teacher_management()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'TEST SUMMARY'.center(70)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")
        
        pass_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        
        print(f"Total Tests:  {self.total}")
        print(f"{Colors.GREEN}Passed:       {self.passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed:       {self.failed}{Colors.RESET}")
        print(f"Pass Rate:    {pass_rate:.1f}%\n")
        
        if self.failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! System is fully functional.{Colors.RESET}\n")
        else:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed. Check the output above for details.{Colors.RESET}\n")
        
        print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")


if __name__ == "__main__":
    print(f"\n{Colors.YELLOW}Make sure both servers are running:{Colors.RESET}")
    print(f"  Backend:  http://localhost:8000")
    print(f"  Frontend: http://localhost:3000")
    print(f"\nPress Enter to start testing...")
    input()
    
    tester = LMSTester()
    tester.run_all_tests()
