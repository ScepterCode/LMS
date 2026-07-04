# 📋 Manual Testing Checklist

## ✅ How to Use This Checklist
- Open the application in your browser: http://localhost:3000
- Follow each test step below
- Check ✓ when a test passes
- Mark ✗ if a test fails (note the error)

---

## 🔐 **TEST 1: AUTHENTICATION**

### Login Test
- [ ] Navigate to http://localhost:3000
- [ ] You should see the login page
- [ ] Enter email: `sarahchidiloveday@gmail.com`
- [ ] Enter password: `Admin123!`
- [ ] Click "Login"
- [ ] ✅ **PASS**: You should be redirected to the dashboard
- [ ] ✅ **PASS**: You should see "Sarah Chidi Loveday" in the sidebar/header

### Session Persistence
- [ ] Refresh the page (F5)
- [ ] ✅ **PASS**: You should remain logged in (not redirected to login)

---

## 📚 **TEST 2: SESSIONS (THE ORIGINAL ISSUE)**

### Navigate to Sessions
- [ ] Click "Academic" in the sidebar
- [ ] You should see the Academic Management page
- [ ] ✅ **PASS**: No errors in browser console (F12)

### View Existing Sessions
- [ ] Look at the "Academic Sessions" table
- [ ] ✅ **PASS**: You should see existing sessions listed

### Create New Session ⭐ **(MAIN FIX TO TEST)**
- [ ] Click "Add New Session" button
- [ ] Fill in:
  - Name: `2024/2025 Academic Year`
  - Start Date: `2024-09-01`
  - End Date: `2025-08-31`
  - Check "Set as current session" (optional)
- [ ] Click "Create Session"
- [ ] ✅ **PASS**: Session should be created successfully
- [ ] ✅ **PASS**: No 403/401 errors in console
- [ ] ✅ **PASS**: New session appears in the table
- [ ] ❌ **FAIL**: If you see 403/401 errors, **report this immediately**

---

## 👨‍🎓 **TEST 3: STUDENT MANAGEMENT**

### View Students
- [ ] Click "Students" in sidebar
- [ ] ✅ **PASS**: Students list loads

### View Student Details
- [ ] Click on any student
- [ ] ✅ **PASS**: Student details page loads
- [ ] ✅ **PASS**: You see student info, guardians, enrollments

---

## 👨‍🏫 **TEST 4: TEACHER ACCOUNT CREATION** ⭐

### Create Teacher with User Account
- [ ] Click "Teachers" in sidebar
- [ ] Click "Add New Teacher"
- [ ] Fill in teacher information:
  - Employee Number: `TCH001` (auto-generated)
  - First Name: `Test`
  - Last Name: `Teacher`
  - Email: `teacher.test@school.com`
  - Phone: `08012345678`
  - Qualification: `B.Ed`
  - Specialization: `Mathematics`
  - **User Email: `testteacher@school.com`**
  - **Password: `Teacher123!`**
  - **Confirm Password: `Teacher123!`**
- [ ] Click "Add Teacher"
- [ ] ✅ **PASS**: Teacher created successfully
- [ ] ✅ **PASS**: Success message appears

### Test Teacher Login
- [ ] Logout (top right corner)
- [ ] Try to login with:
  - Email: `testteacher@school.com`
  - Password: `Teacher123!`
- [ ] ✅ **PASS**: Teacher can login
- [ ] ✅ **PASS**: Teacher sees limited access (teacher dashboard)
- [ ] Logout and login back as admin

---

## 👪 **TEST 5: PARENT ACCOUNT CREATION** ⭐

### Create Parent with User Account
- [ ] Click "Parents" in sidebar
- [ ] Click "Add New Parent"
- [ ] Fill in parent information:
  - Title: `Mr.`
  - First Name: `Test`
  - Last Name: `Parent`
  - Email: `parent.test@email.com`
  - Phone: `08098765432`
  - Occupation: `Engineer`
  - Address: `123 Test Street`
  - **User Email: `testparent@email.com`**
  - **Password: `Parent123!`**
  - **Confirm Password: `Parent123!`**
- [ ] Click "Add Parent"
- [ ] ✅ **PASS**: Parent created successfully
- [ ] ✅ **PASS**: Success message appears
- [ ] ✅ **PASS**: Parent appears in the list

### Test Parent Login
- [ ] Logout
- [ ] Try to login with:
  - Email: `testparent@email.com`
  - Password: `Parent123!`
- [ ] ✅ **PASS**: Parent can login
- [ ] ✅ **PASS**: Parent sees parent-specific dashboard
- [ ] Logout and login back as admin

---

## 🔗 **TEST 6: PARENT-STUDENT LINKING** ⭐ **(JUST FIXED)**

### Link Parent to Student
- [ ] Login as admin
- [ ] Click "Parents" in sidebar
- [ ] Click on the test parent you just created
- [ ] You should see "Linked Children" section
- [ ] Click "Link Student" button
- [ ] ✅ **PASS**: Modal opens with student list

### Select and Link Student
- [ ] Use the search box to find a student
- [ ] ✅ **PASS**: Search filters students
- [ ] Select a student (radio button)
- [ ] Choose relationship: `Father` or `Mother`
- [ ] Check "Set as primary guardian" (optional)
- [ ] Click "Link Student"
- [ ] ✅ **PASS**: Modal closes
- [ ] ✅ **PASS**: Student appears in parent's children list
- [ ] ✅ **PASS**: No errors in console

### Verify Link
- [ ] Go to "Students" → click on the linked student
- [ ] Scroll to "Guardians" section
- [ ] ✅ **PASS**: Parent appears as guardian

### Unlink Student
- [ ] Go back to parent details
- [ ] Click "Unlink" next to the student
- [ ] Confirm unlinking
- [ ] ✅ **PASS**: Student removed from list
- [ ] ✅ **PASS**: No errors

---

## 📝 **TEST 7: GRADING SYSTEM**

### View Assessments
- [ ] Click "Grading" → "Assessments"
- [ ] ✅ **PASS**: Assessment list loads

### View Grade Entry
- [ ] Click "Grading" → "Grade Entry"
- [ ] ✅ **PASS**: Grade entry page loads

---

## 📅 **TEST 8: ATTENDANCE**

### View Attendance
- [ ] Click "Attendance" → "Mark Attendance"
- [ ] ✅ **PASS**: Attendance marking page loads

### View Reports
- [ ] Click "Attendance" → "Reports"
- [ ] ✅ **PASS**: Reports page loads

---

## 💰 **TEST 9: FEE MANAGEMENT**

### View Fee Dashboard
- [ ] Click "Fees" in sidebar
- [ ] ✅ **PASS**: Fee dashboard loads

### View Payments
- [ ] Click "Fees" → "Payments"
- [ ] ✅ **PASS**: Payments page loads

---

## 🎓 **TEST 10: TEACHER MANAGEMENT (PHASE 4)**

### View Grading Schemes
- [ ] Click "Teacher Management" → "Grading Schemes"
- [ ] ✅ **PASS**: Grading schemes page loads

### View Teacher Assignments
- [ ] Click "Teacher Management" → "Teacher Assignments"
- [ ] ✅ **PASS**: Assignments page loads

---

## 🔒 **TEST 11: PERMISSIONS**

### Test Access Control
- [ ] Logout as admin
- [ ] Login as teacher (the one you created)
- [ ] Try to access "Parents" page
- [ ] ✅ **PASS**: Should be redirected or see "No access"
- [ ] Logout and login back as admin

---

## 📊 **FINAL CHECKS**

### Browser Console
- [ ] Open DevTools (F12)
- [ ] Check Console tab
- [ ] ✅ **PASS**: No red errors
- [ ] ✅ **PASS**: No 403/401 authentication errors
- [ ] ✅ **PASS**: No "Cookie" warnings

### Cookies
- [ ] Open DevTools → Application → Cookies
- [ ] Check cookies for localhost:3000
- [ ] ✅ **PASS**: You should see authentication cookies

### Logout
- [ ] Click logout button
- [ ] ✅ **PASS**: Redirected to login page
- [ ] ✅ **PASS**: Cannot access dashboard without logging in

---

## ✅ **TEST RESULTS SUMMARY**

### Critical Tests (Must Pass) ⭐
- [ ] Login works
- [ ] Session creation works (no 403/401)
- [ ] Teacher account creation works
- [ ] Parent account creation works
- [ ] Parent-student linking works

### Secondary Tests
- [ ] All pages load without errors
- [ ] Navigation works
- [ ] Data displays correctly
- [ ] Permissions enforced

---

## 🐛 **IF TESTS FAIL**

### For 403/401 Errors:
1. Check backend console for errors
2. Verify cookies in DevTools
3. Clear browser cookies and try again
4. Check if backend is running on localhost:8000

### For Other Errors:
1. Check browser console (F12)
2. Check backend logs
3. Note the exact error message
4. Report the error with screenshots

---

## 📝 **NOTES**

Use this space to write down any issues you find:

```
Issue 1:
- Feature:
- Error:
- Steps to reproduce:

Issue 2:
- Feature:
- Error:
- Steps to reproduce:
```

---

## ✅ **COMPLETION**

- [ ] All critical tests passed
- [ ] No major errors found
- [ ] System is ready for production

**Tested by:** _________________  
**Date:** _________________  
**Time:** _________________  
**Result:** ☐ Pass  ☐ Fail (with notes)
