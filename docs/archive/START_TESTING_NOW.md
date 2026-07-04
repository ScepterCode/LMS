# 🚀 START TESTING - Quick Guide

## ⚡ **FASTEST WAY TO TEST (Right Now)**

### Step 1: Run the Test Script
```powershell
cd c:\Users\DELL\Downloads\LMS
.\run_tests.ps1
```

Select option **4** (Run all tests)

---

## 🎯 **OR: Test Manually in 3 Steps**

### 1. Make Sure Servers Are Running

**Terminal 1 - Backend:**
```powershell
cd c:\Users\DELL\Downloads\LMS\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd c:\Users\DELL\Downloads\LMS\frontend
npm run dev
```

### 2. Open Your Browser
Go to: **http://localhost:3000**

### 3. Follow These Tests

#### ✅ **TEST 1: Login**
- Email: `sarahchidiloveday@gmail.com`
- Password: `Admin123!`
- Click Login
- **PASS if:** You see the dashboard

#### ✅ **TEST 2: Create Session** (THE ORIGINAL ISSUE)
- Click "Academic" in sidebar
- Click "Add New Session"
- Fill in:
  - Name: `Test Session 2024`
  - Start Date: Pick any date
  - End Date: Pick a future date
- Click "Create Session"
- **PASS if:** Session created, NO 403/401 errors in console (press F12 to check)

#### ✅ **TEST 3: Create Teacher with Login**
- Click "Teachers" → "Add New Teacher"
- Fill required fields + these:
  - User Email: `test@teacher.com`
  - Password: `Teacher123!`
  - Confirm Password: `Teacher123!`
- Click "Add Teacher"
- **PASS if:** Teacher created successfully
- Logout and try login as teacher
- **PASS if:** Teacher can login

#### ✅ **TEST 4: Link Parent to Student** (JUST FIXED)
- Login as admin
- Click "Parents" → select any parent
- Click "Link Student" button
- **PASS if:** Modal opens with student list
- Select a student, choose relationship
- Click "Link Student"
- **PASS if:** Student appears in parent's children list, no errors

---

## 📊 **WHAT YOU'RE TESTING**

| Feature | Status | What We Fixed |
|---------|--------|---------------|
| Session Creation | 🔥 **MAIN ISSUE** | Fixed cookie domain mismatch (127.0.0.1 → localhost) |
| Teacher Accounts | ⭐ **NEW** | Added password field, automatic user creation |
| Parent Accounts | ⭐ **NEW** | Added password field, automatic user creation |
| Parent-Student Links | ⭐ **TODAY** | Fixed POST endpoint to accept JSON body |

---

## ✅ **PASS CRITERIA**

**All 4 tests above must:**
- Work without errors
- Complete successfully
- Show no 403/401 in browser console

---

## 🐛 **IF SOMETHING FAILS**

1. **Open browser console** (F12)
2. **Look for red errors**
3. **Check backend terminal** for error logs
4. **Note the exact error message**
5. **Tell me what failed**

---

## 📝 **DETAILED GUIDES AVAILABLE**

- `TESTING_GUIDE_COMPLETE.md` - Full guide with all instructions
- `MANUAL_TESTING_CHECKLIST.md` - Step-by-step checklist
- `test_system.py` - Automated API testing script
- `run_tests.ps1` - One-click test launcher

---

## 🎉 **EXPECTED RESULT**

After testing, you should be able to say:

✅ "I can login"  
✅ "I can create sessions without 403 errors"  
✅ "I can create teacher accounts with passwords"  
✅ "I can create parent accounts with passwords"  
✅ "I can link parents to students"  
✅ "The system works!"

---

## ⏰ **TIME ESTIMATE**

- **Quick Test** (4 tests above): 5-10 minutes
- **Automated Tests**: 2-3 minutes
- **Full Manual Testing**: 30-45 minutes

---

## 💪 **YOU'VE GOT THIS!**

The system is **100% implemented**. All features are in place. We just need to verify they work correctly through testing.

**Ready? Let's test! 🚀**

```powershell
# Run this command now:
.\run_tests.ps1
```
