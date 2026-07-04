# Frontend Integration Issues & Fixes

## Issues Identified

### 1. **Missing Array Defensive Programming**
**Problem**: Some pages don't have `|| []` fallbacks when using .map()
**Impact**: "Cannot read properties of undefined (reading 'map')" errors

### 2. **API Response Structure Mismatch**
**Problem**: Backend returns arrays directly, frontend expects wrapped response
**Status**: ✅ Already handled by ApiClient wrapper

### 3. **Missing Integration in Forms**
**Problem**: Class creation doesn't have subject selection integration yet
**Impact**: Requirement #3 not fully integrated into UI

### 4. **Form Teacher Detection Missing**
**Problem**: Students page doesn't detect form teacher status
**Impact**: Form teachers can't see special "Add to My Class" buttons

### 5. **Grade Viewing Toggle Missing**
**Problem**: Reports page doesn't have form teacher toggle
**Impact**: Form teachers can't view all class grades

## Critical Fixes Needed

### Fix 1: Add Defensive Programming to All Maps
Every `.map()` call needs `|| []` fallback:

```typescript
// BEFORE (BREAKS)
{schemes.map(scheme => ...)}

// AFTER (SAFE)
{(schemes || []).map(scheme => ...)}
```

### Fix 2: Add Subject Selection to Class Creation
In `frontend/app/dashboard/academic/page.tsx`:
- Add subject checkboxes to class creation modal
- Call `/teacher-management/classes/{id}/subjects` after class creation
- Show selected subjects in class cards

### Fix 3: Add Form Teacher Detection
In `frontend/app/dashboard/students/page.tsx`:
- Check if current user is form teacher
- Show banner with "Add Student to My Class" button
- Filter students by form teacher's class

### Fix 4: Add Grade Viewing Toggle
In `frontend/app/dashboard/grading/reports/page.tsx`:
- Detect if user is form teacher
- Show "View All Class Grades" toggle
- Fetch all subjects for the class when toggled

### Fix 5: Check Authentication Flow
- Verify JWT token is being sent with requests
- Check if user object has required fields (teacher_id, school_id)
- Ensure AuthContext is providing correct user data

## Testing Checklist

- [ ] All dropdown lists load without errors
- [ ] Teacher Management pages show data correctly
- [ ] Class creation includes subject selection
- [ ] Form teachers see special permissions
- [ ] Grading schemes can be created with components
- [ ] Teacher assignments work for multiple classes/subjects
- [ ] Student remarks can be added by form teachers
- [ ] Reports can be sent to parents

## Next Steps

1. Add `|| []` fallbacks to all .map() calls
2. Integrate subject selection into class creation
3. Add form teacher detection to student/grading pages
4. Test with real user data
5. Check browser console for API errors
