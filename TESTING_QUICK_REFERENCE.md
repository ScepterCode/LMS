# ⚡ TESTING QUICK REFERENCE CARD

## 🚀 **START TESTING IN 3 COMMANDS**

```powershell
# 1. Start servers (opens 2 windows)
.\START_BOTH_SERVERS.ps1

# 2. Wait 60 seconds for startup

# 3. Run tests
python test_system.py
```

---

## ✅ **WHAT YOU WANT TO SEE**

```
Total Tests:  30
Passed:       28-30
Failed:       0-2
Pass Rate:    93-100%

🎉 ALL TESTS PASSED!
```

---

## 🎯 **MUST-PASS TESTS**

1. ✓ Admin Login
2. ✓ **Create Session** ← YOUR MAIN FIX
3. ✓ List Students/Teachers/Parents
4. ✓ **Get Parent's Children** ← JUST FIXED

---

## 📊 **SCORING**

| Pass Rate | Meaning |
|-----------|---------|
| 100% | Perfect! ✅ |
| 90-99% | Excellent! ✅ |
| 70-89% | Good (minor issues) ⚠️ |
| <70% | Needs work 🔴 |

---

## 🔗 **URLs TO CHECK**

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Login: sarahchidiloveday@gmail.com / Admin123!

---

## 🐛 **QUICK FIXES**

| Problem | Solution |
|---------|----------|
| Connection refused | Start backend server |
| 403/401 errors | Clear cookies, restart backend |
| Frontend won't start | `npm install` then `npm run dev` |
| Python not found | Install Python 3.8+ |

---

## 📁 **HELPFUL FILES**

- `COMPLETE_TESTING_INSTRUCTIONS.md` - Full guide
- `HOW_TO_INTERPRET_TEST_RESULTS.md` - Read results
- `START_BOTH_SERVERS.ps1` - Auto-start
- `README_TESTING.md` - Overview

---

## 🎯 **YOUR GOAL**

Get **90%+ pass rate** with all 4 critical tests passing.

Then system is **PRODUCTION READY**! 🚀

---

## 💡 **ONE-LINER TO START**

```powershell
.\START_BOTH_SERVERS.ps1 ; Start-Sleep -Seconds 60 ; python test_system.py
```

This will:
1. Start servers
2. Wait 60 seconds
3. Run tests automatically

---

**GO TEST YOUR SYSTEM NOW! ⚡**
