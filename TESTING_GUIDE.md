# 🧪 Testing Guide - Phase 1 MVP

Complete testing guide for Nigerian LMS Phase 1 features.

---

## 📋 Pre-Test Checklist

- [ ] Backend running on http://127.0.0.1:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Database configured and connected
- [ ] Browser console open (F12)
- [ ] Network tab visible

---

## 🔐 Test Suite 1: Authentication

### Test 1.1: System Admin Login

**Steps:**
1. Navigate to http://localhost:3000/login
2. Enter email: `admin@nigerianlms.com`
3. Enter password: `Admin123!@#`
4. Click "Sign In"

**Expected Results:**
- ✅ Login successful
- ✅ Redirected to `/system-admin`
- ✅ User name displayed in nav
- ✅ No console errors

**Actual Results:** _________

---

### Test 1.2: School Admin Login

**Steps:**
1. Logout from system admin
2. Navigate to http://localhost:3000/login
3. Enter email: `admin@demo-school.com`
4. Enter password: `Admin123!@#`
5. Click "Sign In"

**Expected Results:**
- ✅ Login successful
- ✅ Redirected to `/dashboard`
- ✅ Demo School name visible
- ✅ Trial period warning shown
- ✅ No console errors

**Actual Results:** _________

---

### Test 1.3: Invalid Credentials

**Steps:**
1. Logout
2. Navigate to http://localhost:3000/login
3. Enter email: `wrong@email.com`
4. Enter password: `wrongpassword`
5. Click "Sign In"

**Expected Results:**
- ❌ Login failed
- ✅ Error message displayed: "Invalid email or password"
- ✅ No redirect
- ✅ Form still visible

**Actual Results:** _________

---

### Test 1.4: Logout

**Steps:**
1. Login as any user
2. Click "Logout" button

**Expected Results:**
- ✅ Logout successful
- ✅ Redirected to `/login`
- ✅ Cannot access protected pages
- ✅ Cookie cleared

**Actual Results:** _________

---

### Test 1.5: Protected Routes

**Steps:**
1. Logout (ensure not authenticated)
2. Try to access http://localhost:3000/dashboard directly
3. Try to access http://localhost:3000/system-admin directly

**Expected Results:**
- ✅ Automatically redirected to `/login`
- ✅ No access to protected content
- ✅ After login, can access appropriate dashboard

**Actual Results:** _________

---

## 📝 Test Suite 2: School Registration

### Test 2.1: Valid School Registration

**Steps:**
1. Navigate to http://localhost:3000/register-school
2. Fill in school information:
   - School Name: "Test High School"
   - School Email: "info@testhighschool.com"
   - School Phone: "+234 800 111 2222"
   - School Address: "123 Test Street, Lagos"
3. Fill in admin information:
   - Full Name: "John Doe"
   - Email Address: "admin@testhighschool.com"
   - Password: "TestPass123!@#"
   - Phone Number: "+234 800 111 3333"
4. Click "Start Free Trial"

**Expected Results:**
- ✅ Registration successful
- ✅ Success message displayed
- ✅ Redirected to login page after 3 seconds
- ✅ Can login with new credentials
- ✅ New school appears in system admin dashboard

**Actual Results:** _________

---

### Test 2.2: Duplicate Email

**Steps:**
1. Try to register with existing email (e.g., "admin@demo-school.com")

**Expected Results:**
- ❌ Registration failed
- ✅ Error message: "email already exists"
- ✅ Form still visible
- ✅ Can correct and retry

**Actual Results:** _________

---

### Test 2.3: Weak Password

**Steps:**
1. Try to register with password: "weak"

**Expected Results:**
- ❌ Form validation error
- ✅ Password requirements shown
- ✅ Cannot submit form

**Actual Results:** _________

---

### Test 2.4: Form Validation

**Steps:**
1. Try to submit empty form
2. Try to submit with only school name
3. Try to submit without admin email

**Expected Results:**
- ❌ Cannot submit incomplete form
- ✅ Required fields highlighted
- ✅ Browser validation messages

**Actual Results:** _________

---

## 🏢 Test Suite 3: System Admin Dashboard

### Test 3.1: Platform Analytics

**Steps:**
1. Login as system admin
2. View dashboard at `/system-admin`

**Expected Results:**
- ✅ Total Schools card shows correct count
- ✅ Total Users card shows correct count
- ✅ Trial Schools card shows count
- ✅ Suspended Schools card shows count
- ✅ Numbers match database state

**Actual Results:** _________

---

### Test 3.2: Organizations List

**Steps:**
1. On system admin dashboard
2. Scroll to "Recent Organizations" table

**Expected Results:**
- ✅ Table displays all organizations
- ✅ Shows school name, email, status, plan
- ✅ Status badges colored correctly
  - Green for active
  - Yellow for trial
  - Red for suspended
- ✅ Created date formatted correctly

**Actual Results:** _________

---

### Test 3.3: Multiple Organizations

**Steps:**
1. Register 2-3 new schools
2. View system admin dashboard
3. Check if all appear in list

**Expected Results:**
- ✅ All schools visible
- ✅ Count updated
- ✅ All in trial status
- ✅ Sorted by recent first

**Actual Results:** _________

---

## 🏫 Test Suite 4: School Dashboard

### Test 4.1: Organization Details

**Steps:**
1. Login as school admin
2. View dashboard at `/dashboard`

**Expected Results:**
- ✅ School name displayed correctly
- ✅ Welcome message shows admin name
- ✅ Organization info section shows:
  - School name
  - Email
  - Plan
  - Status
- ✅ Statistics show user counts

**Actual Results:** _________

---

### Test 4.2: Trial Warning

**Steps:**
1. Login as school admin (trial account)
2. Check top of dashboard

**Expected Results:**
- ✅ Yellow warning banner visible
- ✅ Shows days remaining (should be ~14)
- ✅ Message about upgrading

**Actual Results:** _________

---

### Test 4.3: Navigation

**Steps:**
1. On school dashboard
2. Click "Students" link
3. Click "Teachers" link
4. Click "Dashboard" link

**Expected Results:**
- ✅ Students page shows "Coming in Phase 2"
- ✅ Teachers page shows "Coming in Phase 2"
- ✅ Dashboard link returns to main dashboard
- ✅ All navigation items highlighted correctly

**Actual Results:** _________

---

### Test 4.4: Quick Actions

**Steps:**
1. On school dashboard
2. Review "Quick Actions" card

**Expected Results:**
- ✅ Shows "Manage Students" (placeholder)
- ✅ Shows "Manage Teachers" (placeholder)
- ✅ Shows "Attendance (Coming Soon)" (disabled)
- ✅ Active items are clickable

**Actual Results:** _________

---

## 🌐 Test Suite 5: UI/UX

### Test 5.1: Responsive Design

**Steps:**
1. Open application on desktop
2. Resize browser to tablet size (768px)
3. Resize to mobile size (375px)
4. Test all pages at each size

**Expected Results:**
- ✅ Desktop: Full layout visible
- ✅ Tablet: Layout adapts gracefully
- ✅ Mobile: Single column, hamburger menu if needed
- ✅ No horizontal scrolling
- ✅ All buttons accessible
- ✅ Text readable at all sizes

**Actual Results:** _________

---

### Test 5.2: Loading States

**Steps:**
1. Login and observe
2. Navigate between pages
3. Watch for loading indicators

**Expected Results:**
- ✅ Spinner shows during login
- ✅ Loading state on dashboard data fetch
- ✅ No flash of wrong content
- ✅ Smooth transitions

**Actual Results:** _________

---

### Test 5.3: Error Messages

**Steps:**
1. Test various error scenarios
2. Check error message display

**Expected Results:**
- ✅ Errors shown in red
- ✅ Error messages clear and helpful
- ✅ Errors dismissible or timeout
- ✅ Forms remain usable after errors

**Actual Results:** _________

---

### Test 5.4: Success Messages

**Steps:**
1. Complete successful actions (login, registration)
2. Observe success feedback

**Expected Results:**
- ✅ Success messages shown in green
- ✅ Clear confirmation of action
- ✅ Auto-dismiss after delay
- ✅ Proper redirect after success

**Actual Results:** _________

---

## 🔄 Test Suite 6: End-to-End Workflows

### Test 6.1: Complete User Journey (New School)

**Steps:**
1. Navigate to landing page
2. Click "Register School"
3. Complete registration form
4. Confirm success message
5. Login with new credentials
6. Explore school dashboard
7. Check trial status
8. Click around navigation
9. Logout

**Expected Results:**
- ✅ All steps complete without errors
- ✅ Smooth flow from start to finish
- ✅ All data persists correctly
- ✅ Can repeat process

**Actual Results:** _________

---

### Test 6.2: System Admin Workflow

**Steps:**
1. Login as system admin
2. View platform analytics
3. Browse organizations list
4. Check subscription plans
5. Monitor user counts
6. Logout

**Expected Results:**
- ✅ All data loads correctly
- ✅ No broken links
- ✅ Fast page loads
- ✅ Accurate statistics

**Actual Results:** _________

---

## 🚀 Test Suite 7: Performance

### Test 7.1: Page Load Speed

**Steps:**
1. Open Network tab in DevTools
2. Navigate to various pages
3. Note load times

**Expected Results:**
- ✅ Landing page: < 2 seconds
- ✅ Login page: < 1 second
- ✅ Dashboard: < 2 seconds
- ✅ API calls: < 500ms

**Actual Results:** _________

---

### Test 7.2: Multiple Tabs

**Steps:**
1. Open application in 2-3 browser tabs
2. Login in one tab
3. Check if logged in on other tabs

**Expected Results:**
- ✅ All tabs share login state
- ✅ Logout affects all tabs
- ✅ No conflicts or errors

**Actual Results:** _________

---

## 🔒 Test Suite 8: Security

### Test 8.1: Cookie Security

**Steps:**
1. Login successfully
2. Open DevTools → Application → Cookies
3. Inspect the auth cookie

**Expected Results:**
- ✅ Cookie is HttpOnly
- ✅ Cookie has expiration
- ✅ Cookie cleared on logout
- ✅ Cannot access from JavaScript

**Actual Results:** _________

---

### Test 8.2: Role-Based Access

**Steps:**
1. Login as school admin
2. Try to access `/system-admin` URL directly
3. Login as system admin
4. Try to access another school's data

**Expected Results:**
- ✅ School admin cannot access system admin
- ✅ Proper permission errors
- ✅ Redirected appropriately
- ✅ No unauthorized data visible

**Actual Results:** _________

---

## 📊 Test Summary

### Total Tests: 34

Fill in after testing:

- ✅ Passed: _____
- ❌ Failed: _____
- ⚠️ Issues: _____

### Critical Issues Found:
1. _____________________
2. _____________________
3. _____________________

### Minor Issues Found:
1. _____________________
2. _____________________
3. _____________________

### Recommendations:
1. _____________________
2. _____________________
3. _____________________

---

## 🎯 Sign-Off

**Tested By:** _____________________  
**Date:** _____________________  
**Browser:** _____________________  
**OS:** _____________________  

**Overall Status:** ☐ Pass  ☐ Pass with Issues  ☐ Fail

**Ready for Production:** ☐ Yes  ☐ No  ☐ Needs Work

**Notes:**
_____________________________________________
_____________________________________________
_____________________________________________

---

## 🔄 Regression Testing

When making changes, rerun:
- Test Suite 1 (Authentication) - Always
- Test Suite 6 (End-to-End) - Always
- Other suites as relevant to changes

---

**Testing Guide Version:** 1.0.0  
**Last Updated:** June 4, 2026  
**Phase:** 1 MVP
