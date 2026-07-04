# ⚡ QUICK TEST GUIDE - 3 Simple Steps

## 🔴 **CURRENT STATUS: Backend Not Running**

---

## ✅ **3 STEPS TO TEST THE SYSTEM**

### **STEP 1: Start Backend** 🖥️

```powershell
# Open PowerShell Terminal #1
cd c:\Users\DELL\Downloads\LMS\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Wait for:** `Application startup complete`  
**Keep terminal open!** ✋

---

### **STEP 2: Start Frontend** 🌐

```powershell
# Open PowerShell Terminal #2
cd c:\Users\DELL\Downloads\LMS\frontend
npm run dev
```

**Wait for:** `Ready in 3s`  
**Keep terminal open!** ✋

---

### **STEP 3: Run Tests** 🧪

```powershell
# Open PowerShell Terminal #3 (or use current)
cd c:\Users\DELL\Downloads\LMS
python test_system.py
```

**Press Enter** when prompted  
**Tests will run automatically** ⚙️

---

## ✅ **WHAT WILL BE TESTED**

The automated test will check:

✓ **Login** - Admin authentication  
✓ **Sessions** - Create/list academic sessions (THE MAIN FIX)  
✓ **Students** - CRUD operations  
✓ **Teachers** - CRUD operations  
✓ **Parents** - CRUD operations + children links  
✓ **Grading** - Assessments and grades  
✓ **Attendance** - Records  
✓ **Fees** - Structures and payments  
✓ **Permissions** - Access control  

**Total: ~30 tests in 2-3 minutes**

---

## 📊 **EXPECTED RESULT**

```
======================================================================
                          TEST SUMMARY                         
======================================================================

Total Tests:  30
Passed:       28-30
Failed:       0-2
Pass Rate:    93-100%

🎉 ALL TESTS PASSED! System is fully functional.
```

---

## 🎯 **IF YOU PREFER MANUAL TESTING**

Instead of Step 3, open your browser:

1. Go to **http://localhost:3000**
2. Login: `sarahchidiloveday@gmail.com` / `Admin123!`
3. Test these 4 things:
   - ✅ Create a session (Academic page)
   - ✅ Create a teacher with password (Teachers → Add)
   - ✅ Create a parent with password (Parents → Add)
   - ✅ Link parent to student (Parent details → Link Student)

**All 4 should work without errors!** ✅

---

## 📝 **DETAILED GUIDES**

- `START_SERVERS_AND_TEST.md` - Full instructions
- `TEST_STATUS_REPORT.md` - Current status
- `MANUAL_TESTING_CHECKLIST.md` - Step-by-step checklist
- `TESTING_GUIDE_COMPLETE.md` - Complete guide

---

## 🚀 **START NOW!**

Open 3 PowerShell terminals and run the commands above!

**Need help? Just ask!** 💬
