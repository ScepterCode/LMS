# Phase 4: Admin Endpoints Documentation

## Overview
This document outlines all Phase 4 backend API endpoints for school administrators to manage teacher-class features, grading schemes, and curriculum.

## Base URL
All endpoints are prefixed with: `/api/v1/teacher-management`

---

## 1. GRADING SCHEMES

### Create Grading Scheme
**POST** `/grading-schemes`

**Permission**: Admin only

**Request Body**:
```json
{
  "session_id": "uuid",
  "name": "20-20-60 Format",
  "description": "2 Tests, Coursework, Final Exam",
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
}
```

**Response**: GradingSchemeResponse with components

**Purpose**: Create configurable grading formats (20-20-60, 20-20-20-40, etc.) that define how grades are calculated.

---

### List Grading Schemes
**GET** `/grading-schemes?session_id={uuid}&is_active={bool}`

**Permission**: All authenticated users

**Response**: Array of GradingSchemeResponse

---

### Get Grading Scheme
**GET** `/grading-schemes/{scheme_id}`

**Permission**: All authenticated users

**Response**: GradingSchemeResponse with components

---

### Update Grading Scheme
**PUT** `/grading-schemes/{scheme_id}`

**Permission**: Admin only

**Request Body**: Partial GradingSchemeUpdate

---

### Delete Grading Scheme
**DELETE** `/grading-schemes/{scheme_id}`

**Permission**: Admin only

**Note**: Cascades to delete all components

---

### Set Default Grading Scheme
When creating or updating a scheme with `is_default: true`, all other schemes for that session are automatically unmarked as default.

---

## 2. CLASS SUBJECTS (Curriculum)

### Add Subject to Class
**POST** `/classes/{class_id}/subjects`

**Permission**: Admin only

**Request Body**:
```json
{
  "subject_id": "uuid",
  "session_id": "uuid",
  "is_mandatory": true,
  "display_order": 1
}
```

**Response**: ClassSubjectResponse

**Purpose**: Define which subjects are offered in a class. When creating a class, admin selects all subjects that students in that class can offer.

---

### List Class Subjects
**GET** `/classes/{class_id}/subjects?session_id={uuid}`

**Permission**: All authenticated users

**Response**: Array of ClassSubjectResponse with subject names

**Purpose**: View the curriculum (all subjects) for a specific class.

---

### Remove Subject from Class
**DELETE** `/classes/{class_id}/subjects/{subject_id}?session_id={uuid}`

**Permission**: Admin only

**Purpose**: Remove a subject from class curriculum.

---

## 3. TEACHER CLASS ASSIGNMENTS

### Create Teacher Assignment
**POST** `/teacher-assignments`

**Permission**: Admin only

**Request Body**:
```json
{
  "teacher_id": "uuid",
  "class_id": "uuid",
  "subject_id": "uuid",
  "session_id": "uuid",
  "term_id": "uuid",  // optional
  "is_form_teacher": false
}
```

**Response**: TeacherClassAssignmentResponse

**Purpose**: 
- Assign a teacher to teach a specific subject in a specific class
- Optionally designate teacher as form teacher for that class
- A teacher can teach multiple subjects to multiple classes
- Example: Teacher John can teach both Maths and Physics to SS1, SS2, SS3

**Rules**:
- A class can only have ONE form teacher per session
- A teacher can be form teacher of only ONE class per session
- A teacher can teach unlimited subject-class combinations

---

### List Teacher Assignments
**GET** `/teacher-assignments?teacher_id={uuid}&class_id={uuid}&session_id={uuid}&is_form_teacher={bool}`

**Permission**: All authenticated users

**Response**: Array of TeacherClassAssignmentResponse with enriched names

**Purpose**: View all teacher assignments with filters.

---

### Get Teacher Assignment
**GET** `/teacher-assignments/{assignment_id}`

**Permission**: All authenticated users

**Response**: TeacherClassAssignmentResponse

---

### Update Teacher Assignment
**PUT** `/teacher-assignments/{assignment_id}`

**Permission**: Admin only

**Request Body**: TeacherClassAssignmentUpdate (partial)

**Purpose**: Change form teacher status, update term, etc.

**Validation**: Prevents setting multiple form teachers for same class/session.

---

### Delete Teacher Assignment
**DELETE** `/teacher-assignments/{assignment_id}`

**Permission**: Admin only

**Purpose**: Remove teacher from teaching a subject in a class.

---

### Get Teacher's Classes
**GET** `/teacher-assignments/teacher/{teacher_id}/classes?session_id={uuid}`

**Permission**: All authenticated users

**Response**: Array of classes with subjects taught

**Purpose**: View all classes a teacher is assigned to, grouped by class with subjects listed.

**Example Response**:
```json
[
  {
    "id": "class-uuid",
    "name": "SS1 Science",
    "level": "SS1",
    "section": "Science",
    "is_form_teacher": true,
    "subjects": [
      {"id": "uuid", "name": "Mathematics"},
      {"id": "uuid", "name": "Physics"}
    ]
  }
]
```

---

### List All Form Teachers
**GET** `/form-teachers?session_id={uuid}`

**Permission**: All authenticated users

**Response**: Array of form teacher assignments

**Purpose**: Get a list of all form teachers with their assigned classes.

---

## 4. STUDENT REMARKS

### Create Student Remark
**POST** `/remarks`

**Permission**: Form teacher or admin

**Request Body**:
```json
{
  "student_id": "uuid",
  "class_id": "uuid",
  "session_id": "uuid",
  "term_id": "uuid",
  "remark_text": "Excellent performance. Keep it up!",
  "remarks_category": "form_teacher_comment"
}
```

**Response**: StudentRemarkResponse

**Purpose**: Form teacher adds comments/remarks to student report cards.

**Authorization**:
- Teachers must be the form teacher of the class
- Admins can add remarks on behalf of form teacher

---

### Get Student Remarks
**GET** `/remarks/student/{student_id}?session_id={uuid}&term_id={uuid}`

**Permission**: All authenticated users

**Response**: Array of StudentRemarkResponse

**Purpose**: View all remarks for a specific student.

---

### Get Class Remarks
**GET** `/remarks/class/{class_id}?session_id={uuid}&term_id={uuid}`

**Permission**: Form teacher or admin

**Response**: Array of StudentRemarkResponse for all students in class

**Purpose**: Form teacher views all remarks they've made for their class.

---

### Update Student Remark
**PUT** `/remarks/{remark_id}`

**Permission**: Form teacher (own remarks) or admin

**Request Body**: StudentRemarkUpdate (partial)

---

### Delete Student Remark
**DELETE** `/remarks/{remark_id}`

**Permission**: Form teacher (own remarks) or admin

---

## 5. SCHOOL REPORTS

### Create School Report
**POST** `/reports`

**Permission**: Form teacher or admin

**Request Body**:
```json
{
  "class_id": "uuid",
  "session_id": "uuid",
  "term_id": "uuid",
  "report_type": "mid_term",
  "parent_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Response**: SchoolReportResponse with recipients

**Purpose**: Form teacher sends reports to specific parent accounts.

**Report Types**:
- `mid_term`
- `end_of_term`
- `annual`
- `progress_report`
- `custom`

---

### Bulk Send Reports
**POST** `/reports/bulk-send`

**Permission**: Form teacher or admin

**Request Body**:
```json
{
  "class_id": "uuid",
  "session_id": "uuid",
  "term_id": "uuid",
  "report_type": "end_of_term",
  "include_all_parents": true
}
```

**Response**: SchoolReportResponse

**Purpose**: Send reports to ALL parents of students in the class at once.

**Authorization**: Only form teacher of the class can bulk send.

---

### List School Reports
**GET** `/reports?class_id={uuid}&session_id={uuid}&term_id={uuid}&report_type={type}`

**Permission**: All authenticated users

**Response**: Array of SchoolReportResponse with recipient counts

---

### Get School Report
**GET** `/reports/{report_id}`

**Permission**: All authenticated users

**Response**: SchoolReportResponse with full recipient details

---

## Permission Matrix

| Action | Admin | Form Teacher | Subject Teacher | Parent |
|--------|-------|--------------|-----------------|--------|
| Create grading scheme | ✅ | ❌ | ❌ | ❌ |
| Add subject to class | ✅ | ❌ | ❌ | ❌ |
| Assign teacher to class/subject | ✅ | ❌ | ❌ | ❌ |
| Set form teacher | ✅ | ❌ | ❌ | ❌ |
| Add student remark | ✅ | ✅ (own class) | ❌ | ❌ |
| Send reports to parents | ✅ | ✅ (own class) | ❌ | ❌ |
| Mark attendance | ✅ | ✅ (own class) | ❌ | ❌ |
| View class grades | ✅ | ✅ (own class) | ❌ | ❌ |
| Enter subject grades | ✅ | ✅ | ✅ (assigned subject/class) | ❌ |

---

## Workflow Examples

### Example 1: Setting Up a New Class
1. **Admin creates class**: `POST /classes` (existing endpoint)
2. **Admin adds subjects to class**: `POST /classes/{id}/subjects` (multiple calls for each subject)
3. **Admin assigns teachers**: 
   - `POST /teacher-assignments` for each teacher-subject-class combination
   - One assignment has `is_form_teacher: true`
4. **Admin enrolls students**: `POST /assignments/enrollment` (existing endpoint)

### Example 2: Multi-Subject Teacher Assignment
Teacher "John Smith" teaches Maths and Physics to SS1, SS2, SS3:
- 6 total assignments (2 subjects × 3 classes)
- Make him form teacher of SS1 Science only

```json
POST /teacher-assignments (6 calls)
[
  { "teacher_id": "john", "class_id": "ss1-science", "subject_id": "maths", "is_form_teacher": true },
  { "teacher_id": "john", "class_id": "ss1-science", "subject_id": "physics", "is_form_teacher": false },
  { "teacher_id": "john", "class_id": "ss2-science", "subject_id": "maths", "is_form_teacher": false },
  { "teacher_id": "john", "class_id": "ss2-science", "subject_id": "physics", "is_form_teacher": false },
  { "teacher_id": "john", "class_id": "ss3-science", "subject_id": "maths", "is_form_teacher": false },
  { "teacher_id": "john", "class_id": "ss3-science", "subject_id": "physics", "is_form_teacher": false }
]
```

### Example 3: Form Teacher End-of-Term Workflow
1. **View class students**: `GET /classes/{id}/students`
2. **View class grades**: `GET /grading/report-cards?class_id={id}&term_id={term}`
3. **Add remarks**: `POST /remarks` for each student
4. **Send reports**: `POST /reports/bulk-send` with `include_all_parents: true`

---

## Error Handling

All endpoints return standard error responses:

**400 Bad Request**: Validation errors
```json
{
  "detail": "Validation error message"
}
```

**401 Unauthorized**: Not authenticated
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden**: Insufficient permissions
```json
{
  "detail": "Only administrators can perform this action"
}
```

**404 Not Found**: Resource doesn't exist
```json
{
  "detail": "Teacher not found: {id}"
}
```

**409 Conflict**: Duplicate or constraint violation
```json
{
  "detail": "This class already has a form teacher for this session"
}
```

**500 Internal Server Error**: Database or server issues
```json
{
  "detail": "Failed to create teacher assignment: {error}"
}
```

---

## Testing the Endpoints

### Prerequisites
1. Backend server running: `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. Authentication token obtained from `/api/v1/auth/login`
3. School admin account

### Test Sequence
```bash
# 1. Create grading scheme
curl -X POST http://localhost:8000/api/v1/teacher-management/grading-schemes \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 2. Add subjects to class
curl -X POST http://localhost:8000/api/v1/teacher-management/classes/{class_id}/subjects \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 3. Assign teachers
curl -X POST http://localhost:8000/api/v1/teacher-management/teacher-assignments \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 4. View teacher's classes
curl -X GET "http://localhost:8000/api/v1/teacher-management/teacher-assignments/teacher/{teacher_id}/classes" \
  -H "Authorization: Bearer {token}"
```

---

## Next Steps

1. ✅ Backend endpoints implemented
2. ⏳ Test all endpoints with actual database
3. ⏳ Create frontend admin pages
4. ⏳ Create frontend form teacher dashboard
5. ⏳ Integrate with existing grading/attendance systems

---

## Database Tables Used

- `grading_schemes` - Stores grading formats
- `grading_scheme_components` - Stores components (tests, exams, etc.)
- `class_subjects` - Defines curriculum for each class
- `teacher_class_assignments` - Teacher-subject-class assignments
- `student_remarks` - Form teacher comments
- `school_reports` - Report metadata
- `school_report_recipients` - Parent recipients for reports

All tables were created in Phase 4 schema migrations.
