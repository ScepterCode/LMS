# Phase 4 Quick Start Guide

## Overview
This guide will help you quickly test the Phase 4 Teacher Management features.

## Prerequisites

### 1. Database Setup
Ensure Phase 4 schema is applied:
```bash
# Check if tables exist
python check_database.py
```

If Phase 4 tables don't exist, apply the schema:
```bash
# Apply Phase 4 schema
python -c "from database.migrate_phase4 import apply_phase4_schema; apply_phase4_schema()"
```

### 2. Start Backend Server
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Wait for:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 3. Verify Health Check
```bash
curl http://localhost:8000/api/v1/health
```

Should show:
```json
{
  "status": "healthy",
  "phase": "Phase 4 In Progress - Teacher Class Management",
  "endpoints": {
    ...
    "teacher_management": [...]
  }
}
```

---

## Testing Workflow

### Step 1: Login as School Admin

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@testschool.com",
    "password": "admin123"
  }'
```

**Save the token** from the response:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {...}
}
```

**Export token for convenience** (Linux/Mac):
```bash
export TOKEN="eyJhbGciOi..."
```

**Windows PowerShell**:
```powershell
$TOKEN = "eyJhbGciOi..."
```

---

### Step 2: Create a Grading Scheme

Create a 20-20-60 grading format (2 tests + final exam):

```bash
curl -X POST http://localhost:8000/api/v1/teacher-management/grading-schemes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "name": "20-20-60 Format",
    "description": "2 Tests (20% each) + Final Exam (60%)",
    "is_default": true,
    "components": [
      {
        "component_type": "test",
        "component_name": "Test 1",
        "weight_percentage": 20.0,
        "max_score": 20.0,
        "required": true,
        "display_order": 1
      },
      {
        "component_type": "test",
        "component_name": "Test 2",
        "weight_percentage": 20.0,
        "max_score": 20.0,
        "required": true,
        "display_order": 2
      },
      {
        "component_type": "exam",
        "component_name": "Final Exam",
        "weight_percentage": 60.0,
        "max_score": 60.0,
        "required": true,
        "display_order": 3
      }
    ]
  }'
```

**Expected Response**: 201 Created with scheme ID and components

---

### Step 3: List Grading Schemes

```bash
curl -X GET "http://localhost:8000/api/v1/teacher-management/grading-schemes" \
  -H "Authorization: Bearer $TOKEN"
```

Should see the scheme you just created.

---

### Step 4: Add Subjects to a Class

First, get your class and subject IDs:

```bash
# List classes
curl -X GET "http://localhost:8000/api/v1/classes" \
  -H "Authorization: Bearer $TOKEN"

# List subjects
curl -X GET "http://localhost:8000/api/v1/subjects" \
  -H "Authorization: Bearer $TOKEN"
```

Then add subjects to class curriculum:

```bash
# Add Mathematics to SS1 Science
curl -X POST "http://localhost:8000/api/v1/teacher-management/classes/CLASS_ID/subjects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "MATHS_SUBJECT_ID",
    "session_id": "YOUR_SESSION_ID",
    "is_mandatory": true,
    "display_order": 1
  }'

# Add Physics to SS1 Science
curl -X POST "http://localhost:8000/api/v1/teacher-management/classes/CLASS_ID/subjects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "PHYSICS_SUBJECT_ID",
    "session_id": "YOUR_SESSION_ID",
    "is_mandatory": true,
    "display_order": 2
  }'
```

---

### Step 5: Assign Teachers to Class/Subject

Get teacher IDs:
```bash
curl -X GET "http://localhost:8000/api/v1/teachers" \
  -H "Authorization: Bearer $TOKEN"
```

Create teacher assignment (make one form teacher):

```bash
# Assign Teacher John to teach Maths in SS1 Science (as form teacher)
curl -X POST "http://localhost:8000/api/v1/teacher-management/teacher-assignments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_id": "JOHN_TEACHER_ID",
    "class_id": "SS1_SCIENCE_CLASS_ID",
    "subject_id": "MATHS_SUBJECT_ID",
    "session_id": "YOUR_SESSION_ID",
    "term_id": "YOUR_TERM_ID",
    "is_form_teacher": true
  }'

# Assign same teacher to teach Physics in SS1 Science (NOT form teacher)
curl -X POST "http://localhost:8000/api/v1/teacher-management/teacher-assignments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_id": "JOHN_TEACHER_ID",
    "class_id": "SS1_SCIENCE_CLASS_ID",
    "subject_id": "PHYSICS_SUBJECT_ID",
    "session_id": "YOUR_SESSION_ID",
    "term_id": "YOUR_TERM_ID",
    "is_form_teacher": false
  }'
```

---

### Step 6: View Teacher's Classes

```bash
curl -X GET "http://localhost:8000/api/v1/teacher-management/teacher-assignments/teacher/JOHN_TEACHER_ID/classes" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected**: Should show SS1 Science with both Maths and Physics subjects, and `is_form_teacher: true`

---

### Step 7: Add Student Remark (Form Teacher)

Login as the teacher or use admin token:

```bash
curl -X POST "http://localhost:8000/api/v1/teacher-management/remarks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STUDENT_ID",
    "class_id": "SS1_SCIENCE_CLASS_ID",
    "session_id": "YOUR_SESSION_ID",
    "term_id": "YOUR_TERM_ID",
    "remark_text": "Excellent performance this term. Keep up the good work!",
    "remarks_category": "form_teacher_comment"
  }'
```

---

### Step 8: View Class Remarks

```bash
curl -X GET "http://localhost:8000/api/v1/teacher-management/remarks/class/SS1_SCIENCE_CLASS_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Should see all remarks for students in that class.

---

### Step 9: Send Reports to Parents

Get parent IDs:
```bash
curl -X GET "http://localhost:8000/api/v1/parents" \
  -H "Authorization: Bearer $TOKEN"
```

Send report to specific parents:
```bash
curl -X POST "http://localhost:8000/api/v1/teacher-management/reports" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "class_id": "SS1_SCIENCE_CLASS_ID",
    "session_id": "YOUR_SESSION_ID",
    "term_id": "YOUR_TERM_ID",
    "report_type": "end_of_term",
    "parent_ids": ["PARENT1_ID", "PARENT2_ID"]
  }'
```

Or bulk send to all parents:
```bash
curl -X POST "http://localhost:8000/api/v1/teacher-management/reports/bulk-send" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "class_id": "SS1_SCIENCE_CLASS_ID",
    "session_id": "YOUR_SESSION_ID",
    "term_id": "YOUR_TERM_ID",
    "report_type": "end_of_term",
    "include_all_parents": true
  }'
```

---

### Step 10: List All Reports Sent

```bash
curl -X GET "http://localhost:8000/api/v1/teacher-management/reports?class_id=SS1_SCIENCE_CLASS_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Common Issues and Solutions

### Issue 1: "User must belong to a school"
**Cause**: User account doesn't have `school_id` set
**Solution**: Update user record to include organization_id

### Issue 2: "Not authenticated"
**Cause**: Token expired or invalid
**Solution**: Login again to get new token

### Issue 3: "Only administrators can perform this action"
**Cause**: Using teacher token for admin-only endpoint
**Solution**: Use admin account token

### Issue 4: "You are not the form teacher of this class"
**Cause**: Teacher trying to access form-teacher-only feature but isn't assigned as form teacher
**Solution**: Admin needs to create assignment with `is_form_teacher: true`

### Issue 5: "This class already has a form teacher for this session"
**Cause**: Trying to assign second form teacher to same class
**Solution**: Remove existing form teacher assignment first, or update existing one

---

## Testing Checklist

### Admin Features
- [ ] Create grading scheme with components
- [ ] List grading schemes
- [ ] Update grading scheme
- [ ] Delete grading scheme
- [ ] Add subject to class curriculum
- [ ] List class subjects
- [ ] Remove subject from class
- [ ] Create teacher assignment (regular)
- [ ] Create teacher assignment (form teacher)
- [ ] List teacher assignments
- [ ] Update teacher assignment
- [ ] Delete teacher assignment
- [ ] View teacher's classes
- [ ] List all form teachers

### Form Teacher Features
- [ ] Add remark to student in own class
- [ ] View all remarks for own class
- [ ] Update own remark
- [ ] Delete own remark
- [ ] Send reports to specific parents
- [ ] Bulk send reports to all parents
- [ ] View reports sent

### Permission Tests
- [ ] Admin can create grading schemes
- [ ] Teacher cannot create grading schemes
- [ ] Form teacher can add remarks to own class
- [ ] Form teacher cannot add remarks to other classes
- [ ] Subject teacher cannot access form teacher features
- [ ] Form teacher can send reports for own class
- [ ] Form teacher cannot send reports for other classes

### Edge Cases
- [ ] Prevent duplicate grading scheme names
- [ ] Prevent multiple form teachers per class
- [ ] Prevent assigning non-existent teacher/class/subject
- [ ] Prevent adding remark for student not in class
- [ ] Handle empty parent list gracefully
- [ ] Validate grading component weights sum to 100

---

## Next Steps After Testing

Once all endpoints are tested and working:

1. **Fix any bugs** found during testing
2. **Document API** with Swagger/OpenAPI
3. **Create frontend pages** for:
   - Admin: Grading scheme management
   - Admin: Class subject configuration
   - Admin: Teacher assignment interface
   - Form Teacher: Dashboard
   - Form Teacher: Remarks page
   - Form Teacher: Send reports page
   - Subject Teacher: Grade entry

4. **Integration work**:
   - Update attendance endpoints with form teacher checks
   - Update grading endpoints with subject teacher checks
   - Update class creation to include subject selection

5. **Write automated tests**

---

## Useful Endpoints for Testing

### Get IDs You'll Need

```bash
# Get organization ID
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# Get session ID
curl -X GET "http://localhost:8000/api/v1/sessions" \
  -H "Authorization: Bearer $TOKEN"

# Get term ID
curl -X GET "http://localhost:8000/api/v1/terms" \
  -H "Authorization: Bearer $TOKEN"

# Get class IDs
curl -X GET "http://localhost:8000/api/v1/classes" \
  -H "Authorization: Bearer $TOKEN"

# Get subject IDs
curl -X GET "http://localhost:8000/api/v1/subjects" \
  -H "Authorization: Bearer $TOKEN"

# Get teacher IDs
curl -X GET "http://localhost:8000/api/v1/teachers" \
  -H "Authorization: Bearer $TOKEN"

# Get student IDs
curl -X GET "http://localhost:8000/api/v1/students" \
  -H "Authorization: Bearer $TOKEN"

# Get parent IDs
curl -X GET "http://localhost:8000/api/v1/parents" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Sample Test Data

### Grading Scheme Examples

**20-20-60 Format** (2 Tests + Exam):
```json
{
  "components": [
    {"component_type": "test", "component_name": "Test 1", "weight_percentage": 20, "max_score": 20, "required": true, "display_order": 1},
    {"component_type": "test", "component_name": "Test 2", "weight_percentage": 20, "max_score": 20, "required": true, "display_order": 2},
    {"component_type": "exam", "component_name": "Final Exam", "weight_percentage": 60, "max_score": 60, "required": true, "display_order": 3}
  ]
}
```

**20-20-20-40 Format** (2 Tests + Coursework + Exam):
```json
{
  "components": [
    {"component_type": "test", "component_name": "Test 1", "weight_percentage": 20, "max_score": 20, "required": true, "display_order": 1},
    {"component_type": "test", "component_name": "Test 2", "weight_percentage": 20, "max_score": 20, "required": true, "display_order": 2},
    {"component_type": "coursework", "component_name": "Coursework", "weight_percentage": 20, "max_score": 20, "required": true, "display_order": 3},
    {"component_type": "exam", "component_name": "Final Exam", "weight_percentage": 40, "max_score": 40, "required": true, "display_order": 4}
  ]
}
```

**10-10-10-10-60 Format** (4 Tests + Exam):
```json
{
  "components": [
    {"component_type": "test", "component_name": "Test 1", "weight_percentage": 10, "max_score": 10, "required": true, "display_order": 1},
    {"component_type": "test", "component_name": "Test 2", "weight_percentage": 10, "max_score": 10, "required": true, "display_order": 2},
    {"component_type": "test", "component_name": "Test 3", "weight_percentage": 10, "max_score": 10, "required": true, "display_order": 3},
    {"component_type": "test", "component_name": "Test 4", "weight_percentage": 10, "max_score": 10, "required": true, "display_order": 4},
    {"component_type": "exam", "component_name": "Final Exam", "weight_percentage": 60, "max_score": 60, "required": true, "display_order": 5}
  ]
}
```

---

## Documentation Links

- **Admin Endpoints**: `backend/PHASE4_ADMIN_ENDPOINTS.md`
- **Teacher Endpoints**: `backend/PHASE4_TEACHER_ENDPOINTS.md`
- **Backend Complete**: `PHASE4_BACKEND_COMPLETE.md`
- **Assessment**: `PHASE4_TEACHER_CLASS_ASSESSMENT.md`
- **Database Schema**: `database/phase4_complete_schema.sql`

---

## Support

If you encounter issues:
1. Check backend logs for errors
2. Verify database tables exist
3. Ensure authentication token is valid
4. Verify IDs (class, teacher, student, etc.) exist in database
5. Check endpoint documentation for correct request format

---

**Status**: Ready for Testing
**Date**: June 20, 2026
