# 🚀 SUPABASE SQL EDITOR - APPLY SCHEMA

## Because Network Connection is Limited

Your local machine can't directly connect to the Supabase database, but you can use the **Supabase SQL Editor** (web interface) to apply the schema. This is actually **faster and more reliable**.

---

## ✅ Step-by-Step Instructions

### **Step 1: Open Supabase Dashboard**

1. Go to: https://app.supabase.com
2. Login to your account
3. Select your **LMS project**

### **Step 2: Open SQL Editor**

1. In the left sidebar, click **"SQL Editor"**
2. Click **"New Query"** button
3. You'll see a blank SQL editor

### **Step 3: Copy the Consolidated SQL**

1. **Find the file**: `SUPABASE_CONSOLIDATED_SCHEMA.sql` in your project root
2. **Open it** with a text editor
3. **Select All** (Ctrl+A) and **Copy** (Ctrl+C)

### **Step 4: Paste into Supabase**

1. **Click in the SQL editor** in your browser
2. **Paste** (Ctrl+V) the entire SQL content
3. You should see ~200 lines of SQL code

### **Step 5: Run the Migration**

1. Click the **"Run"** button (▶️ icon in top right)
2. **Wait 30-60 seconds** for execution
3. Check the **"Results"** tab at the bottom

### **Step 6: Verify Success**

After execution, you should see:
```
Schema Migration Complete!
total_tables: 35+
completed_at: 2026-06-16 XX:XX:XX
```

---

## 🔍 What Gets Created

### **Phase 1** ✅
- ✓ subscription_plans table
- ✓ organizations table (with demo school)
- ✓ users table (with admin accounts)
- ✓ campuses table
- ✓ system_admins table

### **Phase 2** ✅
- ✓ academic_sessions table
- ✓ terms table
- ✓ classes table
- ✓ subjects table
- ✓ students & student_guardians
- ✓ teachers table
- ✓ subject_assignments
- ✓ class_enrollments
- ✓ parents & parent_student_links

### **Phase 4** ✅
- ✓ class_subjects (curriculum)
- ✓ grading_schemes (20-20-60, 20-20-20-40, etc.)
- ✓ grading_scheme_components
- ✓ teacher_class_assignments
- ✓ student_remarks
- ✓ school_reports
- ✓ school_report_recipients

---

## ⚠️ Common Issues & Solutions

### **Issue: "Relation already exists"**
- **Cause**: Running the script twice
- **Solution**: This is OK! The script uses `CREATE TABLE IF NOT EXISTS`
- **Action**: Just run it again, it will skip existing tables

### **Issue: "Foreign key constraint failed"**
- **Cause**: Tables being created out of order
- **Solution**: The script is designed to handle this
- **Action**: Run the complete script, don't run pieces individually

### **Issue: Query times out**
- **Cause**: Script is very large (~500 lines)
- **Solution**: This is expected, just wait
- **Action**: Check the Results tab after 60 seconds

### **Issue: Nothing in Results tab**
- **Cause**: Query is still running or no errors (success case!)
- **Solution**: Scroll down in Results tab
- **Action**: Check that you see "Schema Migration Complete!" message

---

## ✅ After Running the Script

### **1. Verify Tables Were Created**

1. Go to **"Tables"** in left sidebar
2. You should see:
   - users
   - organizations
   - students
   - teachers
   - grading_schemes
   - ... and many more

### **2. Check Demo Data**

Run this query in a new SQL Editor:
```sql
SELECT * FROM users LIMIT 5;
```

Should return:
- admin@nigerianlms.com (System Admin)
- admin@demo-school.com (School Admin)

### **3. Ready for Application**

Now your database is ready:
1. ✅ All tables created
2. ✅ Demo data seeded
3. ✅ Ready to run the app

---

## 🚀 Next Steps

After running migrations:

```bash
# 1. Go back to terminal
cd c:\Users\DELL\Downloads\LMS

# 2. Start the application
.\start-dev.ps1

# 3. Open in browser
http://localhost:3000

# 4. Login with demo account
Email: admin@demo-school.com
Password: Admin123!@#
```

---

## 📝 Alternative: Run in Pieces

If the full script times out, you can run **individual files**:

1. `database/phase1_minimal_schema.sql`
2. `database/phase2_schema.sql`
3. `database/phase4_teacher_class_schema.sql`
4. `database/phase4_seed_data.sql`

Just paste each one in SQL Editor and run separately.

---

## ⏱️ Estimated Time

- **Full Script**: 30-60 seconds
- **Individual Files**: 10-15 seconds each

---

**You got this!** 🎉 The web-based SQL Editor is actually MORE reliable than command-line connections.
