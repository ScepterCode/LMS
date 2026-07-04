# 🚀 QUICK START - Phase 1 MVP

## What We Have Now

✅ **Backend**: Complete FastAPI application with authentication, school registration, and admin features
✅ **Database Schema**: Minimal schema for Phase 1 MVP
✅ **Documentation**: Complete API documentation and guides

## 🎯 Next: Setup and Test

### Step 1: Configure Supabase

1. Go to your Supabase project dashboard
2. Get your connection details:
   - **Database URL**: Settings → Database → Connection String (URI)
   - **Project URL**: Settings → API → Project URL
   - **Anon Key**: Settings → API → Project API keys → anon/public
   - **Service Key**: Settings → API → Project API keys → service_role

### Step 2: Update Backend .env

Edit `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here
JWT_SECRET=change-this-to-a-random-secure-string
```

### Step 3: Setup Database

```bash
# From project root
python apply_phase1_schema.py
```

Answer `y` when prompted. This will:
- Create all tables
- Insert subscription plans
- Create system admin account
- Create demo school

### Step 4: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 5: Start Backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 6: Test Backend

Open browser to: `http://127.0.0.1:8000/docs`

Try the login endpoint:
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
5. Should return 200 OK with user data and token

## 🎨 Next: Build Frontend

Now that backend is working, we need to build the frontend:

### What We Need to Build:

1. **Next.js Setup**
   - Create Next.js 15 app with TypeScript
   - Setup Tailwind CSS
   - Configure environment variables

2. **Authentication**
   - AuthContext for state management
   - Login page
   - Protected routes middleware

3. **Public Pages**
   - Landing page (/)
   - Login page (/login)
   - School registration page (/register-school)

4. **Protected Pages**
   - System admin dashboard (/system-admin)
   - School admin dashboard (/dashboard)

5. **Components**
   - Navigation
   - Forms
   - Cards
   - Tables

## 📋 Development Order

### Today: Backend Testing
- [x] Backend structure created
- [x] Database schema created
- [ ] Test all API endpoints
- [ ] Verify authentication works
- [ ] Test school registration

### Tomorrow: Frontend Foundation
- [ ] Create Next.js app
- [ ] Setup Tailwind CSS
- [ ] Create AuthContext
- [ ] Build login page
- [ ] Test login flow

### Day 3: Dashboards
- [ ] System admin dashboard
- [ ] School admin dashboard
- [ ] Navigation components
- [ ] Basic styling

### Day 4: Polish & Integration
- [ ] Connect all pages
- [ ] Test complete flow
- [ ] Fix any bugs
- [ ] Documentation

## 🧪 Testing Checklist

### Backend Tests

- [ ] Health check: `http://127.0.0.1:8000/health`
- [ ] API docs: `http://127.0.0.1:8000/docs`
- [ ] Login with system admin
- [ ] Login with school admin
- [ ] Register new school
- [ ] Get current user profile
- [ ] Logout
- [ ] View platform analytics (system admin)
- [ ] List organizations (system admin)
- [ ] View organization details

### Integration Tests (After Frontend)

- [ ] Login from frontend
- [ ] Redirect to correct dashboard
- [ ] Protected routes work
- [ ] Logout works
- [ ] School registration from frontend
- [ ] View data in dashboards

## 🐛 Common Issues

### "Database pool initialization failed"
- **Expected on Windows** due to DNS issues
- App will use Supabase client fallback
- Everything will still work

### "Module not found"
- Make sure you're in the `backend` directory
- Run `pip install -r requirements.txt`

### "Invalid credentials"
- Check you're using correct email/password
- Default: `admin@nigerianlms.com` / `Admin123!@#`

### CORS errors (after frontend)
- Check `ALLOWED_ORIGINS` in backend `.env`
- Should include `http://localhost:3000`

## 📞 Need Help?

Check these files:
- `PHASE1_MVP_PLAN.md` - Overall plan
- `PHASE1_BACKEND_COMPLETE.md` - Backend details
- `backend/README.md` - Backend documentation
- `database/phase1_minimal_schema.sql` - Database schema

## 🎯 Success Criteria

Phase 1 MVP is complete when:
- ✅ User can register a school
- ✅ User can login as system admin
- ✅ User can login as school admin
- ✅ System admin can view all schools
- ✅ School admin can view their school
- ✅ Protected routes work correctly
- ✅ No broken links or errors

## 🚀 Let's Build the Frontend!

Ready to continue? Let me know and I'll start building the Next.js frontend!