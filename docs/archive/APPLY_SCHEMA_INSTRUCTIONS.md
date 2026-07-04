# 🔧 Apply Database Schema - Step by Step

Since Windows DNS resolution is blocking the direct connection, we'll apply the schema through Supabase's web interface.

## Step 1: Open Supabase SQL Editor

1. Go to: https://supabase.com/dashboard
2. Select your project: **gygzsasweryajcleolie**
3. Click **SQL Editor** in the left sidebar
4. Click **New Query** button

## Step 2: Copy the SQL Schema

The SQL schema is in: `database/phase1_minimal_schema.sql`

You can either:
- **Option A**: Open the file in VS Code and copy all content (Ctrl+A, Ctrl+C)
- **Option B**: I'll show you the content below

## Step 3: Paste and Run

1. Paste the entire SQL content into the Supabase SQL Editor
2. Click **Run** (or press Ctrl+Enter)
3. Wait for execution (should take 5-10 seconds)
4. You should see: **"Success. No rows returned"** or similar success message

## Step 4: Verify

After running the SQL, you should see these tables created:
- ✅ users
- ✅ organizations  
- ✅ subscription_plans
- ✅ campuses
- ✅ system_admins

You can verify by:
1. Click **Table Editor** in left sidebar
2. You should see all 5 tables listed

## What the Schema Creates

### Default Accounts

**System Admin:**
- Email: `admin@nigerianlms.com`
- Password: `Admin123!@#`
- Role: System Administrator (full platform access)

**Demo School Admin:**
- Email: `admin@demo-school.com`
- Password: `Admin123!@#`
- Role: School Admin (Demo School Lagos only)

### Subscription Plans

- **Trial**: Free 14-day trial (up to 50 students)
- **Basic**: $49.99/month (up to 200 students)
- **Standard**: $99.99/month (up to 500 students)
- **Premium**: $199.99/month (unlimited students)

### Demo Organization

- **Name**: Demo School Lagos
- **Status**: Trial (14 days)
- **Campus**: Main Campus created

## Step 5: Run Verification Script

After applying the schema in Supabase, come back and run:

```bash
python test_backend_setup.py
```

This will verify everything is set up correctly.

## Troubleshooting

### "Permission denied" errors
- Make sure you're using the **service_role** key, not the anon key
- Check that RLS policies allow the operation

### "Table already exists" errors
- The schema includes `DROP TABLE IF EXISTS` statements
- It's safe to run multiple times

### "Syntax error" messages
- Make sure you copied the ENTIRE SQL file
- Check that no characters were corrupted during copy/paste

## Next Steps

Once the schema is applied successfully:

1. ✅ Database is ready
2. ✅ Default accounts created
3. ✅ Subscription plans loaded
4. ✅ Demo school created

**You can now start the backend server!**

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open: http://127.0.0.1:8000/docs
