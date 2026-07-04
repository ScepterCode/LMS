# Step 1: Database Schema Design - Teacher Class Feature

## Overview
Design database schema to support:
1. Form teachers per class
2. Teachers teaching multiple classes/subjects
3. Class-Subject relationships
4. Configurable grading schemes
5. Attendance tracking by form teacher
6. Remarks & reports functionality

---

## Current State
- ✅ `classes` table exists with `class_teacher_id` (form teacher support partial)
- ✅ `teachers` table exists
- ✅ `subject_assignments` table links teacher → subject → class → term
- ✅ `class_enrollments` links student → class → session
- ✅ `subjects` table exists
- ✅ `attendance` basics exist
- ✅ `grading` assessment types exist
- ❌ No Class-Subject relationship table
- ❌ No grading scheme configuration per school
- ❌ No form teacher distinction in subject_assignments
- ❌ No remarks/comments table
- ❌ No reports tracking table

---

## Proposed New/Modified Tables

### 1. **class_subjects** (NEW)
Links subjects to classes (many-to-many). Defines curriculum for a class.

```sql
CREATE TABLE class_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    is_mandatory BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(class_id, subject_id, session_id)
);
```

**Purpose**: When creating a class, admin selects all available subjects. Teachers are then assigned only to subjects offered in that class.

---

### 2. **grading_schemes** (NEW)
Configurable grading format per school/session (20-20-60, 20-20-20-40, etc.)

```sql
CREATE TABLE grading_schemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,  -- "20-20-60", "20-20-20-40"
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, session_id, name)
);
```

---

### 3. **grading_scheme_components** (NEW)
Define each component of a grading scheme.

```sql
CREATE TABLE grading_scheme_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grading_scheme_id UUID NOT NULL REFERENCES grading_schemes(id) ON DELETE CASCADE,
    component_type VARCHAR(50) NOT NULL,  -- 'test', 'coursework', 'exam', 'assignment'
    component_name VARCHAR(100) NOT NULL,  -- e.g., "Test 1", "Test 2", "Coursework", "Final Exam"
    weight_percentage DECIMAL(5,2) NOT NULL CHECK (weight_percentage > 0 AND weight_percentage <= 100),
    max_score DECIMAL(10,2) DEFAULT 100,
    required BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(grading_scheme_id, component_name)
);
```

**Purpose**: For scheme "20-20-60", components would be:
- Test 1: 20%
- Test 2: 20%
- Exam: 60%

---

### 4. **teacher_class_assignments** (MODIFIED/CLARIFIED)
Enhanced `subject_assignments` to explicitly track form teacher role.

```sql
-- Modify existing subject_assignments to add form_teacher flag OR create new table:
CREATE TABLE teacher_class_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id) ON DELETE CASCADE,
    is_form_teacher BOOLEAN DEFAULT false,  -- Only ONE form teacher per class
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(teacher_id, subject_id, class_id, term_id)
);

-- Constraint: Only ONE form teacher per class per session
CREATE UNIQUE INDEX idx_one_form_teacher_per_class 
ON teacher_class_assignments(class_id, session_id) 
WHERE is_form_teacher = true;
```

**Rationale**: Simplifies tracking—form teacher is just a flag on the assignment.

---

### 5. **student_remarks** (NEW)
Form teacher remarks/comments on student report cards.

```sql
CREATE TABLE student_remarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    form_teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    remark_text TEXT NOT NULL,
    remarks_category VARCHAR(50) DEFAULT 'general',  -- 'conduct', 'academic', 'general'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### 6. **school_reports** (NEW)
Track reports sent to parents by form teachers.

```sql
CREATE TABLE school_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL,  -- 'term_result', 'conduct', 'performance', 'special'
    form_teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE school_report_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES school_reports(id) ON DELETE CASCADE,
    parent_id UUID NOT NULL REFERENCES parents(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    delivery_status VARCHAR(20) DEFAULT 'pending'  -- 'pending', 'sent', 'delivered', 'read'
);
```

---

## Schema Relationship Diagram

```
organizations
├── academic_sessions
│   ├── grading_schemes
│   │   └── grading_scheme_components
│   └── terms
│       └── teacher_class_assignments
│
├── classes (has class_teacher_id → teachers.id)
│   ├── class_subjects → subjects (per session)
│   ├── student_remarks (form teacher comments)
│   └── teacher_class_assignments
│       ├── teacher_id → teachers
│       ├── subject_id → subjects
│       └── is_form_teacher flag
│
├── teachers
│   ├── teacher_class_assignments (multiple)
│   └── student_remarks (as form teacher)
│
├── students
│   ├── class_enrollments → classes
│   └── student_remarks
│
├── parents
│   └── school_report_recipients
│
└── school_reports
    ├── form_teacher_id → teachers
    └── school_report_recipients → parents + students
```

---

## Constraints & Business Rules

1. **One Form Teacher per Class**: 
   - Unique constraint on `(class_id, session_id)` WHERE `is_form_teacher = true`

2. **Form Teacher Permissions**:
   - Can only see students in their assigned class
   - Can only see all scores for students in their class
   - Only form teacher can add remarks to report card
   - Only form teacher can send reports to parents
   - Can mark attendance for students in their class

3. **Teacher Subject Assignment**:
   - Teacher can teach same subject to multiple classes
   - Teacher can teach multiple subjects to same class
   - Subject must exist in `class_subjects` before assigning teacher

4. **Grading Scheme**:
   - Per school, per session, one can be default
   - Components must sum to 100% or allow flexibility
   - If scheme changes, old grades remain valid

---

## Migration Strategy

1. **Phase 1**: Create new tables without constraints
2. **Phase 2**: Populate grading schemes from existing data
3. **Phase 3**: Migrate `class_teacher_id` to `teacher_class_assignments.is_form_teacher`
4. **Phase 4**: Add unique constraints & indices
5. **Phase 5**: Enable foreign keys

---

## Notes

- Grading scheme components are flexible (2 tests, 1 exam vs. 1 test, coursework, exam, etc.)
- Form teacher marked as flag on `teacher_class_assignments` for simplicity
- Class subjects tied to session to allow curriculum changes per year
- Reports table allows multiple report types (term results, conduct, performance, etc.)
