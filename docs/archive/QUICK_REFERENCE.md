# ⚡ Quick Reference Card

## 🚀 Start Application

```bash
# Option 1: Automated (Windows)
start-dev.bat

# Option 2: Manual
# Terminal 1: cd backend && uvicorn app.main:app --reload
# Terminal 2: cd frontend && npm run dev
```

## 🌐 URLs

```
Frontend:   http://localhost:3000
Backend:    http://127.0.0.1:8000
API Docs:   http://127.0.0.1:8000/docs
Health:     http://127.0.0.1:8000/health
```

## 🔑 Demo Accounts

```
System Admin:
  📧 admin@nigerianlms.com
  🔒 Admin123!@#
  📍 /system-admin

School Admin:
  📧 admin@demo-school.com
  🔒 Admin123!@#
  📍 /dashboard
```

## 📄 Pages

```
Public:
  /                    Landing page
  /login               Login
  /register-school     Registration

Protected:
  /dashboard           School dashboard
  /dashboard/students  Students (Phase 2)
  /dashboard/teachers  Teachers (Phase 2)
  /system-admin        System admin
```

## 🔌 API Endpoints

```
Auth:
  POST /api/v1/auth/login
  POST /api/v1/auth/logout
  GET  /api/v1/auth/me
  POST /api/v1/auth/register-school

System Admin:
  GET  /api/v1/system-admin/organizations
  GET  /api/v1/system-admin/analytics
  PATCH /api/v1/system-admin/organizations/{id}/status

Organizations:
  GET  /api/v1/organizations/{id}
  GET  /api/v1/organizations/{id}/users
  GET  /api/v1/organizations/{id}/campuses
```

## 🔧 Common Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
npm run build

# Database
python apply_phase1_schema.py
python check_database.py
```

## 📁 Key Files

```
Backend:
  app/main.py              - FastAPI app
  app/core/security.py     - Authentication
  app/api/v1/endpoints/    - API routes
  .env                     - Configuration

Frontend:
  app/page.tsx             - Landing page
  app/login/page.tsx       - Login
  contexts/AuthContext.tsx - Auth state
  lib/api.ts               - API client
  .env.local               - Configuration
```

## 🐛 Troubleshooting

```
Backend won't start:
  ✓ Check .env exists
  ✓ Verify Python 3.13+
  ✓ Run: pip install -r requirements.txt

Frontend won't start:
  ✓ Check .env.local exists
  ✓ Verify Node 18+
  ✓ Run: npm install

CORS errors:
  ✓ Check ALLOWED_ORIGINS in backend/.env
  ✓ Should include: http://localhost:3000

Login fails:
  ✓ Verify backend is running
  ✓ Check browser console
  ✓ Test with: admin@nigerianlms.com
```

## 📚 Documentation

```
🏠 Main Docs:
  README.md                    - Project overview
  START_APPLICATION.md         - How to start
  FINAL_HANDOFF.md            - Complete guide

🧪 Testing:
  TESTING_GUIDE.md            - 34 test cases

🚀 Deployment:
  DEPLOYMENT_GUIDE.md         - Production setup

📖 Detailed:
  PHASE1_COMPLETE_SUMMARY.md  - Feature summary
  FRONTEND_COMPLETE.md        - Frontend docs
  BACKEND_READY.md            - Backend docs
  PROJECT_VISUAL_SUMMARY.md   - Visual diagrams
```

## 🎯 Quick Tests

```
✅ Login Flow:
  1. Go to /login
  2. Use: admin@nigerianlms.com / Admin123!@#
  3. Should redirect to /system-admin

✅ Registration:
  1. Go to /register-school
  2. Fill form with test data
  3. Should create school & redirect

✅ Protected Routes:
  1. Logout
  2. Try to access /dashboard
  3. Should redirect to /login
```

## 🔐 Environment Variables

```
Backend (.env):
  DATABASE_URL=postgresql://...
  SUPABASE_URL=https://...
  SUPABASE_KEY=...
  JWT_SECRET=your-secret
  ALLOWED_ORIGINS=http://localhost:3000

Frontend (.env.local):
  NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## 🏗️ Tech Stack

```
Backend:    Python 3.13 + FastAPI
Frontend:   TypeScript + Next.js 15
Database:   PostgreSQL (Supabase)
Styling:    Tailwind CSS
Auth:       JWT + bcrypt
```

## 📊 Database

```
Tables:
  users              (2 records)
  organizations      (1 record)
  subscription_plans (4 records)
  campuses           (1 record)
  system_admins      (1 record)
```

## ⚡ Performance

```
Backend:    < 200ms response time
Frontend:   < 2s initial load
Build:      ~6 seconds
Hot Reload: < 1 second
```

## 🎨 UI Colors

```
Primary:   Blue (#2563EB)
Success:   Green (#10B981)
Warning:   Yellow (#F59E0B)
Error:     Red (#EF4444)
Neutral:   Gray (#6B7280)
```

## 🚨 Status Codes

```
200  ✅ Success
401  🔒 Unauthorized
403  🚫 Forbidden
404  ❓ Not Found
422  ⚠️  Validation Error
500  💥 Server Error
```

## 📱 Responsive Breakpoints

```
Mobile:   < 768px
Tablet:   768px - 1023px
Desktop:  1024px+
```

## 🎯 Phase 1 Features

```
✅ Authentication
✅ School registration
✅ System admin dashboard
✅ School admin dashboard
✅ User management
✅ Organization management
✅ Responsive design
✅ Error handling
```

## 🚧 Phase 2 (Planned)

```
⏳ Student management
⏳ Teacher management
⏳ Attendance tracking
⏳ Grading system
⏳ Report cards
⏳ Parent portal
⏳ Payment processing
```

## 💡 Pro Tips

```
✓ Keep both servers running during development
✓ Check browser console for errors
✓ Use React DevTools for debugging
✓ Monitor backend terminal for logs
✓ Test on multiple browsers
✓ Clear .next cache if issues occur
```

## 🔄 Git Commands

```bash
# Check status
git status

# Commit changes
git add .
git commit -m "Your message"

# Push to GitHub
git push origin main

# Create branch
git checkout -b feature-name
```

## 🎉 Success Checklist

```
✅ Backend running
✅ Frontend running
✅ Can login as system admin
✅ Can login as school admin
✅ Can register new school
✅ All pages accessible
✅ No console errors
✅ Responsive design works
```

---

**Print this for your desk! 📌**

**Version**: 1.0.0  
**Phase**: 1 MVP  
**Status**: Complete ✅
