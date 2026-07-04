# 🔧 SETUP GUIDE - Phase 1 Backend

Follow these steps to configure and test your backend.

## Step 1: Get Supabase Credentials

### 1.1 Open Supabase Dashboard
Go to: https://supabase.com/dashboard

### 1.2 Select Your Project
Click on your Nigerian LMS project

### 1.3 Get Database URL
1. Click **Settings** (gear icon in sidebar)
2. Click **Database**
3. Scroll to **Connection String**
4. Select **URI** tab
5. Copy the connection string (looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijklmnop.supabase.co:5432/postgres
   ```
6. Replace `[YOUR-PASSWORD]` with your actual database password

### 1.4 Get API Credentials
1. Click **Settings** (gear icon in sidebar)
2. Click **API**
3. Copy these values:
   - **Project URL**: `https://abcdefghijklmnop.supabase.co`
   - **anon public key**: Long string starting with `eyJ...`
   - **service_role key**: Another long string starting with `eyJ...`

## Step 2: Configure Backend Environment

### 2.1 Open backend/.env file

Open the file: `backend/.env`

### 2.2 Update with Your Credentials

Replace the placeholder values with your actual credentials:

```env
# Database (from Step 1.3)
DATABASE_URL=postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres

# Supabase (from Step 1.4)
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_KEY=your_actual_anon_key_here
SUPABASE_SERVICE_KEY=your_actual_service_key_here

# JWT Secret (generate a random string)
JWT_SECRET=your-super-secret-random-string-here-change-this

# Everything else can stay as is
ENVIRONMENT=development
DEBUG=true
HOST=127.0.0.1
PORT=8000
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
BCRYPT_ROUNDS=12
COOKIE_NAME=access_token
COOKIE_MAX_AGE=86400
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 2.3 Generate JWT Secret

For `JWT_SECRET`, use a random string. You can generate one with:

**Option 1: Python**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Option 2: PowerShell**
```powershell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
```

**Option 3: Just use a random string**
```
my-super-secret-jwt-key-2024-nigerian-lms-production
```

## Step 3: Install Dependencies

Open PowerShell/Terminal and run:

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- FastAPI
- Uvicorn
- Supabase client
- PostgreSQL drivers
- JWT libraries
- And more...

Wait for installation to complete (may take 2-3 minutes).

## Step 4: Setup Database Schema

Go back to project root and run:

```bash
cd ..
python apply_phase1_schema.py
```

You'll see:
```
============================================================
NIGERIAN LMS - PHASE 1 MVP DATABASE SETUP
============================================================

This will DROP existing tables and create fresh ones. Continue? (y/N):
```

Type `y` and press Enter.

The script will:
1. ✅ Create all tables (users, organizations, subscription_plans, campuses)
2. ✅ Insert 4 subscription plans
3. ✅ Create system admin account
4. ✅ Create demo school with admin
5. ✅ Verify everything was created

You should see:
```
✅ Schema applied successfully!
🎉 Database setup complete!
```

## Step 5: Test Configuration

Run the test script:

```bash
python test_backend_setup.py
```

This will check:
- ✅ Python version
- ✅ Project structure
- ✅ Environment configuration
- ✅ Dependencies installed
- ✅ Database connection
- ✅ Database schema

If all checks pass, you'll see:
```
✅ All checks passed! (6/6)
🚀 You're ready to start the backend server!
```

## Step 6: Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Note**: You might see a warning about database pool initialization failing on Windows. This is expected and the app will use Supabase client fallback.

## Step 7: Test API

### 7.1 Open API Documentation

Open your browser to: http://127.0.0.1:8000/docs

You should see the Swagger UI with all API endpoints.

### 7.2 Test Health Check

Click on `GET /health` → Try it out → Execute

Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": {
    "overall": true
  }
}
```

### 7.3 Test Login

1. Click on `POST /api/v1/auth/login`
2. Click "Try it out"
3. Enter:
   ```json
   {
     "email": "admin@nigerianlms.com",
     "password": "Admin123!@#"
   }
   ```
4. Click "Execute"

Should return 200 OK with:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "admin@nigerianlms.com",
    "full_name": "System Administrator",
    "role": "system_admin",
    ...
  }
}
```

### 7.4 Test Get Current User

1. Click on `GET /api/v1/auth/me`
2. Click "Try it out"
3. Click "Execute"

Should return your user profile (because the cookie was set from login).

### 7.5 Test System Admin Endpoints

1. Click on `GET /api/v1/system-admin/analytics`
2. Click "Try it out"
3. Click "Execute"

Should return platform analytics:
```json
{
  "organizations": {
    "total": 1,
    "trial": 1,
    "active": 0,
    ...
  },
  "users": {
    "total": 2,
    "system_admin": 1,
    "admin": 1,
    ...
  }
}
```

## Step 8: Test School Registration

### 8.1 Register a New School

1. Click on `POST /api/v1/auth/register-school`
2. Click "Try it out"
3. Enter:
   ```json
   {
     "school_name": "My Test School",
     "school_email": "contact@mytestschool.com",
     "school_phone": "+234 800 123 4567",
     "school_address": "123 Test Street, Lagos, Nigeria",
     "admin_name": "John Doe",
     "admin_email": "admin@mytestschool.com",
     "admin_password": "TestPass123!",
     "admin_phone": "+234 800 123 4568",
     "subscription_plan_id": "trial"
   }
   ```
4. Click "Execute"

Should return:
```json
{
  "message": "School registered successfully! You can now login with your admin credentials.",
  "organization_id": "...",
  "admin_id": "...",
  "login_email": "admin@mytestschool.com"
}
```

### 8.2 Login with New School Admin

1. Go back to `POST /api/v1/auth/login`
2. Enter:
   ```json
   {
     "email": "admin@mytestschool.com",
     "password": "TestPass123!"
   }
   ```
3. Click "Execute"

Should return 200 OK with the new admin's details.

## ✅ Success Checklist

- [ ] Supabase credentials configured in `.env`
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database schema applied (`python apply_phase1_schema.py`)
- [ ] Test script passed (`python test_backend_setup.py`)
- [ ] Backend server started successfully
- [ ] API documentation accessible at http://127.0.0.1:8000/docs
- [ ] Health check returns healthy status
- [ ] Can login as system admin
- [ ] Can view current user profile
- [ ] Can view platform analytics
- [ ] Can register new school
- [ ] Can login as new school admin

## 🐛 Troubleshooting

### "Database pool initialization failed"
- **This is expected on Windows**
- App will use Supabase client fallback
- Everything will still work

### "Invalid credentials" when logging in
- Check you're using the correct email/password
- Default system admin: `admin@nigerianlms.com` / `Admin123!@#`
- Make sure database schema was applied

### "Module not found" errors
- Make sure you're in the `backend` directory
- Run `pip install -r requirements.txt`
- Check Python version is 3.8+

### "Connection refused" errors
- Make sure backend server is running
- Check it's running on http://127.0.0.1:8000
- Try accessing http://127.0.0.1:8000/health directly

### "Table does not exist" errors
- Run `python apply_phase1_schema.py` again
- Check Supabase credentials are correct
- Verify you can access Supabase dashboard

## 📞 Next Steps

Once all tests pass:

1. ✅ Backend is working
2. ✅ Database is configured
3. ✅ Authentication works
4. ✅ School registration works

**You're ready to build the frontend!**

Let me know when you're ready and I'll start building the Next.js frontend.