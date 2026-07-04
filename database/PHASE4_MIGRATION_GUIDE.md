# Phase 4 Migration Guide - Teacher Class Management

## Overview

This guide walks you through applying Phase 4 database migrations for the teacher class management feature.

**Phase 4 adds:**
- Class-Subject curriculum mapping
- Configurable grading schemes (20-20-60, 20-20-20-40, etc.)
- Enhanced teacher-to-class assignments with form teacher role
- Student remarks and report distribution system

**Total:** 7 new tables, 15 indices, default grading schemes, and data migration helpers

---

## Prerequisites

1. **Supabase Project** — Active PostgreSQL database
2. **PostgreSQL Client** — `psql` or Supabase Studio SQL editor
3. **Backup** — CRITICAL: Backup your database before running migrations
4. **Current State** — Phase 2 or Phase 3 schema already applied

---

## Migration Approach

Phase 4 is designed to be **backward compatible**:
- Existing `subject_assignments` data is preserved
- New `teacher_class_assignments` table is auto-populated from existing assignments
- New tables use `IF NOT EXISTS` clauses for idempotency
- Conflicts handled with `ON CONFLICT DO NOTHING`

---

## Step-by-Step Migration

### Step 1: Backup Your Database

**Using Supabase:**
1. Go to your Supabase project dashboard
2. Settings → Backups
3. Click "Create a backup"
4. Wait for completion (~5-10 minutes)

**Using psql (local):**
```bash
pg_dump postgresql://[user]:[password]@[host]/[database] > backup_phase4_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Apply Phase 4 Schema

**Option A: Using Supabase Studio (Recommended for GUI)**

1. Open Supabase Studio → SQL Editor
2. Copy and paste the entire contents of `phase4_complete_schema.sql`
3. Review the SQL
4. Click "Run"
5. Check the "Results" tab for status messages

**Option B: Using psql (CLI)**

```bash
psql postgresql://[user]:[password]@[host]/[database] -f database/phase4_complete_schema.sql
```

**Option C: Step-by-step (Troubleshooting)**

Run each file individually:

```bash
# Step 1: Create tables
psql postgresql://[user]:[password]@[host]/[database] -f database/phase4_teacher_class_schema.sql

# Step 2: Seed default data
psql postgresql://[user]:[password]@[host]/[database] -f database/phase4_seed_data.sql
```

### Step 3: Verify Migration

Run these queries in Supabase Studio or psql to confirm:

```sql
-- Check all new tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'phase4_%' OR table_name IN (
    'class_subjects', 'grading_schemes', 'grading_scheme_components',
    'teacher_class_assignments', 'student_remarks', 'school_reports', 'school_report_recipients'
)
ORDER BY table_name;

-- Expected output: 7 tables
```

```sql
-- Check grading schemes were seeded
SELECT name, COUNT(*) as component_count 
FROM grading_schemes gs
LEFT JOIN grading_scheme_components gsc ON gs.id = gsc.grading_scheme_id
GROUP BY gs.id, gs.name
ORDER BY gs.name;

-- Expected output: 5 schemes (20-20-60, 20-20-20-40, 20-40-40, 10-10-10-70, 100-Exam-Only)
```

```sql
-- Check teacher_class_assignments were populated
SELECT COUNT(*) as total_assignments FROM teacher_class_assignments;

-- Expected: > 0 if you had subject_assignments
```

```sql
-- Check indices
SELECT indexname FROM pg_indexes 
WHERE schemaname = 'public' AND tablename IN (
    'class_subjects', 'grading_schemes', 'grading_scheme_components',
    'teacher_class_assignments', 'student_remarks', 'school_reports', 'school_report_recipients'
)
ORDER BY indexname;

-- Expected: 15 indices
```

---

## Data Integrity Checks

After migration, verify:

### 1. No Orphaned Records

```sql
-- Check class_subjects
SELECT COUNT(*) FROM class_subjects 
WHERE NOT EXISTS (SELECT 1 FROM classes WHERE classes.id = class_subjects.class_id);

-- Should return: 0
```

### 2. No Duplicate Assignments

```sql
-- Check teacher_class_assignments uniqueness
SELECT teacher_id, subject_id, class_id, term_id, COUNT(*) 
FROM teacher_class_assignments 
GROUP BY teacher_id, subject_id, class_id, term_id 
HAVING COUNT(*) > 1;

-- Should return: 0 rows
```

### 3. Grading Scheme Validity

```sql
-- Verify component weights sum to 100%
SELECT 
    gs.name,
    gs.id,
    ROUND(SUM(gsc.weight_percentage)::numeric, 2) as total_weight
FROM grading_schemes gs
LEFT JOIN grading_scheme_components gsc ON gs.id = gsc.grading_scheme_id
GROUP BY gs.id, gs.name
HAVING ROUND(SUM(gsc.weight_percentage)::numeric, 2) != 100.00;

-- Should return: 0 rows (all schemes sum to 100%)
```

---

## Testing the New Features

### Test 1: Create a Class with Subjects

```sql
-- Get a session ID
SELECT id FROM academic_sessions LIMIT 1;

-- Get some subject IDs
SELECT id FROM subjects LIMIT 5;

-- Then use the API to create a class with these subjects
POST /api/classes
{
    "name": "JSS 1 Test",
    "level": "Junior",
    "section": "A",
    "capacity": 40,
    "session_id": "{{session_uuid}}",
    "subject_ids": ["{{subject_uuid_1}}", "{{subject_uuid_2}}", "{{subject_uuid_3}}"]
}
```

### Test 2: Assign Form Teacher

```sql
-- Get a teacher ID
SELECT id FROM teachers LIMIT 1;

-- Use API to assign as form teacher to a class
POST /api/teacher-class-assignments
{
    "teacher_id": "{{teacher_uuid}}",
    "class_id": "{{class_uuid}}",
    "subject_id": "{{subject_uuid}}",
    "session_id": "{{session_uuid}}",
    "is_form_teacher": true
}
```

### Test 3: Add Student Remarks

```sql
-- Use API to add remarks
POST /api/student-remarks
{
    "student_id": "{{student_uuid}}",
    "class_id": "{{class_uuid}}",
    "session_id": "{{session_uuid}}",
    "term_id": "{{term_uuid}}",
    "remark_text": "Student shows good attendance and participates actively in class.",
    "remarks_category": "academic"
}
```

---

## Rollback Procedure (If Needed)

**WARNING:** This is destructive. Use only if absolutely necessary.

```bash
psql postgresql://[user]:[password]@[host]/[database] -f database/phase4_rollback.sql
```

Or from Supabase Studio:
1. Open SQL Editor
2. Copy contents of `phase4_rollback.sql`
3. Review carefully
4. Run

**After Rollback:**
- All Phase 4 data is deleted
- Existing Phase 2/3 data remains intact
- Run backups if needed for recovery

---

## Common Issues & Troubleshooting

### Issue 1: `relation already exists` error

**Cause:** Tables already exist (possible re-run attempt)

**Solution:** This is expected! The `IF NOT EXISTS` clause handles it. Continue.

### Issue 2: `Foreign key constraint failed`

**Cause:** Referenced table/records don't exist

**Solution:**
- Ensure Phase 2 schema is applied first
- Check that `organizations`, `academic_sessions`, `classes`, `subjects`, `teachers` tables exist

### Issue 3: Grading scheme components don't sum to 100%

**Cause:** Seeding query failed or incomplete

**Solution:**
```sql
-- Check if components exist
SELECT name, COUNT(*) FROM grading_scheme_components GROUP BY name;

-- Re-run seed script if count is 0
psql postgresql://[user]:[password]@[host]/[database] -f database/phase4_seed_data.sql
```

### Issue 4: Performance degradation after migration

**Cause:** Indices not created or statistics not updated

**Solution:**
```sql
-- Analyze all tables
ANALYZE;

-- Reindex if needed
REINDEX TABLE teacher_class_assignments;
REINDEX TABLE class_subjects;
```

---

## Performance Considerations

Phase 4 adds 15 indices for optimal query performance:

- **teacher_class_assignments**: 5 indices (teacher, class, subject, session, form teacher flag)
- **grading_schemes**: 2 indices (organization, session)
- **class_subjects**: 3 indices (class, subject, session)
- **student_remarks**: 4 indices (student, class, session/term, teacher)
- **school_reports**: 5 indices (organization, class, session/term, teacher, type)

**Estimated storage overhead:** ~50-100 MB per 10K records

---

## Next Steps

1. **Update Backend Models** ✓ (Already done in Step 2)
2. **Create API Endpoints** (Step 4)
3. **Implement Permission Checks** (Step 5)
4. **Create Frontend UI** (Step 4)
5. **Test & Deploy** (Step 6)

---

## Support & Questions

For issues or questions:

1. Check error messages in Supabase Studio "Error" tab
2. Review `database/SCHEMA_DESIGN_STEP1.md` for schema overview
3. Check logs in your application backend

---

## Appendix: Migration Checklist

- [ ] Database backup created
- [ ] Phase 4 schema applied (`phase4_complete_schema.sql`)
- [ ] All 7 new tables verified (query: information_schema)
- [ ] Grading schemes seeded (5 schemes with components)
- [ ] teacher_class_assignments populated from subject_assignments
- [ ] Data integrity checks passed (no orphans, valid uniqueness)
- [ ] Index performance verified
- [ ] Backend models updated ✓
- [ ] API endpoints ready for development (Step 4)
- [ ] Testing in progress or complete

---

**Status:** Phase 4 migrations complete ✓

