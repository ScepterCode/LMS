# 🎯 LMS Onboarding Workflow Guide

## Overview
The LMS has a **required setup sequence** that must be followed. This guide explains the correct order and dependencies.

## ⚠️ Critical Setup Order

### Phase 1: Foundation (REQUIRED FIRST)
These **must** be completed before anything else:

#### 1️⃣ Create Academic Session
**Location:** Dashboard > Academic Management > Sessions Tab
**Why First:** Everything else depends on having an active session
**Example:**
- Name: `2024/2025` or `2026/2027`
- Start Date: September 1, 2024
- End Date: August 31, 2025
- ✅ Check "Set as current session"

**Status:** ✅ **COMPLETE THIS FIRST**

---

#### 2️⃣ Create Subjects
**Location:** Dashboard > Academic Management > Subjects Tab
**Why Second:** Classes and teachers need subjects to assign
**Examples:**
- Mathematics (Core)
- English Language (Core)
- Physics (Core)
- Chemistry (Core)
- Biology (Core)
- Computer Science (Elective)
- Fine Arts (Elective)

**Minimum Required:** At least 3-5 subjects

---

#### 3️⃣ Create Classes
**Location:** Dashboard > Academic Management > Classes Tab
**Why Third:** Students and teachers need classes to belong to
**Examples:**
- JSS 1 (Junior Secondary 1)
- JSS 2
- JSS 3
- SS 1 (Senior Secondary 1)
- SS 2
- SS 3

**Important:** Select which subjects are offered in each class

---

### Phase 2: People (After Foundation)

#### 4️⃣ Create User Accounts for Teachers
**Location:** Dashboard > System Admin (if system admin) OR Register-School page
**Process:**
1. Go to user management
2. Create account with role = "teacher"
3. Record the User ID (you'll need it next)

**Note:** Teachers need a USER ACCOUNT first, then a teacher profile

---

#### 5️⃣ Create Teacher Profiles
**Location:** Dashboard > Teachers > Add Teacher
**Required Fields:**
- User ID (from step 4)
- Qualification
- Subjects they can teach
- Specialization

---

#### 6️⃣ Create Students
**Location:** Dashboard > Students > Add Student
**Required Fields:**
- Basic Information
- **Current Class** (select from classes created in step 3)
- Admission Number
- Contact Details

**Dependency:** Requires academic session + class to exist

---

#### 7️⃣ Add Parents/Guardians
**Location:** Dashboard > Parents > Add Parent OR Students > [Student] > Add Guardian
**Two Options:**
- Create parent first, then link to student
- Or add guardian directly from student detail page

---

### Phase 3: Academic Structure (After People)

#### 8️⃣ Class Enrollment
**Location:** Dashboard > Enrollments
**Purpose:** Formally enroll students into classes for the current session
**Required:**
- Student (created)
- Class (created)
- Academic Session (created)

---

#### 9️⃣ Teacher Assignments
**Location:** Dashboard > Teacher Management > Teacher Assignments
**Purpose:** Assign teachers to specific subjects in specific classes
**Required:**
- Teacher (created)
- Subject (created)
- Class (created)
- Academic Session (created)

---

#### 🔟 Subject Configuration
**Location:** Dashboard > Teacher Management > Class Subjects
**Purpose:** Configure which subjects are taught in each class
**Required:**
- Class (created)
- Subjects (created)
- Academic Session (created)

---

### Phase 4: Operations (After Everything Above)

Now you can use all other features:
- ✅ Attendance Management
- ✅ Grading & Assessments
- ✅ Fee Management
- ✅ Report Cards
- ✅ Teacher Class Management
- ✅ Parent Portal

---

## 🐛 Current Known Issues & Fixes

### Issue #1: Session Creation Fails
**Error:** "An error occurred" when creating academic session
**Status:** FIXED - Supabase client error resolved
**Action:** Restart backend server

### Issue #2: "Current Class" Not Available
**Cause:** No classes created yet OR no current session set
**Fix:**
1. Create academic session FIRST
2. Then create classes
3. Current class dropdown will populate

### Issue #3: Parent Creation Fails
**Cause:** Backend validation or database connection
**Fix:** 
1. Check backend logs
2. Ensure all required fields filled
3. Verify database connection

### Issue #4: Teacher Creation - No User ID
**Cause:** User account must be created FIRST
**Fix:**
1. Go to System Admin or auth management
2. Create user with role="teacher"
3. Use that user's ID when creating teacher profile

### Issue #5: No Options in Dropdowns
**Cause:** Dependency not created yet
**Example:** "No classes available" = you need to create classes first
**Fix:** Follow the setup order above

---

## 📋 Quick Setup Checklist

Use this checklist to track your setup progress:

```
PHASE 1: FOUNDATION
[ ] 1. Create Academic Session (2024/2025)
[ ] 2. Set session as "current"
[ ] 3. Create at least 5 subjects
[ ] 4. Create at least 3 classes
[ ] 5. Assign subjects to classes

PHASE 2: PEOPLE
[ ] 6. Create user accounts for teachers
[ ] 7. Create teacher profiles (using user IDs)
[ ] 8. Create students (with classes assigned)
[ ] 9. Add parents/guardians

PHASE 3: ACADEMIC STRUCTURE
[ ] 10. Enroll students in classes
[ ] 11. Assign teachers to subjects/classes
[ ] 12. Configure grading schemes

PHASE 4: OPERATIONS
[ ] 13. Start marking attendance
[ ] 14. Create assessments
[ ] 15. Enter grades
[ ] 16. Manage fees
```

---

## 🔧 Troubleshooting Commands

### Restart Backend Server
```powershell
# Navigate to backend folder
cd backend

# Restart with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Check Backend Logs
```powershell
# View logs
type backend\app.log | Select-Object -Last 50
```

### Restart Frontend
```powershell
# Navigate to frontend
cd frontend

# Restart Next.js
npm run dev
```

---

## 🎓 Recommended First-Time Setup Sequence

1. **Login as Admin** (admin@nigerianlms.com)
2. **Create Session:** 2024/2025 (mark as current)
3. **Create Subjects:**
   - Mathematics
   - English
   - Science
   - Social Studies
   - Computer Science
4. **Create Classes:**
   - JSS 1 (assign all subjects)
   - JSS 2 (assign all subjects)
   - JSS 3 (assign all subjects)
5. **Create Teacher Accounts:**
   - Create 2-3 user accounts with role="teacher"
   - Note their User IDs
6. **Create Teacher Profiles:**
   - Use the User IDs from step 5
7. **Create Students:**
   - Create 5-10 test students
   - Assign them to different classes
8. **Test All Features:**
   - Attendance
   - Grading
   - Fees
   - Reports

---

## 📞 Need Help?

If you encounter errors:
1. Check this guide for the correct setup order
2. Review backend logs for specific error messages
3. Verify all dependencies are created
4. Ensure backend and frontend servers are running
5. Check database connection in Supabase dashboard

---

## ✅ Success Indicators

You'll know the setup is complete when:
- ✅ Academic session shows as "Current"
- ✅ All dropdown menus populate with options
- ✅ Students appear in class lists
- ✅ Teachers can be assigned to classes
- ✅ Attendance page shows classes to select
- ✅ Grading page shows students and subjects
- ✅ Fee management shows students

---

*Last Updated: July 1, 2026*
*Version: 1.0*
