# 🧪 Complete Testing Guide

## 📋 **WHAT TO TEST**

We need to test these recently fixed/implemented features:

1. ✅ **Session Creation** - The original 403/401 error issue
2. ✅ **Teacher Account Creation** - With username/password
3. ✅ **Parent Account Creation** - With username/password
4. ✅ **Parent-Student Linking** - Just fixed today

---

## 🚀 **HOW TO START TESTING**

### Option 1: Use the Quick Start Script (Recommended)
```powershell
cd c:\Users\DELL\Downloads\LMS
.\run_tests.ps1
```

This script will:
- Check if both servers are running
- Let you choose between automated or manual testing
- Open the browser and checklist for you

### Option 2: Manual Setup

#### Step 1: Start Backend
```powershell
cd c:\Users\DELL\Downloads\LMS\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Step 2: Start Frontend (New Terminal)
```powershell
cd c:\Users\DELL\Downloads\LMS\frontend
npm run dev
```

#### Step 3: Open Browser
Navigate to: http://localhost:3000

---

## 🤖 **AUTOMATED TESTING**

### Run Python Test Script
```powershell
cd c:\Users\DELL\Downloads\LMS
python test_system.py
```

This will:
- Test all major API endpoints
- Verify authentication
- Check CRUD operations
- Display pass/fail results

**What it tests:**
- ✅ Authentication & login
- ✅ Academic sessions (CREATE, READ, UPDATE, DELETE)
- ✅ Classes and subjects
- ✅ Students, teachers, parents
- ✅ Parent-student linking
- ✅ Grading system
- ✅ Attendance records
- ✅ Fee management
- ✅ Teacher management features

---

## 👤 **MANUAL TESTING**

### Follow the Checklist
Open and follow: `MANUAL_TESTING_CHECKLIST.md`

### Login Credentials
```
Email: sarahchidiloveday@gmail.com
Password: Admin123!
```

### Critical Tests to Perform:

#### 1. Session Creation Test ⭐ (THE MAIN ISSUE)
1. Login to the system
2. Go to "Academic" page
3. Click "Add New Session"
4. Fill in session details:
   - Name: `2024/2025 Test`
   - Start Date: `2024-09-01`
   - End Date: `2025-08-31`
5. Click "Create Session"
6. **EXPECTED**: Session created without 403/401 errors
7. **CHECK**: Open browser console (F12) - no red errors

#### 2. Teacher Account Creation Test ⭐
1. Go to "Teachers" → "Add New Teacher"
2. Fill in teacher info INCLUDING:
   - User Email: `newteacher@test.com`
   - Password: `Teacher123!`
3. Click "Add Teacher"
4. **EXPECTED**: Teacher created with login account
5. **TEST LOGIN**: Logout and login as the new teacher
6. **EXPECTED**: Teacher can login successfully

#### 3. Parent Account Creation Test ⭐
1. Go to "Parents" → "Add New Parent"
2. Fill in parent info INCLUDING:
   - User Email: `newparent@test.com`
   - Password: `Parent123!`
3. Click "Add Parent"
4. **EXPECTED**: Parent created with login account
5. **TEST LOGIN**: Logout and login as the new parent
6. **EXPECTED**: Parent can login successfully

#### 4. Parent-Student Linking Test ⭐ (JUST FIXED)
1. Go to "Parents" → Click on any parent
2. Click "Link Student" button
3. **EXPECTED**: Modal opens with searchable student list
4. Select a student
5. Choose relationship (Father/Mother/Guardian)
6. Click "Link Student"
7. **EXPECTED**: Student appears in parent's children list
8. **EXPECTED**: No errors in console
9. **TEST UNLINK**: Click "Unlink" button
10. **EXPECTED**: Link removed successfully

---

## ✅ **WHAT SHOULD WORK**

### After All Fixes:
- ✅ Login with correct credentials → Dashboard
- ✅ Create sessions → No 403/401 errors
- ✅ Create teachers with user accounts → Can login
- ✅ Create parents with user accounts → Can login
- ✅ Link parents to students → Works via UI
- ✅ All pages load without errors
- ✅ Navigation works smoothly
- ✅ No cookie/authentication issues

---

## 🐛 **WHAT TO REPORT IF TESTS FAIL**

### For 403/401 Errors:
Take a screenshot and note:
1. What page you were on
2. What button you clicked
3. The exact error in console (F12)
4. Check: Backend logs (terminal running backend)

### For Login Issues:
1. Clear browser cookies (DevTools → Application → Clear storage)
2. Try again
3. If still fails, check backend logs

### For Linking Issues:
1. Open browser console (F12)
2. Try linking a student
3. Check for errors in console
4. Check backend terminal for error logs

---

## 📊 **EXPECTED TEST RESULTS**

### Automated Tests:
```
Total Tests:  30+
Passed:       28-30
Failed:       0-2
Pass Rate:    90-100%
```

### Manual Tests:
- All critical features (4) should work
- No console errors
- Smooth navigation
- Data displays correctly

---

## 🎯 **PRIORITY TESTING ORDER**

1. **HIGHEST PRIORITY** - Session Creation (original issue)
2. **HIGH** - Teacher account creation
3. **HIGH** - Parent account creation
4. **HIGH** - Parent-student linking
5. **MEDIUM** - Other CRUD operations
6. **LOW** - UI/UX issues

---

## 💡 **TESTING TIPS**

### Browser Console
Always keep F12 open to see:
- Network requests (403/401 errors)
- Console errors (red text)
- Cookie information

### Multiple Users
Test with different roles:
1. Admin (full access)
2. Teacher (limited access)
3. Parent (view own children only)

### Clean State
- Clear cookies between role tests
- Use incognito mode for multi-user testing
- Refresh page after each major operation

---

## 📝 **TEST REPORT TEMPLATE**

After testing, document your findings:

```markdown
# Test Report - [Date]

## Environment
- Backend: Running ✓ / Not Running ✗
- Frontend: Running ✓ / Not Running ✗
- Browser: Chrome/Edge/Firefox
- OS: Windows

## Test Results

### 1. Session Creation
- Status: PASS ✓ / FAIL ✗
- Notes: 

### 2. Teacher Account Creation
- Status: PASS ✓ / FAIL ✗
- Notes:

### 3. Parent Account Creation
- Status: PASS ✓ / FAIL ✗
- Notes:

### 4. Parent-Student Linking
- Status: PASS ✓ / FAIL ✗
- Notes:

## Issues Found
1. [Issue description]
   - Severity: Critical/High/Medium/Low
   - Steps to reproduce:
   - Error message:
   - Screenshot: [attach]

## Overall Result
- System Status: READY / NEEDS FIXES
- Production Ready: YES / NO
```

---

## 🔥 **QUICK TESTING (5 Minutes)**

If you only have 5 minutes, test these:

1. **Login** - Does it work? ✓
2. **Create Session** - Any 403/401? ✓
3. **Link Parent-Student** - Does modal open? ✓
4. **Check Console** - Any red errors? ✓

If all 4 pass → System is working! 🎉

---

## 📞 **NEED HELP?**

If you encounter issues:
1. Check backend terminal for errors
2. Check browser console (F12)
3. Clear cookies and try again
4. Restart both servers
5. Report the issue with:
   - Screenshot
   - Console errors
   - Backend logs
   - Steps to reproduce

---

## ✅ **COMPLETION CHECKLIST**

- [ ] Both servers running
- [ ] Automated tests run (optional)
- [ ] Manual critical tests completed
- [ ] All 4 priority features tested
- [ ] No major errors found
- [ ] Test report created (if issues found)
- [ ] System status: READY / NEEDS ATTENTION

---

## 🎉 **SUCCESS CRITERIA**

System is READY if:
- ✅ Login works
- ✅ Session creation works (no 403)
- ✅ Teacher/parent accounts can be created
- ✅ Parent-student linking works
- ✅ No console errors during normal use
- ✅ All pages load correctly

**If all criteria met → 🚀 SYSTEM IS PRODUCTION READY!**
