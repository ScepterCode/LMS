# ⚡ QUICK START - After Fixes Applied

## 🎯 TL;DR (Too Long; Didn't Read)

**All your 18 issues are fixed. Here's what to do:**

1. **Restart backend** → `cd backend` → `uvicorn app.main:app --reload`
2. **Open browser** → `http://localhost:3000`
3. **Follow the checklist** that appears on your dashboard
4. **Done!** ✅

---

## 🚀 3-Minute Restart Guide

### Option A: Automated (Easiest)
```powershell
.\restart-servers.ps1
```
**That's it!** Both servers will start automatically.

### Option B: Manual
```powershell
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend (new terminal)
cd frontend
npm run dev
```

---

## 📋 What Happens Next

### 1. Login
- Go to `http://localhost:3000`
- Login as admin

### 2. See Onboarding Checklist
You'll see this on your dashboard:

```
🚀 Getting Started
Complete these steps to start using the LMS

Progress: 0 of 5 completed

⭕ 1. Create Academic Session → [Create Session]
⭕ 2. Add Subjects → [Add Subjects]
⭕ 3. Create Classes → [Create Classes]
⭕ 4. Add Teachers → [Add Teachers]
⭕ 5. Enroll Students → [Add Students]
```

### 3. Click the Buttons
- Each step has a button
- Click it → completes that step
- Checkbox turns green ✅
- Move to next step

### 4. System Unlocks
As you complete steps, features become available:
- After step 1: Terms and sessions work
- After step 2: Subject assignments work
- After step 3: Student enrollment works
- After step 4: Teacher assignments work
- After step 5: **Everything works!**

---

## 🎓 Example First Session (10 minutes)

### Step 1: Create Session (2 min)
1. Dashboard → Academic Management → Sessions tab
2. Click "+ Add Session"
3. Enter:
   - Name: `2024/2025`
   - Start: `2024-09-01`
   - End: `2025-08-31`
   - ✅ Check "Set as current"
4. Click "Create"

✅ **Checklist updates automatically!**

### Step 2: Add Subjects (3 min)
1. Stay on Academic Management → Subjects tab
2. Add these subjects (click "+ Add Subject" for each):
   - Mathematics (Core)
   - English Language (Core)
   - Physics (Core)
   - Chemistry (Core)
   - Biology (Core)

✅ **Checklist updates!**

### Step 3: Create Classes (3 min)
1. Stay on Academic Management → Classes tab
2. Add these classes:
   - JSS 1 (Junior, capacity 40)
   - JSS 2 (Junior, capacity 40)
   - SS 1 (Senior, capacity 40)

✅ **Checklist updates!**

### Step 4: Add Teachers (Optional for now)
You can skip this and come back later.

### Step 5: Add Students (2 min)
1. Dashboard → Students → + Add Student
2. Fill in details
3. **Important:** "Current Class" dropdown now works!
4. Select JSS 1
5. Click "Create"

✅ **Checklist updates!**

**Total time: 10 minutes**  
**Result: System ready to use! 🎉**

---

## 🐛 If Something Goes Wrong

### Error: "Database connection not available"
```powershell
# Restart backend
cd backend
uvicorn app.main:app --reload
```

### Error: "An error occurred"
```powershell
# Check backend logs
type backend\app.log | Select-Object -Last 20
```

### Dropdown Still Empty
- Did you complete the previous steps?
- Check: Academic session created and marked as "current"
- Check: Classes created
- Refresh page (F5)

### Checklist Not Showing
- You must be logged in as Admin
- Clear browser cache (Ctrl + Shift + Delete)
- Reload page

---

## 📊 Success Checklist

After following the guide, verify:

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can login successfully
- [ ] Onboarding checklist visible
- [ ] Academic session created
- [ ] Subjects added
- [ ] Classes created
- [ ] "Current Class" dropdown populated
- [ ] No "An error occurred" messages

---

## 🎉 You're Done!

### What Changed:
- ❌ **Before:** 18 broken features
- ✅ **After:** Everything works with guidance

### What You Get:
- ✅ Clear setup workflow
- ✅ Automatic progress tracking
- ✅ No more guessing
- ✅ All features unlocked properly

### Next Steps:
1. Complete the 5 onboarding steps
2. Add your real school data
3. Train your teachers
4. Start using the LMS!

---

## 📞 Need More Help?

### Documentation:
- **Full Guide:** `ONBOARDING_WORKFLOW_GUIDE.md`
- **Technical Details:** `CRITICAL_FIXES_APPLIED.md`
- **Issue Status:** `FIXES_SUMMARY_README.md`

### Quick Commands:
```powershell
# View backend logs
type backend\app.log | Select-Object -Last 50

# Restart everything
.\restart-servers.ps1

# Check backend health
Invoke-WebRequest -Uri "http://localhost:8000/api/health"
```

---

**🚀 Ready? Let's go!**

```powershell
# Run this now:
.\restart-servers.ps1
```

Then open: **http://localhost:3000**

**That's it! Follow the onboarding checklist on screen.**

---

*Time to Complete: 5 minutes setup + 10 minutes onboarding = 15 minutes total*  
*Difficulty: Easy (just click buttons)*  
*Result: Fully working LMS ✅*
