# Phase 4: Teacher Endpoints Documentation

## Overview
This document outlines endpoints available to teachers in Phase 4, with a focus on form teacher capabilities.

## Form Teacher vs Subject Teacher

### Form Teacher Capabilities
A **form teacher** has special responsibilities for their assigned class:
- ✅ Mark attendance for ALL students in the class
- ✅ View ALL grades for ALL subjects in the class
- ✅ Add remarks to ALL student report cards
- ✅ Send reports to parents
- ✅ Add students to the class (like admin)
- ✅ View complete class roster

### Subject Teacher Capabilities
A **subject teacher** can only:
- ✅ Enter grades for their own subject in assigned classes
- ✅ View students they teach
- ✅ Create assessments for their subject

---

## Teacher Endpoints

### 1. View My Classes
**GET** `/api/v1/teacher-management/teacher-assignments/teacher/{teacher_id}/classes?session_id={uuid}`

**Permission**: Teacher (own data), Admin

**Response**:
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
  },
  {
    "id": "class-uuid-2",
    "name": "SS2 Science",
    "level": "SS2",
    "section": "Science",
    "is_form_teacher": false,
    "subjects": [
      {"id": "uuid", "name": "Mathematics"}
    ]
  }
]
```

**Purpose**: Teacher sees all classes they teach, which subjects, and which class they are form teacher for.

---

### 2. View My Form Teacher Classes Only
**GET** `/api/v1/teacher-management/teacher-assignments?teacher_id={teacher_id}&is_form_teacher=true`

**Permission**: Teacher (own data), Admin

**Response**: Array of assignments where teacher is form teacher

**Purpose**: Quickly see which class(es) the teacher is responsible for as form teacher.

---

### 3. Add Remark to Student (Form Teacher Only)
**POST** `/api/v1/teacher-management/remarks`

**Permission**: Form teacher (own class), Admin

**Request Body**:
```json
{
  "student_id": "uuid",
  "class_id": "uuid",
  "session_id": "uuid",
  "term_id": "uuid",
  "remark_text": "John has shown excellent improvement in Mathematics this term.",
  "remarks_category": "form_teacher_comment"
}
```

**Authorization Check**:
- System verifies teacher is form teacher of the specified class
- Student must be enrolled in that class

**Purpose**: Form teacher adds personalized comments to student report cards.

---

### 4. View All Remarks for My Class (Form Teacher Only)
**GET** `/api/v1/teacher-management/remarks/class/{class_id}?session_id={uuid}&term_id={uuid}`

**Permission**: Form teacher (own class), Admin

**Response**: Array of remarks with student names and dates

**Purpose**: Form teacher reviews all remarks they've made for their class.

---

### 5. View Student's Remarks
**GET** `/api/v1/teacher-management/remarks/student/{student_id}?session_id={uuid}&term_id={uuid}`

**Permission**: Any teacher, Admin, Parent (own child)

**Response**: Array of remarks for the student

**Purpose**: View historical remarks for a specific student.

---

### 6. Update My Remark (Form Teacher Only)
**PUT** `/api/v1/teacher-management/remarks/{remark_id}`

**Permission**: Form teacher (own remark), Admin

**Request Body**:
```json
{
  "remark_text": "Updated comment...",
  "remarks_category": "form_teacher_comment"
}
```

**Authorization**: Teachers can only edit their own remarks.

---

### 7. Send Reports to Parents (Form Teacher Only)
**POST** `/api/v1/teacher-management/reports`

**Permission**: Form teacher (own class), Admin

**Request Body**:
```json
{
  "class_id": "uuid",
  "session_id": "uuid",
  "term_id": "uuid",
  "report_type": "end_of_term",
  "parent_ids": ["parent1-uuid", "parent2-uuid"]
}
```

**Authorization**: Only form teacher of the specified class can send reports.

**Purpose**: Send specific reports to selected parents.

---

### 8. Bulk Send Reports to All Parents (Form Teacher Only)
**POST** `/api/v1/teacher-management/reports/bulk-send`

**Permission**: Form teacher (own class), Admin

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

**Authorization**: Only form teacher of the class.

**Purpose**: Send reports to ALL parents of students in the class at once.

**Behavior**:
- System automatically finds all students in the class
- Gets all parent accounts linked to those students
- Creates report records for each parent
- Sets delivery status to "pending"

---

### 9. View Students in My Class (Form Teacher)
**GET** `/api/v1/classes/{class_id}/students`

**Permission**: Form teacher (own class), Subject teacher (assigned to class), Admin

**Response**: Array of students with enrollment details

**Purpose**: Form teacher views complete roster of students in their class.

---

### 10. Mark Attendance (Form Teacher Only)
**POST** `/api/v1/attendance/mark`

**Permission**: Form teacher (own class), Admin

**Request Body**:
```json
{
  "class_id": "uuid",
  "date": "2024-01-15",
  "term_id": "uuid",
  "attendance_records": [
    {
      "student_id": "uuid1",
      "status": "present"
    },
    {
      "student_id": "uuid2",
      "status": "absent",
      "reason": "sick"
    }
  ]
}
```

**Authorization**: Only form teacher of the class can mark attendance.

**Purpose**: Form teacher marks daily attendance for their class.

---

### 11. View Class Attendance (Form Teacher)
**GET** `/api/v1/attendance/class/{class_id}?term_id={uuid}&start_date={date}&end_date={date}`

**Permission**: Form teacher (own class), Admin

**Response**: Array of attendance records for the class

**Purpose**: Form teacher reviews attendance history for their class.

---

### 12. View All Grades for My Class (Form Teacher Only)
**GET** `/api/v1/grading/report-cards?class_id={class_id}&term_id={term_id}`

**Permission**: Form teacher (own class), Admin

**Response**: Array of report cards with all subjects and grades

**Purpose**: Form teacher sees comprehensive view of all students' performance across all subjects.

**Note**: This is different from subject teachers who can only see grades for their own subjects.

---

### 13. Enter Grades (Subject Teacher)
**POST** `/api/v1/grading/grades`

**Permission**: Subject teacher (assigned to class/subject), Admin

**Request Body**:
```json
{
  "student_id": "uuid",
  "subject_id": "uuid",
  "class_id": "uuid",
  "assessment_id": "uuid",
  "term_id": "uuid",
  "score": 85.5,
  "grading_scheme_component_id": "uuid"
}
```

**Authorization**: Teacher must be assigned to teach that subject in that class.

**Purpose**: Subject teacher enters grades for their subject only.

---

### 14. Create Assessment (Subject Teacher)
**POST** `/api/v1/grading/assessments`

**Permission**: Subject teacher (assigned subject/class), Admin

**Request Body**:
```json
{
  "class_id": "uuid",
  "subject_id": "uuid",
  "term_id": "uuid",
  "assessment_type_id": "uuid",
  "title": "Mid-Term Test",
  "max_score": 20.0,
  "date": "2024-01-20",
  "grading_scheme_component_id": "uuid"
}
```

**Authorization**: Teacher must teach that subject in that class.

**Purpose**: Subject teacher creates tests/exams for their subject.

---

### 15. View My Assignments
**GET** `/api/v1/teacher-management/teacher-assignments?teacher_id={teacher_id}`

**Permission**: Teacher (own data), Admin

**Response**: Array of all teacher's assignments (subject-class combinations)

**Purpose**: Teacher sees all their teaching assignments.

---

### 16. View Reports I've Sent
**GET** `/api/v1/teacher-management/reports?form_teacher_id={teacher_id}`

**Permission**: Teacher (own reports), Admin

**Response**: Array of reports sent by this form teacher

**Purpose**: Form teacher tracks which reports they've sent.

---

## Teacher Dashboard Data Requirements

### Form Teacher Dashboard Should Display:

1. **My Class Overview**
   - Class name, level, section
   - Total students enrolled
   - Current session/term

2. **Quick Stats**
   - Total students: `GET /classes/{id}/students`
   - Average attendance: `GET /attendance/class/{id}/summary`
   - Reports sent this term: `GET /reports?class_id={id}&term_id={term}`
   - Pending remarks: Count students without remarks

3. **Recent Activity**
   - Last attendance marked
   - Last report sent
   - Recent remarks added

4. **Action Items**
   - Students without remarks
   - Attendance not marked today
   - Reports pending to be sent

5. **Class Performance**
   - Subject-wise average grades
   - Top performers
   - Students needing attention

### Subject Teacher Dashboard Should Display:

1. **My Subjects & Classes**
   - List of classes taught
   - Subjects per class
   - Total students across all classes

2. **Assessments**
   - Upcoming assessments
   - Recently graded
   - Pending grade entry

3. **Grade Entry Status**
   - Students with missing grades
   - Assessment completion percentage

---

## Permission Enforcement

All teacher endpoints enforce these rules:

### Form Teacher Checks
```python
def require_form_teacher(teacher_id: str, class_id: str):
    # Query: teacher_class_assignments
    # WHERE teacher_id = {teacher_id}
    # AND class_id = {class_id}
    # AND is_form_teacher = true
    # IF no results: raise AuthorizationError
```

### Subject Teacher Checks
```python
def require_subject_teacher(teacher_id: str, subject_id: str, class_id: str):
    # Query: teacher_class_assignments
    # WHERE teacher_id = {teacher_id}
    # AND subject_id = {subject_id}
    # AND class_id = {class_id}
    # IF no results: raise AuthorizationError
```

### Admin Bypass
- System admins can perform all actions
- School admins can perform all actions for their organization

---

## Workflow Examples

### Example 1: Form Teacher Morning Routine
```bash
# 1. View my form teacher class
GET /teacher-management/teacher-assignments?teacher_id={me}&is_form_teacher=true

# 2. Get students in class
GET /classes/{class_id}/students

# 3. Mark attendance
POST /attendance/mark
{
  "class_id": "{class_id}",
  "date": "2024-01-15",
  "attendance_records": [...]
}
```

### Example 2: Form Teacher End-of-Term Report Distribution
```bash
# 1. View all class grades
GET /grading/report-cards?class_id={class_id}&term_id={term_id}

# 2. Add remarks for each student (loop)
POST /teacher-management/remarks
{
  "student_id": "{student_id}",
  "remark_text": "...",
  ...
}

# 3. Bulk send reports to all parents
POST /teacher-management/reports/bulk-send
{
  "class_id": "{class_id}",
  "include_all_parents": true,
  ...
}
```

### Example 3: Subject Teacher Grade Entry
```bash
# 1. View my teaching assignments
GET /teacher-management/teacher-assignments?teacher_id={me}

# 2. Select a class/subject to work on
# 3. Create assessment
POST /grading/assessments
{
  "class_id": "{class_id}",
  "subject_id": "{subject_id}",
  "title": "Test 1",
  ...
}

# 4. Enter grades for each student
POST /grading/grades
{
  "student_id": "{student_id}",
  "assessment_id": "{assessment_id}",
  "score": 85,
  ...
}
```

---

## Frontend Pages Needed

### For Form Teachers:
1. **My Form Class Dashboard** - Overview and stats
2. **Mark Attendance Page** - Daily attendance entry
3. **View Class Grades** - Comprehensive grade view across all subjects
4. **Add Remarks Page** - Form to add/edit student remarks
5. **Send Reports Page** - Select and send reports to parents
6. **Class Roster** - View/manage students in class

### For Subject Teachers:
1. **My Classes Dashboard** - All classes taught with subjects
2. **Create Assessment** - Create tests/exams for subjects
3. **Enter Grades** - Grade entry form
4. **View My Assessments** - List of assessments created

### For All Teachers:
1. **My Profile** - View assignments and basic info
2. **Reports Sent** - History of reports distributed

---

## Testing Checklist

### Form Teacher Tests
- [ ] Can mark attendance for own class
- [ ] Cannot mark attendance for other classes
- [ ] Can view all grades for own class
- [ ] Can add remarks to students in own class
- [ ] Cannot add remarks to students in other classes
- [ ] Can bulk send reports for own class
- [ ] Cannot send reports for other classes

### Subject Teacher Tests
- [ ] Can enter grades for assigned subject/class
- [ ] Cannot enter grades for unassigned subject/class
- [ ] Can create assessments for assigned subject/class
- [ ] Can view students in assigned classes
- [ ] Cannot access form teacher features

### Admin Tests
- [ ] Can perform all teacher actions
- [ ] Can view all teacher assignments
- [ ] Can reassign form teachers
- [ ] Can view all reports sent

---

## Security Notes

1. **Teacher ID Verification**: All teacher endpoints verify the authenticated user has a valid teacher_id
2. **Class Ownership**: Form teacher actions verify teacher is form teacher of the specific class
3. **Subject Assignment**: Grade entry verifies teacher teaches that subject in that class
4. **Session/Term Scope**: All queries are scoped to organization, session, and term
5. **Student Privacy**: Teachers can only view students in classes they teach

---

## Error Scenarios

### Common Errors Teachers May Encounter:

**403: Not Form Teacher**
```json
{
  "detail": "You are not the form teacher of this class"
}
```
**Solution**: Contact admin to verify form teacher assignment

**403: Not Assigned to Class**
```json
{
  "detail": "You do not teach Physics in this class"
}
```
**Solution**: Contact admin to verify teacher-subject-class assignment

**400: Validation Error**
```json
{
  "detail": "Student is not enrolled in this class"
}
```
**Solution**: Verify student enrollment before taking action

**404: Class Not Found**
```json
{
  "detail": "Class not found: {id}"
}
```
**Solution**: Verify class exists and you have access

---

## Next Steps

1. Create teacher frontend pages
2. Implement form teacher dashboard
3. Build grade entry interface for subject teachers
4. Add attendance marking UI for form teachers
5. Create report sending interface
6. Test with real teacher accounts
