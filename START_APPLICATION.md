# 🚀 START APPLICATION - Quick Guide

## Prerequisites

- ✅ Backend setup complete
- ✅ Frontend setup complete
- ✅ Database configured
- ✅ Dependencies installed

---

## Start Backend (Terminal 1)

### Windows (PowerShell/CMD)

```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Expected Output

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Verify Backend

Open browser: http://127.0.0.1:8000

Should see:
```json
{
  "message": "Welcome to Nigerian LMS API",
  "version": "1.0.0",
  "status": "active"
}
```

---

## Start Frontend (Terminal 2)

### Windows (PowerShell/CMD)

```powershell
cd frontend
npm run dev
```

### Expected Output

```
  ▲ Next.js 15.x.x
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000

 ✓ Starting...
 ✓ Ready in 2.5s
```

### Verify Frontend

Open browser: http://localhost:3000

Should see the landing page!

---

## 🧪 Quick Test

### Test 1: System Admin Login

1. Go to http://localhost:3000/login
2. Login with:
   - Email: `admin@nigerianlms.com`
   - Password: `Admin123!@#`
3. Should redirect to `/system-admin`
4. Should see platform analytics

### Test 2: School Admin Login

1. Logout from system admin
2. Login with:
   - Email: `admin@demo-school.com`
   - Password: `Admin123!@#`
3. Should redirect to `/dashboard`
4. Should see school dashboard

### Test 3: Register New School

1. Logout
2. Go to http://localhost:3000/register-school
3. Fill in form with test data
4. Should successfully register
5. Should redirect to login
6. Login with new credentials
7. Should see trial dashboard

---

## 📍 URLs Reference

### Frontend
- **Home**: http://localhost:3000
- **Login**: http://localhost:3000/login
- **Register**: http://localhost:3000/register-school
- **System Admin**: http://localhost:3000/system-admin
- **School Dashboard**: http://localhost:3000/dashboard

### Backend
- **API Root**: http://127.0.0.1:8000
- **Health Check**: http://127.0.0.1:8000/health
- **API Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## 🔑 Demo Accounts

### System Admin
```
Email: admin@nigerianlms.com
Password: Admin123!@#
```

### School Admin (Demo School)
```
Email: admin@demo-school.com
Password: Admin123!@#
```

---

## 🐛 Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Verify virtual environment is activated
- Check `.env` file exists in `backend/`
- Run `pip install -r requirements.txt`

### Frontend won't start
- Check if port 3000 is already in use
- Run `npm install` in `frontend/`
- Check `.env.local` exists in `frontend/`
- Clear `.next` folder and retry

### CORS errors
- Verify backend `ALLOWED_ORIGINS` includes `http://localhost:3000`
- Check both servers are running
- Clear browser cache

### Login not working
- Check backend is running
- Check API URL in `.env.local`
- Open browser console for errors
- Verify credentials are correct

### Database errors
- Check Supabase credentials in `backend/.env`
- Verify database schema is applied
- Check internet connection

---

## 🎯 Success Checklist

- [ ] Backend running on http://127.0.0.1:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Can access landing page
- [ ] Can login as system admin
- [ ] Can login as school admin
- [ ] Can register new school
- [ ] No errors in console
- [ ] All navigation working

---

## 🔄 Restart Application

### Stop Servers
Press `CTRL+C` in both terminals

### Restart Backend
```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Restart Frontend
```powershell
cd frontend
npm run dev
```

---

## 📱 Access from Other Devices

### Find Your Local IP

**Windows (PowerShell):**
```powershell
ipconfig
```
Look for "IPv4 Address" (e.g., 192.168.1.100)

### Update Backend CORS

Add your IP to `backend/.env`:
```env
ALLOWED_ORIGINS=http://localhost:3000,http://192.168.1.100:3000
```

### Access from Phone/Tablet

Open browser on device:
```
http://192.168.1.100:3000
```

---

## 💻 Development Workflow

1. **Start both servers** (backend + frontend)
2. **Make changes** to code
3. **Changes auto-reload** (hot reload enabled)
4. **Test in browser**
5. **Check console** for errors
6. **Commit changes** when working

---

## 🎉 You're Ready!

Both backend and frontend are running successfully!

**What to do next:**
1. ✅ Test all pages and features
2. ✅ Try registering a new school
3. ✅ Explore both dashboards
4. ✅ Test on mobile devices
5. ✅ Invite others to test
6. ✅ Gather feedback
7. ✅ Plan Phase 2 features

---

**Application Status**: ✅ RUNNING  
**Phase 1 MVP**: ✅ COMPLETE  
**Ready for**: Testing & Feedback
