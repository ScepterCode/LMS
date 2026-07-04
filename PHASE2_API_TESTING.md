# 🧪 Phase 2 API Testing Guide

## **Base URL**
```
http://127.0.0.1:8000/api/v1
```

## **Authentication**
All endpoints require authentication. Use the login endpoint to get a token:

```bash
POST /auth/login
{
  "email": "admin@demohighschool.edu.ng",
  "password": "DemoSchool123!@#"
}
```

The token is set in an HttpOnly cookie automatically.

---

## 📅 **Academic Sessions API**

### Create Session
```bash
POST /sessions
{
  "name": "2024/2025",
  "start_date": "2024-09-01",
  "end_date": "2025-07-31",
  "is_current": true
}
```

### List Sessions
```bash
GET /sessions
GET /sessions?is_current=true
```

### Get Session
```bash
GET /sessions/{session_id}
```

### Update Session
```bash
PUT /sessions/{session_id}
{
  "name": "2024/2025 Updated"
}
```

### Set as Current
```bash
POST /sessions/{session_id}/set-current
```

---

## 🏫 **Classes API**

### Create Class
```bash
POST /classes
{
  "name": "JSS 1A",
  "level": "Junior",
  "section": "A",
  "capacity": 40
}
```

### List Classes
```bash
GET /classes
GET /classes?level=Junior
```

### Get Class with Students
```bash
GET /classes/{class_id}
GET /classes/{class_id}/students
```

---

## 📚 **Subjects API**

### Create Subject
```bash
POST /subjects
{
  "name": "Mathematics",
  "code": "MATH101",
  "subject_type": "core",
  "description": "Basic mathematics for JSS 1"
}
```

### List Subjects
```bash
GET /subjects
GET /subjects?subject_type=core
```

---

## 👨‍🎓 **Students API**

### Register Student
```bash
POST /students
{
  "admission_number": "2024/001",
  "first_name": "Chioma",
  "middle_name": "Grace",
  "last_name": "Okafor",
  "date_of_birth": "2010-05-15",
  "gender": "Female",
  "blood_group": "O+",
  "email": "chioma.okafor@student.demo.ng",
  "phone": "+234 803 111 2222",
  "address": "45 Lagos Street, Lagos",
  "state_of_origin": "Lagos",
  "lga": "Ikeja",
  "nationality": "Nigerian",
  "religion": "Christianity",
  "current_class_id": "{class_id}",
  "admission_date": "2024-09-01"
}
```

### List Students
```bash
GET /students
GET /students?class_id={class_id}
GET /students?status=active
GET /students?search=Chioma
GET /students?skip=0&limit=20
```

### Get Student
```bash
GET /students/{student_id}
```

### Update Student
```bash
PUT /students/{student_id}
{
  "current_class_id": "{new_class_id}",
  "phone": "+234 803 111 3333"
}
```

### Delete Student
```bash
DELETE /students/{student_id}
```

---

## 👨‍👩‍👧 **Guardian Management**

### Add Guardian
```bash
POST /students/{student_id}/guardians
{
  "guardian_type": "father",
  "title": "Mr",
  "first_name": "Emeka",
  "last_name": "Okafor",
  "relationship": "Father",
  "phone": "+234 803 444 5555",
  "email": "emeka.okafor@email.com",
  "occupation": "Engineer",
  "address": "45 Lagos Street, Lagos",
  "is_emergency_contact": true,
  "is_primary": true
}
```

### List Guardians
```bash
GET /students/{student_id}/guardians
```

### Update Guardian
```bash
PUT /students/{student_id}/guardians/{guardian_id}
{
  "phone": "+234 803 444 6666",
  "is_primary": true
}
```

### Delete Guardian
```bash
DELETE /students/{student_id}/guardians/{guardian_id}
```

---

## 🧪 **Testing Workflow**

### 1. Setup Academic Structure
```bash
# 1. Create Academic Session
POST /sessions
{
  "name": "2024/2025",
  "start_date": "2024-09-01",
  "end_date": "2025-07-31",
  "is_current": true
}

# 2. Create Classes
POST /classes
{ "name": "JSS 1A", "level": "Junior", "section": "A", "capacity": 40 }

POST /classes
{ "name": "JSS 2B", "level": "Junior", "section": "B", "capacity": 35 }

# 3. Create Subjects
POST /subjects
{ "name": "Mathematics", "code": "MATH101", "subject_type": "core" }

POST /subjects
{ "name": "English Language", "code": "ENG101", "subject_type": "core" }

POST /subjects
{ "name": "Biology", "code": "BIO101", "subject_type": "core" }
```

### 2. Register Students
```bash
# Student 1
POST /students
{
  "admission_number": "2024/001",
  "first_name": "Chioma",
  "last_name": "Okafor",
  "date_of_birth": "2010-05-15",
  "gender": "Female",
  "current_class_id": "{jss1a_class_id}"
}

# Student 2
POST /students
{
  "admission_number": "2024/002",
  "first_name": "Oluwaseun",
  "last_name": "Adeyemi",
  "date_of_birth": "2009-08-20",
  "gender": "Male",
  "current_class_id": "{jss2b_class_id}"
}
```

### 3. Add Guardians
```bash
# Add father for Student 1
POST /students/{student1_id}/guardians
{
  "guardian_type": "father",
  "first_name": "Emeka",
  "last_name": "Okafor",
  "relationship": "Father",
  "phone": "+234 803 111 2222",
  "is_primary": true
}

# Add mother for Student 1
POST /students/{student1_id}/guardians
{
  "guardian_type": "mother",
  "first_name": "Ada",
  "last_name": "Okafor",
  "relationship": "Mother",
  "phone": "+234 803 333 4444",
  "is_primary": false
}
```

### 4. Query and Verify
```bash
# List all students
GET /students

# Search for student
GET /students?search=Chioma

# Get students in a class
GET /classes/{class_id}/students

# Get student with guardians
GET /students/{student_id}
GET /students/{student_id}/guardians
```

---

## 🔍 **Response Examples**

### Student Response
```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "admission_number": "2024/001",
  "first_name": "Chioma",
  "middle_name": "Grace",
  "last_name": "Okafor",
  "full_name": "Chioma Grace Okafor",
  "date_of_birth": "2010-05-15",
  "age": 14,
  "gender": "Female",
  "blood_group": "O+",
  "email": "chioma.okafor@student.demo.ng",
  "phone": "+234 803 111 2222",
  "current_class_id": "uuid",
  "class_name": "JSS 1A",
  "status": "active",
  "created_at": "2024-06-05T20:00:00",
  "updated_at": "2024-06-05T20:00:00"
}
```

### Guardian Response
```json
{
  "id": "uuid",
  "student_id": "uuid",
  "guardian_type": "father",
  "title": "Mr",
  "first_name": "Emeka",
  "last_name": "Okafor",
  "full_name": "Mr Emeka Okafor",
  "relationship": "Father",
  "phone": "+234 803 444 5555",
  "email": "emeka.okafor@email.com",
  "occupation": "Engineer",
  "is_emergency_contact": true,
  "is_primary": true,
  "created_at": "2024-06-05T20:00:00"
}
```

---

## ✅ **Validation Rules**

### Students
- Admission number must be unique per school
- Age must be between 2 and 25 years
- Gender must be: Male, Female, or Other
- Date of birth is required

### Guardians
- At least one guardian per student (recommended)
- Only one guardian can be primary
- Guardian type: father, mother, guardian, other
- Phone number is required

### Classes
- Level must be: Primary, Junior, or Senior
- Capacity must be between 1 and 200

### Subjects
- Subject code must be unique per school
- Subject type: core or elective

---

## 🐛 **Error Responses**

### 404 Not Found
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Student with ID xxx not found",
    "status_code": 404
  }
}
```

### 400 Validation Error
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid class ID",
    "status_code": 400
  }
}
```

### 409 Duplicate
```json
{
  "error": {
    "code": "DUPLICATE_RECORD",
    "message": "Student with admission_number '2024/001' already exists",
    "status_code": 409
  }
}
```

---

## 🚀 **Next Steps**

After testing these APIs:
1. Test with Postman or curl
2. Verify data in Supabase dashboard
3. Check relationships between entities
4. Test filtering and search
5. Move to frontend development

Happy Testing! 🎉
