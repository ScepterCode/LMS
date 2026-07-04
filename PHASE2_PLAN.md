# 🚀 PHASE 2: CORE SCHOOL MANAGEMENT

## **OBJECTIVES**
Build complete student and teacher management with class structure, academic sessions, and role-based portals.

## **DEVELOPMENT STRATEGY**
Given the scope of Phase 2, we'll implement in focused increments:

### **Phase 2A: Foundation (Days 1-3)**
- Database schema for students, teachers, classes, subjects
- Academic sessions and terms
- Backend APIs for CRUD operations
- Basic frontend pages

### **Phase 2B: Portals & Assignment (Days 4-6)**
- Teacher portal and dashboard
- Student portal and dashboard
- Class and subject assignments
- Student-class mapping

### **Phase 2C: Enhanced Features (Days 7-9)**
- Parent accounts and portal
- Timetable system
- Enhanced user management
- Campus management

### **Phase 2D: Polish & Integration (Days 10-12)**
- Reports and analytics
- Notifications system
- Settings and configuration
- Testing and documentation

---

## **PHASE 2A: DATABASE SCHEMA**

### **New Tables**

#### **1. academic_sessions**
```sql
id UUID PRIMARY KEY
organization_id UUID REFERENCES organizations(id)
name VARCHAR NOT NULL  -- "2024/2025"
start_date DATE NOT NULL
end_date DATE NOT NULL
is_current BOOLEAN DEFAULT false
created_at TIMESTAMP DEFAULT NOW()
```

#### **2. terms**
```sql
id UUID PRIMARY KEY
session_id UUID REFERENCES academic_sessions(id)
name VARCHAR NOT NULL  -- "1st Term", "2nd Term", "3rd Term"
term_number INTEGER NOT NULL  -- 1, 2, 3
start_date DATE NOT NULL
end_date DATE NOT NULL
is_current BOOLEAN DEFAULT false
created_at TIMESTAMP DEFAULT NOW()
```

#### **3. classes**
```sql
id UUID PRIMARY KEY
organization_id UUID REFERENCES organizations(id)
name VARCHAR NOT NULL  -- "JSS 1", "SS 2"
level VARCHAR NOT NULL  -- "Junior", "Senior"
section VARCHAR  -- "A", "B", "C"
capacity INTEGER DEFAULT 40
class_teacher_id UUID REFERENCES users(id)
created_at TIMESTAMP DEFAULT NOW()
```

#### **4. subjects**
```sql
id UUID PRIMARY KEY
organization_id UUID REFERENCES organizations(id)
name VARCHAR NOT NULL  -- "Mathematics", "English"
code VARCHAR  -- "MATH101"
subject_type VARCHAR DEFAULT 'core'  -- 'core', 'elective'
description TEXT
created_at TIMESTAMP DEFAULT NOW()
```

#### **5. students**
```sql
id UUID PRIMARY KEY
organization_id UUID REFERENCES organizations(id)
admission_number VARCHAR UNIQUE NOT NULL
first_name VARCHAR NOT NULL
middle_name VARCHAR
last_name VARCHAR NOT NULL
date_of_birth DATE NOT NULL
gender VARCHAR NOT NULL
blood_group VARCHAR
email VARCHAR
phone VARCHAR
address TEXT
state_of_origin VARCHAR
lga VARCHAR
nationality VARCHAR DEFAULT 'Nigerian'
religion VARCHAR
photo_url VARCHAR
medical_conditions TEXT
allergies TEXT
current_class_id UUID REFERENCES classes(id)
admission_date DATE DEFAULT CURRENT_DATE
status VARCHAR DEFAULT 'active'  -- 'active', 'graduated', 'suspended', 'withdrawn'
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP DEFAULT NOW()
```

#### **6. student_guardians**
```sql
id UUID PRIMARY KEY
student_id UUID REFERENCES students(id)
guardian_type VARCHAR NOT NULL  -- 'father', 'mother', 'guardian'
title VARCHAR  -- 'Mr', 'Mrs', 'Dr'
first_name VARCHAR NOT NULL
last_name VARCHAR NOT NULL
relationship VARCHAR  -- 'Father', 'Mother', 'Uncle', etc.
phone VARCHAR NOT NULL
email VARCHAR
occupation VARCHAR
address TEXT
is_emergency_contact BOOLEAN DEFAULT true
is_primary BOOLEAN DEFAULT false
created_at TIMESTAMP DEFAULT NOW()
```

#### **7. teachers**
```sql
id UUID PRIMARY KEY
user_id UUID REFERENCES users(id) UNIQUE NOT NULL
organization_id UUID REFERENCES organizations(id)
staff_number VARCHAR UNIQUE NOT NULL
first_name VARCHAR NOT NULL
middle_name VARCHAR
last_name VARCHAR NOT NULL
date_of_birth DATE
gender VARCHAR NOT NULL
email VARCHAR NOT NULL
phone VARCHAR NOT NULL
address TEXT
state_of_origin VARCHAR
lga VARCHAR
nationality VARCHAR DEFAULT 'Nigerian'
photo_url VARCHAR
qualification VARCHAR  -- "B.Ed", "M.Ed", etc.
specialization VARCHAR  -- "Mathematics", "Physics"
employment_date DATE DEFAULT CURRENT_DATE
employment_type VARCHAR DEFAULT 'full-time'  -- 'full-time', 'part-time', 'contract'
status VARCHAR DEFAULT 'active'  -- 'active', 'on-leave', 'terminated'
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP DEFAULT NOW()
```

#### **8. subject_assignments**
```sql
id UUID PRIMARY KEY
teacher_id UUID REFERENCES teachers(id)
subject_id UUID REFERENCES subjects(id)
class_id UUID REFERENCES classes(id)
session_id UUID REFERENCES academic_sessions(id)
term_id UUID REFERENCES terms(id)
created_at TIMESTAMP DEFAULT NOW()
UNIQUE(teacher_id, subject_id, class_id, term_id)
```

#### **9. class_enrollments**
```sql
id UUID PRIMARY KEY
student_id UUID REFERENCES students(id)
class_id UUID REFERENCES classes(id)
session_id UUID REFERENCES academic_sessions(id)
enrollment_date DATE DEFAULT CURRENT_DATE
status VARCHAR DEFAULT 'active'  -- 'active', 'promoted', 'repeated'
created_at TIMESTAMP DEFAULT NOW()
UNIQUE(student_id, session_id)
```

#### **10. parents**
```sql
id UUID PRIMARY KEY
user_id UUID REFERENCES users(id) UNIQUE NOT NULL
organization_id UUID REFERENCES organizations(id)
title VARCHAR  -- 'Mr', 'Mrs', 'Dr'
first_name VARCHAR NOT NULL
last_name VARCHAR NOT NULL
phone VARCHAR NOT NULL
email VARCHAR NOT NULL
occupation VARCHAR
address TEXT
created_at TIMESTAMP DEFAULT NOW()
```

#### **11. parent_student_links**
```sql
id UUID PRIMARY KEY
parent_id UUID REFERENCES parents(id)
student_id UUID REFERENCES students(id)
relationship VARCHAR NOT NULL  -- 'Father', 'Mother', 'Guardian'
is_primary BOOLEAN DEFAULT false
created_at TIMESTAMP DEFAULT NOW()
UNIQUE(parent_id, student_id)
```

---

## **PHASE 2A: API ENDPOINTS**

### **Academic Sessions**
- `GET /api/v1/sessions` - List all sessions for school
- `POST /api/v1/sessions` - Create new session
- `GET /api/v1/sessions/{id}` - Get session details
- `PUT /api/v1/sessions/{id}` - Update session
- `DELETE /api/v1/sessions/{id}` - Delete session
- `POST /api/v1/sessions/{id}/set-current` - Set as current session

### **Terms**
- `GET /api/v1/terms` - List terms for session
- `POST /api/v1/terms` - Create new term
- `GET /api/v1/terms/{id}` - Get term details
- `PUT /api/v1/terms/{id}` - Update term
- `DELETE /api/v1/terms/{id}` - Delete term
- `POST /api/v1/terms/{id}/set-current` - Set as current term

### **Classes**
- `GET /api/v1/classes` - List all classes
- `POST /api/v1/classes` - Create new class
- `GET /api/v1/classes/{id}` - Get class details
- `PUT /api/v1/classes/{id}` - Update class
- `DELETE /api/v1/classes/{id}` - Delete class
- `GET /api/v1/classes/{id}/students` - List students in class

### **Subjects**
- `GET /api/v1/subjects` - List all subjects
- `POST /api/v1/subjects` - Create new subject
- `GET /api/v1/subjects/{id}` - Get subject details
- `PUT /api/v1/subjects/{id}` - Update subject
- `DELETE /api/v1/subjects/{id}` - Delete subject

### **Students**
- `GET /api/v1/students` - List all students (with filters)
- `POST /api/v1/students` - Register new student
- `GET /api/v1/students/{id}` - Get student details
- `PUT /api/v1/students/{id}` - Update student
- `DELETE /api/v1/students/{id}` - Delete student
- `POST /api/v1/students/{id}/upload-photo` - Upload student photo
- `GET /api/v1/students/{id}/guardians` - List student guardians
- `POST /api/v1/students/{id}/guardians` - Add guardian
- `PUT /api/v1/students/{id}/guardians/{guardian_id}` - Update guardian
- `DELETE /api/v1/students/{id}/guardians/{guardian_id}` - Remove guardian

### **Teachers**
- `GET /api/v1/teachers` - List all teachers
- `POST /api/v1/teachers` - Register new teacher
- `GET /api/v1/teachers/{id}` - Get teacher details
- `PUT /api/v1/teachers/{id}` - Update teacher
- `DELETE /api/v1/teachers/{id}` - Delete teacher
- `POST /api/v1/teachers/{id}/upload-photo` - Upload teacher photo
- `GET /api/v1/teachers/{id}/assignments` - List teacher's subject assignments

### **Assignments**
- `POST /api/v1/assignments/subject` - Assign teacher to subject/class
- `DELETE /api/v1/assignments/subject/{id}` - Remove assignment
- `POST /api/v1/assignments/class-enrollment` - Enroll student in class
- `DELETE /api/v1/assignments/class-enrollment/{id}` - Remove enrollment

### **Parents**
- `GET /api/v1/parents` - List all parents
- `POST /api/v1/parents` - Register new parent
- `GET /api/v1/parents/{id}` - Get parent details
- `PUT /api/v1/parents/{id}` - Update parent
- `DELETE /api/v1/parents/{id}` - Delete parent
- `GET /api/v1/parents/{id}/children` - List parent's children

---

## **PHASE 2A: FRONTEND PAGES**

### **School Admin**
1. `/dashboard/sessions` - Manage academic sessions
2. `/dashboard/classes` - Manage classes
3. `/dashboard/subjects` - Manage subjects
4. `/dashboard/students` - Student management (upgrade from placeholder)
5. `/dashboard/students/add` - Add new student
6. `/dashboard/students/[id]` - Student profile
7. `/dashboard/students/[id]/edit` - Edit student
8. `/dashboard/teachers` - Teacher management (upgrade from placeholder)
9. `/dashboard/teachers/add` - Add new teacher
10. `/dashboard/teachers/[id]` - Teacher profile
11. `/dashboard/teachers/[id]/edit` - Edit teacher

### **Teacher Portal** (Phase 2B)
1. `/teacher/dashboard` - Teacher dashboard
2. `/teacher/classes` - My classes
3. `/teacher/students` - My students

### **Student Portal** (Phase 2B)
1. `/student/dashboard` - Student dashboard
2. `/student/profile` - My profile

### **Parent Portal** (Phase 2C)
1. `/parent/dashboard` - Parent dashboard
2. `/parent/children` - My children

---

## **DEVELOPMENT PRIORITIES FOR PHASE 2A**

### **Day 1: Database Setup**
1. Create SQL migration file for all new tables
2. Apply schema to Supabase
3. Test database relationships

### **Day 2: Backend - Academic Structure**
1. Create models for sessions, terms, classes, subjects
2. Implement CRUD endpoints for academic structure
3. Add validation and error handling

### **Day 3: Backend - Students & Teachers**
1. Create models for students, teachers, parents
2. Implement student CRUD endpoints
3. Implement teacher CRUD endpoints
4. Add photo upload functionality

### **Day 4: Frontend - Academic Structure**
1. Create session management page
2. Create class management page
3. Create subject management page
4. Add forms and validation

### **Day 5: Frontend - Student Management**
1. Upgrade student list page with real data
2. Create add student form
3. Create student profile page
4. Add guardian management

### **Day 6: Frontend - Teacher Management**
1. Upgrade teacher list page with real data
2. Create add teacher form
3. Create teacher profile page
4. Add subject assignment interface

---

## **SUCCESS CRITERIA FOR PHASE 2A**
- ✅ All database tables created and relationships working
- ✅ Academic sessions and terms can be created
- ✅ Classes and subjects can be managed
- ✅ Students can be registered with full details
- ✅ Teachers can be registered with full details
- ✅ Guardians can be added to students
- ✅ All CRUD operations working
- ✅ Frontend forms are functional and validated
- ✅ Photo upload working
- ✅ Data displays correctly on all pages

Let's build Phase 2A! 🚀
