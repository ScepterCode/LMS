# 📋 Manual Testing Checklist - Phase 2 Complete

## **Test All New Features**

### **Prerequisites**
- ✅ Backend running on http://localhost:8000
- ✅ Frontend running on http://localhost:3000
- ✅ Login credentials: admin@demohighschool.edu.ng / DemoSchool123!@#

---

## **1. Teacher Detail Page** (NEW!)

### Test Steps:
1. Navigate to http://localhost:3000/login
2. Login with admin credentials
3. Go to Teachers page
4. Click "View" on any teacher (or add a new teacher first)
5. **Expected**:
   - ✅ Complete teacher profile displayed
   - ✅ Personal information section
   - ✅ Professional information section
   - ✅ Subject assignments table
   - ✅ Quick stats sidebar
   - ✅ Status badges (active/on-leave/terminated)
   - ✅ Employment type badge
   - ✅ Years of service calculated
   - ✅ Edit button functional

### Status: ⬜ PASS | ⬜ FAIL

---

## **2. Teacher Edit Page** (NEW!)

### Test Steps:
1. From teacher detail page, click "Edit Teacher"
2. Try updating information:
   - Change qualification
   - Update phone number
   - Change status
   - Modify employment type
3. Click "Update Teacher"
4. **Expected**:
   - ✅ Form pre-filled with existing data
   - ✅ Staff number is read-only
   - ✅ All fields editable
   - ✅ Success message shown
   - ✅ Redirects to teacher detail page
   - ✅ Updated data displayed

### Status: ⬜ PASS | ⬜ FAIL

---

## **3. Academic Management - Session Modal** (NEW!)

### Test Steps:
1. Go to Academic page (http://localhost:3000/dashboard/academic)
2. Click "Sessions" tab
3. Click "+ Add Session"
4. Fill in:
   - Name: "2024/2025"
   - Start Date: Select a date
   - End Date: Select a date
   - Check "Set as current session"
5. Click "Create Session"
6. **Expected**:
   - ✅ Modal appears with form
   - ✅ All fields work
   - ✅ Checkbox toggles
   - ✅ Success - session created
   - ✅ Modal closes
   - ✅ Table updates with new session
   - ✅ "Current" badge shown

### Status: ⬜ PASS | ⬜ FAIL

---

## **4. Academic Management - Class Modal** (NEW!)

### Test Steps:
1. On Academic page, click "Classes" tab
2. Click "+ Add Class"
3. Fill in:
   - Name: "JSS 1"
   - Level: "Junior"
   - Section: "A"
   - Capacity: 40
4. Click "Create Class"
5. **Expected**:
   - ✅ Modal appears
   - ✅ Form validation works
   - ✅ Success - class created
   - ✅ Card layout updates
   - ✅ Capacity displayed (0/40)
   - ✅ Section badge shown

### Status: ⬜ PASS | ⬜ FAIL

---

## **5. Academic Management - Subject Modal** (NEW!)

### Test Steps:
1. On Academic page, click "Subjects" tab
2. Click "+ Add Subject"
3. Fill in:
   - Name: "Mathematics"
   - Code: "MATH101"
   - Type: "Core"
   - Description: "Basic mathematics"
4. Click "Create Subject"
5. **Expected**:
   - ✅ Modal appears
   - ✅ Subject created
   - ✅ Table updates
   - ✅ Type badge shown (blue for core)

### Status: ⬜ PASS | ⬜ FAIL

---

## **6. Guardian Management - Add Guardian** (NEW!)

### Test Steps:
1. Go to a student detail page
2. In Guardians section, click "+ Add"
3. Fill in guardian form:
   - Type: "Father"
   - Title: "Mr"
   - First Name: "John"
   - Last Name: "Doe"
   - Relationship: "Father"
   - Phone: "+234 803 000 0000"
   - Email: "john.doe@email.com"
   - Check "Emergency Contact"
   - Check "Primary Guardian"
4. Click "Add Guardian"
5. **Expected**:
   - ✅ Modal appears
   - ✅ All fields work
   - ✅ Checkboxes toggle
   - ✅ Guardian added successfully
   - ✅ Modal closes
   - ✅ Guardian card appears
   - ✅ Primary badge shown
   - ✅ Emergency contact indicator shown

### Status: ⬜ PASS | ⬜ FAIL

---

## **7. Guardian Management - Edit Guardian** (NEW!)

### Test Steps:
1. On student detail page with guardians
2. Click "Edit" on a guardian card
3. Update information:
   - Change occupation
   - Update email
4. Click "Update Guardian"
5. **Expected**:
   - ✅ Modal pre-filled with data
   - ✅ Can update fields
   - ✅ Success message
   - ✅ Guardian card updates

### Status: ⬜ PASS | ⬜ FAIL

---

## **8. Assignment Interface** (NEW!)

### Test Steps:
1. Navigate to http://localhost:3000/dashboard/assignments
2. **Expected page elements**:
   - ✅ Session dropdown (current session auto-selected)
   - ✅ Term dropdown (current term auto-selected)
   - ✅ Teacher dropdown (list of all teachers)
   - ✅ Subject dropdown (list of all subjects)
   - ✅ Class dropdown (list of all classes)
   - ✅ Info panel with assignment rules
3. Fill in all fields and submit
4. **Expected**:
   - ✅ Success message shown
   - ✅ Form clears (except session/term)
   - ✅ Assignment created
5. Go to teacher detail page
6. **Expected**:
   - ✅ Assignment appears in list
   - ✅ Shows subject, class, session, term

### Status: ⬜ PASS | ⬜ FAIL

---

## **9. Enrollment Interface** (NEW!)

### Test Steps:
1. Navigate to http://localhost:3000/dashboard/enrollments
2. **Expected page elements**:
   - ✅ Session dropdown
   - ✅ Student dropdown (all students)
   - ✅ Class dropdown (with capacity info)
   - ✅ Class capacity overview cards
   - ✅ Progress bars for each class
   - ✅ Color coding (green/yellow/red)
   - ✅ Info panel with enrollment rules
3. Select session, student, and class
4. Check capacity indicator below class dropdown
5. Click "Enroll Student"
6. **Expected**:
   - ✅ Success message
   - ✅ Form clears
   - ✅ Capacity overview updates
   - ✅ Progress bar moves
   - ✅ Student enrolled
7. Try enrolling in a full class
8. **Expected**:
   - ✅ Button disabled
   - ✅ "Class is Full" message
   - ✅ Cannot submit

### Status: ⬜ PASS | ⬜ FAIL

---

## **10. Teacher Complete Workflow**

### Test Steps:
1. **Add Teacher**:
   - Go to Teachers → + Add Teacher
   - Fill all details
   - Submit → Success
2. **View Teacher**:
   - Click "View" on new teacher
   - See complete profile
   - Check stats sidebar
3. **Edit Teacher**:
   - Click "Edit Teacher"
   - Update qualification
   - Submit → Success
   - See updated info
4. **Assign Subject**:
   - Go to Assignments page
   - Assign teacher to a subject
   - Go back to teacher profile
   - See assignment in list

### Status: ⬜ PASS | ⬜ FAIL

---

## **11. Student Complete Workflow with Guardian**

### Test Steps:
1. **Add Student**:
   - Go to Students → + Add Student
   - Fill all details
   - Submit → Success
2. **View Student**:
   - Click "View" on new student
   - See profile
   - Notice "No guardians added"
3. **Add Guardian**:
   - Click "+ Add" in Guardians section
   - Fill guardian details
   - Mark as primary and emergency
   - Submit → Success
   - See guardian card
4. **Edit Guardian**:
   - Click "Edit" on guardian
   - Update occupation
   - Submit → Success
   - See updated info
5. **Enroll in Class**:
   - Go to Enrollments
   - Enroll this student
   - Go back to student profile
   - See class assignment

### Status: ⬜ PASS | ⬜ FAIL

---

## **12. Class Capacity Management**

### Test Steps:
1. Create a class with capacity of 3
2. Enroll 3 students
3. **Expected on Enrollments page**:
   - ✅ Progress bar at 100%
   - ✅ Red color
   - ✅ "FULL" indicator in dropdown
   - ✅ Cannot select this class
   - ✅ Button disabled
4. Try enrolling 4th student
5. **Expected**:
   - ✅ Cannot submit
   - ✅ "Class is Full" message

### Status: ⬜ PASS | ⬜ FAIL

---

## **13. Modal User Experience**

### Test all modals for:
- ✅ Opens on button click
- ✅ Overlay background visible
- ✅ Form fields all work
- ✅ Required fields enforced
- ✅ Cancel button closes modal
- ✅ X button closes modal (if present)
- ✅ Submit button shows loading state
- ✅ Success closes modal
- ✅ Error displays in modal
- ✅ Data refreshes after close

**Modals to test**:
- Session modal
- Class modal
- Subject modal
- Guardian modal (add)
- Guardian modal (edit)

### Status: ⬜ PASS | ⬜ FAIL

---

## **14. Responsive Design**

### Test on different screen sizes:
1. Desktop (1920x1080)
2. Tablet (768x1024)
3. Mobile (375x667)

**Check**:
- ✅ All pages responsive
- ✅ Modals work on mobile
- ✅ Forms usable on mobile
- ✅ Tables scroll horizontally
- ✅ Navigation accessible
- ✅ Buttons accessible

### Status: ⬜ PASS | ⬜ FAIL

---

## **15. Navigation Flow**

### Test navigation:
- ✅ Dashboard → Students → works
- ✅ Dashboard → Teachers → works
- ✅ Dashboard → Academic → works
- ✅ Dashboard → Assignments → works
- ✅ Dashboard → Enrollments → works
- ✅ Back buttons work
- ✅ Breadcrumbs work (if present)
- ✅ Active page highlighted
- ✅ Logout works

### Status: ⬜ PASS | ⬜ FAIL

---

## **16. Error Handling**

### Test error scenarios:
1. Submit form with missing required fields
   - ✅ Validation error shown
2. Submit invalid data
   - ✅ Error message displayed
3. Network error (turn off backend)
   - ✅ Error message shown
4. Invalid ID in URL
   - ✅ "Not found" message
5. Unauthorized access
   - ✅ Redirects to login

### Status: ⬜ PASS | ⬜ FAIL

---

## **17. Data Enrichment**

### Check computed fields:
- ✅ Student age calculated from DOB
- ✅ Teacher years of service calculated
- ✅ Class capacity shows current/max
- ✅ Subject count per teacher
- ✅ Student count per class
- ✅ Guardian relationships display
- ✅ Status badges colored correctly

### Status: ⬜ PASS | ⬜ FAIL

---

## **18. Search and Filter**

### Test on each list page:
- **Students page**:
  - ✅ Search by name works
  - ✅ Filter by class works
  - ✅ Filter by status works
- **Teachers page**:
  - ✅ Search by name/staff number works
  - ✅ Filter by status works
- **Academic page**:
  - ✅ Tabs switch correctly
  - ✅ Data loads for each tab

### Status: ⬜ PASS | ⬜ FAIL

---

## **Summary**

### Features Tested:
- ⬜ Teacher Detail Page
- ⬜ Teacher Edit Page
- ⬜ Session Modal
- ⬜ Class Modal
- ⬜ Subject Modal
- ⬜ Add Guardian Modal
- ⬜ Edit Guardian Modal
- ⬜ Assignment Interface
- ⬜ Enrollment Interface
- ⬜ Complete Workflows
- ⬜ Capacity Management
- ⬜ Modal UX
- ⬜ Responsive Design
- ⬜ Navigation
- ⬜ Error Handling
- ⬜ Data Enrichment
- ⬜ Search & Filter

### Overall Status:
- **Tested**: __ / 18
- **Passed**: __
- **Failed**: __
- **Success Rate**: __%

---

## **Quick Test URLs**

- Login: http://localhost:3000/login
- Dashboard: http://localhost:3000/dashboard
- Students: http://localhost:3000/dashboard/students
- Teachers: http://localhost:3000/dashboard/teachers
- Academic: http://localhost:3000/dashboard/academic
- Assignments: http://localhost:3000/dashboard/assignments
- Enrollments: http://localhost:3000/dashboard/enrollments

---

## **Notes**

Use this space to record any issues or observations:

```
Issue 1:
[Description]
[Steps to reproduce]
[Expected vs Actual]

Issue 2:
[Description]
...
```

---

**Testing Instructions**:
1. Print this checklist or keep it open in a separate window
2. Go through each test systematically
3. Mark ✅ PASS or ❌ FAIL for each section
4. Note any issues in the Notes section
5. Calculate final success rate

**Good luck! 🚀**
