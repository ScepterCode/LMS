# Phase 4 Deployment & Migration Guide

## Overview

This guide provides step-by-step instructions for deploying Phase 4 (Teacher Class Management) to your LMS. Phase 4 introduces form teachers, class subject curriculum, and configurable grading schemes.

**Key Features Deployed:**
- ✓ Form teacher role with exclusive permissions
- ✓ Class-subject curriculum management
- ✓ Configurable grading schemes (20-20-60, 20-20-20-40, etc.)
- ✓ Attendance marking by form teachers
- ✓ Report card remarks system
- ✓ Report distribution to parents
- ✓ Complete permission enforcement

---

## Pre-Deployment Checklist

- [ ] Backend server running (Python 3.9+, FastAPI)
- [ ] PostgreSQL database (Supabase or local)
- [ ] Database connection credentials configured
- [ ] All Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables configured (`.env` file)
- [ ] Current database schema at Phase 3 level
- [ ] Backup of existing database created
- [ ] Git repository up to date

**Verify Database Connection:**
```bash
cd backend
python -c "from app.core.database import get_supabase; print(get_supabase())"
```

---

## Step 1: Backup Current Database

**IMPORTANT:** Create a backup before applying migrations.

```bash
# For Supabase:
# Download backup from Supabase Dashboard → Settings → Backups

# For local PostgreSQL:
pg_dump -U postgres -d lms_database -f backups/phase3_backup_$(date +%Y%m%d_%H%M%S).sql
```

**Backup Verification:**
```bash
ls -lh backups/
# Should see recent backup file
```

---

## Step 2: Review Phase 4 Schema

Review the new schema before applying:

```bash
# View schema design
cat database/phase4_complete_schema.sql | head -100

# Count tables to be created
grep "CREATE TABLE" database/phase4_complete_schema.sql | wc -l
# Expected: 7 new tables
```

**New Tables:**
1. `class_subjects` — Class curriculum (subjects per class/session)
2. `grading_schemes` — Configurable assessment formats (20-20-60, etc.)
3. `grading_scheme_components` — Individual assessment components
4. `teacher_class_assignments` — Teacher assignments (form teacher + subject teachers)
5. `student_remarks` — Report card remarks
6. `school_reports` — Reports sent to parents
7. `school_report_recipients` — Report delivery tracking

---

## Step 3: Apply Database Migration

### Option A: Python Migration Tool (Recommended)

```bash
cd backend

# Apply migration
python database/migrate_phase4.py --apply

# Expected output:
# Connected to database
# Applying Phase 4 schema...
# ✓ Phase 4 tables created successfully
# ✓ Indices created successfully
# ✓ Seed data loaded
# Migration completed!
```

### Option B: SQL Script (Direct)

```bash
# For Supabase:
# 1. Go to Supabase Dashboard → SQL Editor
# 2. Create new query
# 3. Copy contents of database/phase4_complete_schema.sql
# 4. Execute

# For local PostgreSQL:
psql -U postgres -d lms_database -f database/phase4_complete_schema.sql

# Expected output:
# CREATE TABLE
# CREATE INDEX
# ...
```

---

## Step 4: Verify Migration Success

```bash
# Run verification script
python database/migrate_phase4.py --verify

# Expected output:
# ✓ class_subjects table exists
# ✓ grading_schemes table exists
# ✓ grading_scheme_components table exists
# ✓ teacher_class_assignments table exists
# ✓ student_remarks table exists
# ✓ school_reports table exists
# ✓ school_report_recipients table exists
# ✓ All indices created
# ✓ Seed data loaded (5 grading schemes)
# All verifications passed!
```

**Manual Verification Queries:**

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'class_%'
OR table_name LIKE 'grading_%'
OR table_name LIKE 'teacher_%'
OR table_name LIKE 'student_%'
OR table_name LIKE 'school_%';

-- Should return 7 rows

-- Check seed data
SELECT COUNT(*) FROM grading_schemes;
-- Should return 5 (default schemes)

SELECT name FROM grading_schemes;
-- Should show: 20-20-60, 20-20-20-40, 20-40-40, 10-10-10-70, 100-Exam-Only
```

---

## Step 5: Update Backend Code

### 1. Ensure Latest Code Files

Verify these files exist:

```bash
ls -l backend/app/models/teacher_management.py
ls -l backend/app/api/v1/endpoints/teacher_management.py
ls -l backend/app/api/v1/endpoints/teacher_actions.py
ls -l backend/app/core/permissions.py
```

### 2. Verify Router Registration

Check `backend/app/api/v1/api.py`:

```python
# Should contain these imports:
from app.api.v1.endpoints import (
    ...
    teacher_management,
    teacher_actions
)

# Should contain these registrations:
api_router.include_router(teacher_management.router, prefix="/teacher-management", tags=["Teacher Management - Form Teachers & Grading Schemes"])
api_router.include_router(teacher_actions.router, prefix="/teacher", tags=["Teacher Actions - Form Teacher Duties"])
```

### 3. Install/Update Dependencies

```bash
cd backend
pip install -r requirements.txt

# Verify FastAPI version (should be 0.104.1+)
pip show fastapi | grep Version
```

---

## Step 6: Start Backend Server

```bash
cd backend

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# Uvicorn running on http://0.0.0.0:8000
# ...
# Application startup complete
```

**Verify API is running:**
```bash
curl http://localhost:8000/api/v1/health

# Expected response:
{
  "status": "healthy",
  "version": "v1",
  "phase": "Phase 4 - Teacher Class Management (Form Teachers & Grading Schemes)",
  "endpoints": {
    ...
    "teacher_management": [...],
    "teacher_actions": [...]
  }
}
```

---

## Step 7: Test Core Features

### Test 1: Create Grading Scheme (Admin)

```bash
curl -X POST http://localhost:8000/api/v1/teacher-management/grading-schemes \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Scheme",
    "components": [
      {"name": "CA", "percentage": 20},
      {"name": "MT", "percentage": 20},
      {"name": "EOT", "percentage": 60}
    ]
  }'

# Expected response: 201 Created
```

### Test 2: View My Classes (Teacher)

```bash
curl -X GET http://localhost:8000/api/v1/teacher/my-classes \
  -H "Authorization: Bearer YOUR_TEACHER_TOKEN"

# Expected response: 200 OK with list of form teacher's classes
```

### Test 3: Mark Attendance (Form Teacher)

```bash
curl -X POST http://localhost:8000/api/v1/teacher/my-classes/{class_id}/attendance \
  -H "Authorization: Bearer YOUR_TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "uuid",
    "term_id": "uuid",
    "attendance_date": "2024-06-11",
    "records": [
      {"student_id": "uuid", "status": "present"}
    ]
  }'

# Expected response: 200 OK with count
```

---

## Step 8: Data Migration (Existing Data)

### Option A: Automatic (if available)

```bash
python database/migrate_phase4.py --migrate-data

# This migrates:
# - Existing teacher assignments
# - Existing attendance records
# - Student enrollments
```

### Option B: Manual

**1. Link existing teachers to classes as form teachers:**

```sql
-- For each teacher already assigned to a class, designate as form teacher
-- (Only if you want to preserve existing assignments)
UPDATE teacher_class_assignments
SET is_form_teacher = true
WHERE subject_id IS NULL  -- Teachers without specific subject
LIMIT 1 PER class_id;  -- Only one per class
```

**2. Migrate existing attendance:**

Existing attendance records should still work if they exist in the `attendance` table.

**3. Create class subjects from existing enrollments:**

```sql
-- Create class_subjects from existing teacher assignments
INSERT INTO class_subjects (class_id, subject_id, session_id)
SELECT DISTINCT c.id, ta.subject_id, ta.session_id
FROM teacher_class_assignments ta
JOIN classes c ON ta.class_id = c.id
WHERE ta.subject_id IS NOT NULL
ON CONFLICT DO NOTHING;
```

---

## Step 9: Update Frontend (if applicable)

### Add New Routes

Add these to your frontend routing:

```typescript
// For teachers
/teacher/dashboard          // Form teacher dashboard
/teacher/my-classes        // View assigned classes
/teacher/attendance        // Mark attendance
/teacher/remarks           // Add remarks
/teacher/reports           // Send reports

// For admins
/admin/grading-schemes     // Configure grading schemes
/admin/teacher-assignments // Assign form teachers
/admin/class-subjects      // Manage class curriculum
```

### Fetch from New Endpoints

```typescript
// Get form teacher's classes
const response = await fetch('/api/v1/teacher/my-classes', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// Mark attendance
await fetch(`/api/v1/teacher/my-classes/${classId}/attendance`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify(attendanceData)
});
```

---

## Step 10: Rollback Instructions (if needed)

If you need to rollback Phase 4:

```bash
# Run rollback script
python database/migrate_phase4.py --rollback

# Expected output:
# ⚠️  WARNING: This will DROP all Phase 4 tables
# Continue? (yes/no): yes
# Dropping Phase 4 tables...
# ✓ All Phase 4 tables dropped
# Rollback completed!

# OR manually:
psql -U postgres -d lms_database -f database/phase4_rollback.sql
```

**What gets deleted:**
- All 7 Phase 4 tables
- All associated data (remarks, reports, assignments)
- All indices

---

## Troubleshooting

### Issue: Migration fails with "Table already exists"

**Solution:**
```bash
# Check which tables exist
python database/migrate_phase4.py --verify

# If tables exist but need recreation:
python database/migrate_phase4.py --rollback  # Remove old tables
python database/migrate_phase4.py --apply     # Reapply
```

---

### Issue: Permission denied on teacher endpoints

**Possible Causes:**
1. User is not a teacher in the system
2. Teacher not assigned as form teacher for the class
3. Invalid authentication token

**Debug:**
```bash
# Check teacher record exists
SELECT * FROM teachers WHERE user_id = 'user_uuid';

# Check form teacher assignment
SELECT * FROM teacher_class_assignments 
WHERE teacher_id = 'teacher_uuid' AND is_form_teacher = true;

# Check token validity
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Issue: Attendance date validation error

**Problem:** "Cannot mark attendance for future dates"

**Solution:**
- Ensure system date/time is correct
- Attendance date must be today or earlier
- Use ISO format: YYYY-MM-DD

---

### Issue: Grading scheme validation error

**Problem:** "Components must sum to 100%"

**Solution:**
- Verify all component percentages
- Sum must equal exactly 100
- Check for rounding errors (use whole numbers)

Example valid scheme:
```json
{
  "components": [
    {"name": "CA", "percentage": 20},
    {"name": "MT", "percentage": 20},
    {"name": "EOT", "percentage": 60}
  ]
  // Total: 20 + 20 + 60 = 100 ✓
}
```

---

## Performance Considerations

### Database Indices

Phase 4 creates these indices for performance:

```sql
CREATE INDEX idx_teacher_class_assignments_teacher_id 
ON teacher_class_assignments(teacher_id);

CREATE INDEX idx_teacher_class_assignments_class_id 
ON teacher_class_assignments(class_id);

CREATE UNIQUE INDEX idx_form_teacher_unique 
ON teacher_class_assignments(class_id, session_id) 
WHERE is_form_teacher = true;
```

### Query Optimization Tips

1. **Class Students Query:** Uses `class_id` index (fast)
2. **Form Teacher Check:** Uses unique constraint (very fast)
3. **Attendance Queries:** Add index on `attendance_date` if querying many dates

---

## Post-Deployment Monitoring

### Health Check

```bash
# Run daily
curl http://localhost:8000/api/v1/health

# Monitor:
# - Phase status should show "Phase 4"
# - Endpoints should list new routes
```

### Database Queries to Monitor

```sql
-- Active form teacher assignments
SELECT COUNT(*) FROM teacher_class_assignments 
WHERE is_form_teacher = true;

-- Attendance records created today
SELECT COUNT(*) FROM attendance 
WHERE attendance_date = CURRENT_DATE;

-- Reports sent (last 7 days)
SELECT COUNT(*) FROM school_reports 
WHERE created_at > CURRENT_DATE - INTERVAL '7 days';

-- Teachers with form classes
SELECT COUNT(DISTINCT teacher_id) 
FROM teacher_class_assignments 
WHERE is_form_teacher = true;
```

---

## Documentation References

- [Database Schema Design](database/PHASE4_MIGRATION_GUIDE.md)
- [Admin Endpoints Documentation](backend/PHASE4_ADMIN_ENDPOINTS.md)
- [Teacher Endpoints Documentation](backend/PHASE4_TEACHER_ENDPOINTS.md)
- [Permissions & Authorization](backend/PERMISSIONS_ENFORCEMENT.md)
- [Test Suite](backend/tests/test_phase4_features.py)

---

## Support & Issues

**Common Issues Channel:** 
See `TROUBLESHOOTING.md` for additional solutions

**Database Issues:**
Run `python database/migrate_phase4.py --verify` to diagnose

**API Issues:**
Check logs: `tail -f backend/app.log`

---

## Success Criteria

Phase 4 deployment is successful when:

- ✓ All 7 Phase 4 tables created
- ✓ Admin can create grading schemes
- ✓ Admin can assign form teachers
- ✓ Form teachers can mark attendance
- ✓ Form teachers can add remarks
- ✓ Form teachers can send reports
- ✓ Permissions enforced (403 for unauthorized access)
- ✓ Tests pass: `pytest backend/tests/test_phase4_features.py`

---

**Phase 4 Deployment Ready!** 🚀

