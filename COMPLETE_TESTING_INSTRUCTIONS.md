# 🚀 COMPLETE TESTING INSTRUCTIONS

## ⚡ **FASTEST WAY TO START & TEST (3 Options)**

---

## **OPTION 1: Automatic Startup Script** ⭐ (EASIEST)

### Step 1: Run the Startup Script
```powershell
cd c:\Users\DELL\Downloads\LMS
.\START_BOTH_SERVERS.ps1
```

This will:
- ✅ Open 2 new terminal windows
- ✅ Start backend automatically
- ✅ Start frontend automatically
- ✅ Show you what to do next

### Step 2: Wait for Servers to Start

**Backend Terminal** (Window 1):
Wait for this message:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Frontend Terminal** (Window 2):
Wait for this message:
```
✓ Ready in 3s
○ Local: http://localhost:3000
```

### Step 3: Run Tests
```powershell
cd c:\Users\DELL\Downloads\LMS
python test_system.py
```

Press Enter when prompted, then watch the tests run!

---

## **OPTION 2: Manual Startup** (Step-by-Step)

### Terminal 1 - Backend:
```powershell
cd c:\Users\DELL\Downloads\LMS\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Frontend:
```powershell
cd c:\Users\DELL\Downloads\LMS\frontend
npm run dev
```

### Terminal 3 - Run Tests:
```powershell
cd c:\Users\DELL\Downloads\LMS
python test_system.py
```

---

## **OPTION 3: Use Existing start-dev.ps1 Script**

If you already have the servers started, skip to testing:

```powershell
cd c:\Users\DELL\Downloads\LMS
python test_system.py
```

---

## ✅ **VERIFY SERVERS ARE RUNNING**

### Check Backend:
Open browser: **http://localhost:8000/docs**
- ✅ Should see Swagger API documentation

### Check Frontend:
Open browser: **http://localhost:3000**
- ✅ Should see the login page

---

## 🧪 **RUNNING THE AUTOMATED TESTS**

Once both servers are running:

```powershell
cd c:\Users\DELL\Downloads\LMS
python test_system.py
```

**You'll see:**
1. Prompt to press Enter
2. Test sections running (Authentication, Sessions, Students, etc.)
3. Green ✓ for passing tests
4. Red ✗ for failing tests
5. Final summary with pass rate

---

## 📊 **WHAT TO EXPECT**

### **Perfect Result:**
```
======================================================================
                          TEST SUMMARY                         
======================================================================

Total Tests:  30
Passed:       30
Failed:       0
Pass Rate:    100%

🎉 ALL TESTS PASSED! System is fully functional.
```

### **Good Result:**
```
Total Tests:  30
Passed:       28
Failed:       2
Pass Rate:    93.3%

✅ System is working! Minor issues may exist.
```

### **Acceptable Result:**
```
Total Tests:  30
Passed:       27
Failed:       3
Pass Rate:    90%

⚠️ Some tests failed. Review failed tests.
```

---

## 🎯 **KEY TESTS TO CHECK**

### **CRITICAL** (Must Pass):
- ✅ Admin Login
- ✅ **Create Session** ← YOUR MAIN FIX (403/401)
- ✅ List Students/Teachers/Parents
- ✅ **Get Parent's Children** ← JUST FIXED TODAY

### **IMPORTANT** (Should Pass):
- List Classes
- List Subjects
- Get Student Details
- Get Teacher Details

### **NICE TO HAVE** (Can show "Found 0"):
- List Assessments (may be empty)
- Get Attendance Records (may be empty)
- Get Fee Structures (may be empty)

---

## 🐛 **TROUBLESHOOTING**

### **If Backend Won't Start:**
```powershell
# Check if port 8000 is already in use
netstat -ano | findstr "8000"

# If something is using it, kill the process or use different port
# Then try starting again
```

### **If Frontend Won't Start:**
```powershell
# Make sure you're in the frontend directory
cd c:\Users\DELL\Downloads\LMS\frontend

# Install dependencies if needed
npm install

# Then try starting
npm run dev
```

### **If Tests Show Connection Errors:**
1. Make sure both servers are running
2. Check backend terminal for errors
3. Check frontend terminal for errors
4. Try opening http://localhost:8000/docs in browser
5. Try opening http://localhost:3000 in browser

### **If Tests Fail with 403/401:**
1. This was your original issue
2. Check if the fix is applied (cookie domain = localhost)
3. Clear browser cookies
4. Restart backend server

---

## 📝 **AFTER TESTING**

### **If All Tests Pass (90%+):**
1. ✅ System is ready!
2. ✅ Original issue (403/401) is fixed!
3. ✅ Parent-student linking works!
4. ✅ You can proceed to production!

### **If Some Tests Fail:**
1. Copy the failed test output
2. Share it with me
3. I'll help you fix it

### **If Many Tests Fail (<70%):**
1. Check backend logs for errors
2. Check database connection
3. Verify .env file has correct settings
4. Share the full test output

---

## 🎉 **MANUAL TESTING (Alternative)**

If you prefer to test manually through the UI:

1. **Open Browser:** http://localhost:3000
2. **Login:** sarahchidiloveday@gmail.com / Admin123!
3. **Test Session Creation:**
   - Go to Academic page
   - Click "Add New Session"
   - Fill in details and create
   - ✅ Should work without 403/401 errors
4. **Test Parent-Student Linking:**
   - Go to Parents page
   - Click on any parent
   - Click "Link Student" button
   - ✅ Modal should open with student list
   - Select student and link
   - ✅ Should work without errors

---

## 📚 **HELPFUL DOCUMENTS**

- `HOW_TO_INTERPRET_TEST_RESULTS.md` - Understand test output
- `QUICK_TEST_GUIDE.md` - 3-step quick guide
- `MANUAL_TESTING_CHECKLIST.md` - UI testing checklist
- `TEST_STATUS_REPORT.md` - Current status

---

## 💡 **QUICK COMMANDS SUMMARY**

```powershell
# Option 1: Auto-start servers
.\START_BOTH_SERVERS.ps1

# Option 2: Manual start
# Terminal 1:
cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2:
cd frontend && npm run dev

# Run tests (after servers start):
python test_system.py
```

---

## ✅ **CHECKLIST**

- [ ] Backend server started
- [ ] Frontend server started
- [ ] Can access http://localhost:8000/docs
- [ ] Can access http://localhost:3000
- [ ] Tests executed
- [ ] Test results reviewed
- [ ] Pass rate: ____%
- [ ] Critical tests passed: Yes/No
- [ ] System ready: Yes/No

---

## 🚀 **READY?**

Run this command now:
```powershell
.\START_BOTH_SERVERS.ps1
```

Then wait for both servers to start, and run:
```powershell
python test_system.py
```

**You've got this! Let's test your system! 💪**
