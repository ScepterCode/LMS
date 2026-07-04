# 🚀 START SERVERS AND TEST - Step by Step

## ⚠️ **BACKEND IS NOT RUNNING**

The automated test failed because the backend server is not running on port 8000.

---

## 📋 **STEP-BY-STEP INSTRUCTIONS**

### **Step 1: Start Backend Server**

Open a **NEW PowerShell terminal** and run:

```powershell
cd c:\Users\DELL\Downloads\LMS\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Wait for this message:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

✅ **DO NOT CLOSE THIS TERMINAL** - Keep it running

---

### **Step 2: Start Frontend Server**

Open **ANOTHER NEW PowerShell terminal** and run:

```powershell
cd c:\Users\DELL\Downloads\LMS\frontend
npm run dev
```

**Wait for this message:**
```
✓ Ready in 3.2s
○ Local:   http://localhost:3000
```

✅ **DO NOT CLOSE THIS TERMINAL** - Keep it running

---

### **Step 3: Run Automated Tests**

Open a **THIRD PowerShell terminal** (or use the current one) and run:

```powershell
cd c:\Users\DELL\Downloads\LMS
python test_system.py
```

Press Enter when prompted, and the tests will run automatically.

---

## 🎯 **QUICK VERIFICATION (Before Testing)**

### Check Backend:
Open browser and go to: **http://localhost:8000/docs**

✅ You should see the API documentation (Swagger UI)

### Check Frontend:
Open browser and go to: **http://localhost:3000**

✅ You should see the login page

---

## 🔄 **IF SERVERS ARE ALREADY RUNNING**

If you already have the servers running in other terminals, just run:

```powershell
cd c:\Users\DELL\Downloads\LMS
python test_system.py
```

---

## 📊 **WHAT THE AUTOMATED TEST WILL CHECK**

The test script will automatically verify:

1. ✅ **Authentication** - Login with admin credentials
2. ✅ **Sessions** - List and create academic sessions (THE MAIN FIX)
3. ✅ **Classes** - List classes
4. ✅ **Subjects** - List subjects
5. ✅ **Students** - List and get student details
6. ✅ **Teachers** - List and get teacher details
7. ✅ **Parents** - List, get details, and check children links
8. ✅ **Grading** - List assessments and student grades
9. ✅ **Attendance** - Get attendance records
10. ✅ **Fees** - Get fee structures and payments
11. ✅ **Teacher Management** - Get grading schemes and assignments

---

## ✅ **EXPECTED RESULT**

After running the tests, you should see:

```
======================================================================
                          TEST SUMMARY                         
======================================================================

Total Tests:  30+
Passed:       28-30
Failed:       0-2
Pass Rate:    90-100%

🎉 ALL TESTS PASSED! System is fully functional.
```

---

## 🐛 **IF TESTS FAIL**

1. Check that both servers are running
2. Check for error messages in the backend terminal
3. Try clearing browser cookies
4. Restart both servers

---

## 🔍 **MANUAL TESTING (Alternative)**

If automated testing doesn't work, you can manually test by:

1. Opening http://localhost:3000 in browser
2. Login with: sarahchidiloveday@gmail.com / Admin123!
3. Follow the checklist in `MANUAL_TESTING_CHECKLIST.md`

---

## 💡 **NEXT STEPS**

1. ✅ Start backend server (Terminal 1)
2. ✅ Start frontend server (Terminal 2)
3. ✅ Run automated tests (Terminal 3)
4. ✅ Review test results
5. ✅ Report any failures

**Ready to start? Open those terminals and let's test! 🚀**
