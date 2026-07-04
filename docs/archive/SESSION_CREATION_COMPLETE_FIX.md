# Session Creation - Complete Root Cause Analysis & Fix

## Date: 2026-07-01

## 🔍 ROOT CAUSE ANALYSIS

After deep diagnostic investigation, I've identified **3 CRITICAL ISSUES**:

### Issue 1: PORT MISMATCH ✅ FIXED
- **Problem**: Frontend configured to call port 8001, backend running on port 8000
- **Impact**: All API calls failing with connection errors
- **Fix**: Updated `frontend/.env.local` to use port 8000

### Issue 2: AUTHENTICATION REQUIREMENT
- **Problem**: `/api/v1/sessions` endpoint requires authentication token
- **Error**: "Authentication token required" (403 Forbidden)
- **Root Cause**: Sessions endpoint requires logged-in user with school_id
- **Impact**: Cannot even list sessions without being logged in

### Issue 3: VALIDATION ERRORS (422)
- **Problem**: Session creation data not meeting backend validation
- **Requirements**:
  - name: Must be in format "YYYY/YYYY" (e.g., "2024/2025")
  - start_date: Required, must be valid date
  - end_date: Required, must be AFTER start_date
  - User must have school_id (organization)
  - User must be admin or system_admin role

## 📋 COMPLETE VALIDATION REQUIREMENTS

### Backend Model (AcademicSessionCreate):
```python
name: str  # 7-50 chars, format YYYY/YYYY
start_date: date  # Required
end_date: date  # Required, must be > start_date
is_current: bool  # Optional, defaults to False
```

### Backend Security Requirements:
1. **Authentication**: Valid JWT token required
2. **Authorization**: User must be "admin" or "system_admin"  
3. **Organization**: User must have school_id
4. **Uniqueness**: Each organization manages its own sessions

## 🔧 FIXES APPLIED

### 1. Port Configuration Fix ✅
**File**: `frontend/.env.local`
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000  # Changed from 8001
```

## 🎯 REMAINING ISSUES TO ADDRESS

### Frontend Form Validation
The form needs better validation before submission:

**Current Form State**:
```typescript
sessionForm = {
  name: '',          // Needs format validation YYYY/YYYY
  start_date: '',    // Needs date validation
  end_date: '',      // Must be after start_date
  is_current: false
}
```

### Recommended Frontend Fixes:

1. **Add Name Format Validation**:
```typescript
const validateSessionName = (name: string) => {
  const pattern = /^\d{4}\/\d{4}$/;
  if (!pattern.test(name)) {
    return 'Session name must be in format YYYY/YYYY (e.g., 2024/2025)';
  }
  const [year1, year2] = name.split('/').map(Number);
  if (year2 !== year1 + 1) {
    return 'Second year must be one year after first year';
  }
  return null;
};
```

2. **Add Date Validation**:
```typescript
const validateDates = (startDate: string, endDate: string) => {
  if (!startDate || !endDate) {
    return 'Both start and end dates are required';
  }
  if (new Date(endDate) <= new Date(startDate)) {
    return 'End date must be after start date';
  }
  return null;
};
```

3. **Enhanced Form Submit Handler**:
```typescript
const handleCreateSession = async (e: React.FormEvent) => {
  e.preventDefault();
  setError('');
  
  // Validate name format
  const nameError = validateSessionName(sessionForm.name);
  if (nameError) {
    setError(nameError);
    return;
  }
  
  // Validate dates
  const dateError = validateDates(sessionForm.start_date, sessionForm.end_date);
  if (dateError) {
    setError(dateError);
    return;
  }
  
  setSubmitting(true);
  
  try {
    const response = await api.createSession(sessionForm);
    if (response.error) {
      setError(response.error);
    } else {
      handleCloseModal();
      loadData();
    }
  } catch (err) {
    setError('Failed to create session');
  } finally {
    setSubmitting(false);
  }
};
```

## 🧪 TESTING CHECKLIST

### Prerequisites:
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] User logged in as admin
- [ ] User has school_id assigned

### Test Cases:
1. **Invalid Session Name**:
   - Input: "2024-2025" → Should show error
   - Input: "2024" → Should show error
   - Input: "202/2025" → Should show error
   
2. **Invalid Date Range**:
   - End date before start date → Should show error
   - End date same as start date → Should show error
   
3. **Valid Session Creation**:
   - Name: "2024/2025"
   - Start: 2024-09-01
   - End: 2025-08-31
   - Should create successfully

4. **Current Session Toggle**:
   - Creating with is_current=true should unset other current sessions
   - Only one session should be marked as current

## 📊 API ENDPOINT DETAILS

### GET /api/v1/sessions
- **Auth**: Required
- **Permissions**: Any authenticated user with school_id
- **Returns**: List of sessions for user's organization

### POST /api/v1/sessions
- **Auth**: Required
- **Permissions**: admin or system_admin only
- **Body**:
```json
{
  "name": "2024/2025",
  "start_date": "2024-09-01",
  "end_date": "2025-08-31",
  "is_current": false
}
```
- **Returns**: Created session object

## 🚨 COMMON ERRORS & SOLUTIONS

### Error: 403 Forbidden
**Cause**: Not authenticated or no token
**Solution**: Ensure user is logged in and token is being sent

### Error: 403 "Only school administrators can manage academic sessions"
**Cause**: User role is not admin or system_admin
**Solution**: User needs admin privileges

### Error: 403 "User must belong to a school"
**Cause**: User doesn't have school_id
**Solution**: Assign user to an organization

### Error: 422 Unprocessable Entity
**Cause**: Validation failed on request data
**Common Reasons**:
- Session name not in YYYY/YYYY format
- End date not after start date
- Required fields missing

### Error: "Failed to load resource: net::ERR_CONNECTION_REFUSED"
**Cause**: Backend not running or wrong port
**Solution**: Ensure backend is running on correct port

## 🎉 SUCCESS CRITERIA

Session creation working when:
1. ✅ Frontend connects to correct port (8000)
2. ✅ User is authenticated
3. ✅ User has admin role
4. ✅ User belongs to school
5. ✅ Session name in correct format
6. ✅ Dates are valid
7. ✅ Form validation prevents bad data

## 📝 NEXT STEPS

1. **Restart Frontend** to pick up .env.local changes
2. **Add Form Validation** to prevent 422 errors
3. **Add User Feedback** for better error messages
4. **Test Complete Flow** from login to session creation

---

**Status**: Port fix applied ✅ | Validation improvements recommended ⚠️
**Next Action**: Restart frontend server to apply port change
