# 📋 Phase 3 Schema Application Instructions

## ⚠️ Important Note

The `phase3_complete_schema.sql` file contains psql commands (`\echo`, `\i`) that don't work in Supabase SQL Editor.

**Instead, apply each schema file individually in the correct order.**

---

## ✅ Step-by-Step Instructions

### Step 1: Open Supabase Dashboard
1. Go to your Supabase project
2. Click **SQL Editor** in the left sidebar
3. Click **New Query**

---

### Step 2: Apply Grading Schema

1. Open file: `database/phase3_grading_schema.sql`
2. Copy the ENTIRE contents
3. Paste into Supabase SQL Editor
4. Click **Run** (or press Ctrl+Enter)
5. Wait for "Success" message
6. Verify 8 tables created:
   - `assessment_types`
   - `assessments`
   - `grade_configs`
   - `grades`
   - `subject_grades`
   - `report_cards`
   - `grade_comments`

**Expected Result:** ✅ All 8 grading tables created

---

### Step 3: Apply Attendance Schema

1. Open file: `database/phase3_attendance_schema.sql`
2. Copy the ENTIRE contents
3. Paste into Supabase SQL Editor (new query or clear previous)
4. Click **Run**
5. Wait for "Success" message
6. Verify 6 tables created:
   - `attendance_records`
   - `attendance_summaries`
   - `leave_requests`
   - `attendance_settings`
   - `holidays`
   - `teacher_attendance`

**Expected Result:** ✅ All 6 attendance tables created

---

### Step 4: Apply Fee Management Schema

1. Open file: `database/phase3_fees_schema.sql`
2. Copy the ENTIRE contents
3. Paste into Supabase SQL Editor
4. Click **Run**
5. Wait for "Success" message
6. Verify 9 tables created:
   - `fee_categories`
   - `fee_structures`
   - `student_fees`
   - `payments`
   - `payment_allocations`
   - `payment_plans`
   - `payment_installments`
   - `receipts`
   - `fee_reminders`

**Expected Result:** ✅ All 9 fee tables created

---

### Step 5: Seed Default Data

After all tables are created, run this SQL to add default data:

```sql
-- Default Grade Configuration (Nigerian System)
INSERT INTO grade_configs (organization_id, grade_letter, min_score, max_score, grade_point, remark, color_code, is_passing, display_order)
SELECT 
    o.id as organization_id,
    grade_letter,
    min_score,
    max_score,
    grade_point,
    remark,
    color_code,
    is_passing,
    display_order
FROM organizations o
CROSS JOIN (VALUES
    ('A', 70.00, 100.00, 5.00, 'Excellent', '#10B981', true, 1),
    ('B', 60.00, 69.99, 4.00, 'Very Good', '#3B82F6', true, 2),
    ('C', 50.00, 59.99, 3.00, 'Good', '#F59E0B', true, 3),
    ('D', 45.00, 49.99, 2.00, 'Pass', '#EF4444', true, 4),
    ('E', 40.00, 44.99, 1.00, 'Poor', '#DC2626', true, 5),
    ('F', 0.00, 39.99, 0.00, 'Fail', '#991B1B', false, 6)
) AS grades(grade_letter, min_score, max_score, grade_point, remark, color_code, is_passing, display_order)
ON CONFLICT (organization_id, grade_letter) DO NOTHING;

-- Default Assessment Types
INSERT INTO assessment_types (organization_id, name, code, max_score, weight_percentage, display_order)
SELECT 
    o.id as organization_id,
    name,
    code,
    max_score,
    weight_percentage,
    display_order
FROM organizations o
CROSS JOIN (VALUES
    ('First Continuous Assessment', 'CA1', 20.00, 10.00, 1),
    ('Second Continuous Assessment', 'CA2', 20.00, 10.00, 2),
    ('Third Continuous Assessment', 'CA3', 20.00, 10.00, 3),
    ('Midterm Test', 'MID', 20.00, 10.00, 4),
    ('Examination', 'EXAM', 60.00, 60.00, 5)
) AS types(name, code, max_score, weight_percentage, display_order)
ON CONFLICT (organization_id, code) DO NOTHING;

-- Default Fee Categories
INSERT INTO fee_categories (organization_id, name, code, is_mandatory, display_order)
SELECT 
    o.id as organization_id,
    name,
    code,
    is_mandatory,
    display_order
FROM organizations o
CROSS JOIN (VALUES
    ('Tuition Fee', 'TUITION', true, 1),
    ('Development Levy', 'DEVELOPMENT', true, 2),
    ('PTA Dues', 'PTA', true, 3),
    ('Sports Fee', 'SPORTS', false, 4),
    ('Lesson Note', 'LESSON', false, 5),
    ('Uniform', 'UNIFORM', false, 6),
    ('Textbooks', 'BOOKS', false, 7),
    ('Transport', 'TRANSPORT', false, 8),
    ('Feeding', 'FEEDING', false, 9),
    ('ICT Fee', 'ICT', false, 10)
) AS categories(name, code, is_mandatory, display_order)
ON CONFLICT (organization_id, code) DO NOTHING;

-- Default Attendance Settings
INSERT INTO attendance_settings (organization_id, school_start_time, school_end_time, late_threshold_minutes)
SELECT 
    id as organization_id,
    '08:00:00'::time,
    '14:00:00'::time,
    15
FROM organizations
ON CONFLICT (organization_id) DO NOTHING;
```

**Expected Result:** ✅ Default data seeded for all organizations

---

## 🔍 Verification Checklist

After completing all steps, verify:

### In Table Editor:
- [ ] 23 new tables visible
- [ ] `grade_configs` has 6 rows (A-F grades)
- [ ] `assessment_types` has 5 rows (CA1, CA2, CA3, MID, EXAM)
- [ ] `fee_categories` has 10 rows (Tuition, etc.)
- [ ] `attendance_settings` has 1 row per organization

### Quick Count Query:
```sql
-- Count new Phase 3 tables
SELECT 
    COUNT(*) as phase3_tables
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'assessment_types', 'assessments', 'grade_configs', 'grades',
    'subject_grades', 'report_cards', 'grade_comments',
    'attendance_records', 'attendance_summaries', 'leave_requests',
    'attendance_settings', 'holidays', 'teacher_attendance',
    'fee_categories', 'fee_structures', 'student_fees',
    'payments', 'payment_allocations', 'payment_plans',
    'payment_installments', 'receipts', 'fee_reminders'
);
-- Should return: 23
```

---

## ❌ Troubleshooting

### Error: "relation already exists"
**Solution:** Table already created. Skip that file or drop table first.

### Error: "foreign key constraint"
**Solution:** Apply schemas in correct order (grading → attendance → fees)

### Error: "syntax error"
**Solution:** Make sure you copied the ENTIRE file content including comments

### No default data
**Solution:** Re-run Step 5 seed data SQL

---

## ✅ Success Confirmation

You'll know it worked when:
1. All 23 tables visible in Table Editor
2. No SQL errors in editor
3. Default data present in lookup tables
4. Can query: `SELECT * FROM grade_configs;` successfully

---

## 🚀 Next Steps

After schema is applied:

1. **Build Backend APIs** - Create FastAPI endpoints for:
   - Grading & assessments
   - Attendance tracking
   - Fee management

2. **Build Frontend Pages** - Create UI for:
   - Grade entry
   - Attendance marking
   - Payment recording

3. **Test Features** - Verify full workflows work end-to-end

---

## 📞 Need Help?

If you encounter issues:
1. Check Supabase logs for detailed error messages
2. Verify all Phase 1 & 2 tables exist first
3. Ensure organizations table has data
4. Try applying one table at a time instead of full file

Good luck! 🎉
