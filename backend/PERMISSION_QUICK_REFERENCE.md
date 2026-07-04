# Permission System - Quick Reference Card

## For Backend Developers

### Quick Start

```python
# 1. Import permission checker
from app.core.permissions import PermissionChecker
from app.core.database import get_supabase
from app.core.exceptions import AuthorizationError

# 2. Get supabase client
supabase = get_supabase()

# 3. Check permission
teacher_id = current_user["id"]
class_id = "some-class-id"

try:
    await PermissionChecker.verify_form_teacher_permission(
        teacher_id, class_id, supabase
    )
    # Permission granted - proceed
except AuthorizationError as e:
    # Permission denied - raise HTTPException
    raise HTTPException(403, detail=str(e))
```

---

## Common Patterns

### Pattern 1: Form Teacher Check (Attendance, Remarks, Reports)

```python
@router.post("/attendance/mark")
async def mark_attendance(data, current_user, db):
    # Admin bypass
    if current_user["role"] == "admin":
        # Allow admin access
        pass
    
    # Teacher check
    elif current_user["role"] == "teacher":
        supabase = get_supabase()
        try:
            await PermissionChecker.verify_form_teacher_permission(
                current_user["id"], data.class_id, supabase
            )
        except AuthorizationError as e:
            raise HTTPException(403, detail=str(e))
    
    # Process request...
```

### Pattern 2: Subject Teacher Check (Grade Entry, Assessment Creation)

```python
@router.post("/grades/bulk")
async def bulk_grade_entry(data, current_user, db):
    # Get assessment to find subject_id and class_id
    assessment = db.table("assessments").select("subject_id, class_id").eq(
        "id", data.assessment_id
    ).execute()
    
    subject_id = assessment.data[0]["subject_id"]
    class_id = assessment.data[0]["class_id"]
    
    # Teacher check
    if current_user["role"] == "teacher":
        supabase = get_supabase()
        try:
            await PermissionChecker.verify_subject_teacher_permission(
                current_user["id"], subject_id, class_id, supabase
            )
        except AuthorizationError as e:
            raise HTTPException(403, detail=str(e))
    
    # Process grades...
```

### Pattern 3: Either Form OR Subject Teacher (View Class Data)

```python
@router.get("/class/{class_id}/analytics")
async def get_analytics(class_id, subject_id, current_user, db):
    if current_user["role"] == "teacher":
        supabase = get_supabase()
        teacher_id = current_user["id"]
        
        # Check if form teacher OR subject teacher
        is_form_teacher = await PermissionChecker.can_view_class_grades(
            teacher_id, class_id, supabase
        )
        is_subject_teacher = await PermissionChecker.can_enter_grades(
            teacher_id, subject_id, class_id, supabase
        )
        
        if not (is_form_teacher or is_subject_teacher):
            raise HTTPException(403, detail="No permission")
    
    # Return analytics...
```

---

## Permission Methods Reference

### Verification Methods (Raise Exception if Denied)

```python
# Use these in endpoint handlers
await PermissionChecker.verify_form_teacher_permission(teacher_id, class_id, supabase)
await PermissionChecker.verify_subject_teacher_permission(teacher_id, subject_id, class_id, supabase)
await PermissionChecker.verify_admin_only(user)
await PermissionChecker.verify_teacher_only(user)
```

### Check Methods (Return Boolean)

```python
# Use these for conditional logic
is_form = await PermissionChecker.is_form_teacher(teacher_id, class_id, supabase)
is_subject = await PermissionChecker.is_subject_teacher(teacher_id, subject_id, class_id, supabase)
can_mark = await PermissionChecker.can_mark_attendance(teacher_id, class_id, supabase)
can_enter = await PermissionChecker.can_enter_grades(teacher_id, subject_id, class_id, supabase)
can_view = await PermissionChecker.can_view_class_grades(teacher_id, class_id, supabase)
```

### Query Methods

```python
# Get teacher's assignments
classes = await PermissionChecker.get_teacher_classes(teacher_id, supabase)
subjects = await PermissionChecker.get_teacher_subjects(teacher_id, class_id, supabase)
can_view_students = await PermissionChecker.can_view_students_in_class(teacher_id, class_id, supabase)
```

---

## Using Permission Middleware (Advanced)

### Decorator-Based Permissions

```python
from app.middleware.permissions import require_roles, require_form_teacher, require_subject_teacher

# Require specific roles
@require_roles(["admin", "teacher"])
async def my_endpoint(current_user):
    # Only admins and teachers can access
    pass

# Require form teacher
@require_form_teacher(class_id_param="class_id")
async def mark_attendance(class_id, current_user):
    # Only form teacher of this class can access
    # Admin bypass is automatic
    pass

# Require subject teacher
@require_subject_teacher(subject_id_param="subject_id", class_id_param="class_id")
async def enter_grades(subject_id, class_id, current_user):
    # Only teacher assigned to this subject+class can access
    pass
```

### Permission Caching

```python
from app.middleware.permissions import check_form_teacher_cached, permission_cache

# Cached check (faster)
is_form_teacher = await check_form_teacher_cached(teacher_id, class_id, supabase)

# Clear cache when assignments change
permission_cache.clear_user(teacher_id)
```

### Audit Logging

```python
from app.middleware.permissions import PermissionAuditLog

# Log access attempt
await PermissionAuditLog.log_attendance_access(
    user_id=teacher_id,
    class_id=class_id,
    granted=True,
    reason="Form teacher of class"
)
```

---

## Testing Permissions

### Unit Test Example

```python
import pytest
from app.core.permissions import PermissionChecker

@pytest.mark.asyncio
async def test_form_teacher_permission():
    # Setup
    teacher_id = "teacher-123"
    class_id = "class-456"
    
    # Test: Form teacher can mark attendance
    result = await PermissionChecker.can_mark_attendance(
        teacher_id, class_id, mock_supabase
    )
    assert result == True
    
    # Test: Non-form teacher cannot mark attendance
    result = await PermissionChecker.can_mark_attendance(
        "other-teacher-id", class_id, mock_supabase
    )
    assert result == False
```

### Integration Test Example

```python
def test_mark_attendance_permission():
    # Test as form teacher
    response = client.post(
        "/api/v1/attendance/mark",
        headers={"Authorization": f"Bearer {form_teacher_token}"},
        json={"class_id": "5A", "records": [...]}
    )
    assert response.status_code == 201
    
    # Test as non-form teacher
    response = client.post(
        "/api/v1/attendance/mark",
        headers={"Authorization": f"Bearer {other_teacher_token}"},
        json={"class_id": "5A", "records": [...]}
    )
    assert response.status_code == 403
    assert "Form teacher" in response.json()["detail"]
```

---

## Database Queries

### Check Form Teacher

```sql
SELECT id FROM teacher_class_assignments
WHERE teacher_id = $1 
  AND class_id = $2 
  AND is_form_teacher = TRUE
LIMIT 1;
```

### Check Subject Teacher

```sql
SELECT id FROM teacher_class_assignments
WHERE teacher_id = $1 
  AND subject_id = $2 
  AND class_id = $3
LIMIT 1;
```

### Get Teacher's Form Classes

```sql
SELECT class_id FROM teacher_class_assignments
WHERE teacher_id = $1 
  AND is_form_teacher = TRUE;
```

### Get Teacher's Subject Assignments

```sql
SELECT subject_id, class_id FROM teacher_class_assignments
WHERE teacher_id = $1
  [AND class_id = $2];  -- optional
```

---

## Troubleshooting

### Issue: Permission Check Always Fails

**Check**:
1. Is teacher properly assigned in `teacher_class_assignments` table?
2. Is `is_form_teacher` flag set correctly?
3. Is teacher_id from JWT token correct?
4. Is class_id parameter correct?

**Debug**:
```python
# Check teacher's assignments
response = supabase.table('teacher_class_assignments').select('*').eq(
    'teacher_id', teacher_id
).execute()
print(f"Teacher assignments: {response.data}")
```

### Issue: Admin Getting Permission Denied

**Check**: User role in JWT token

**Fix**: Ensure `current_user["role"]` is "admin" or "system_admin"

### Issue: Permission Cache Not Clearing

**Solution**:
```python
from app.middleware.permissions import permission_cache

# Clear specific user
permission_cache.clear_user(teacher_id)

# Or clear all
permission_cache.clear()
```

---

## Performance Tips

1. **Use caching** for frequently checked permissions
2. **Batch permission checks** when possible
3. **Cache teacher assignments** in frontend to reduce API calls
4. **Add database indexes** on `teacher_class_assignments(teacher_id, class_id)`
5. **Monitor slow queries** in permission checks

---

## When to Use What

| Scenario | Use This |
|----------|----------|
| Mark attendance | `verify_form_teacher_permission()` |
| Enter grades | `verify_subject_teacher_permission()` |
| View all class grades | `can_view_class_grades()` |
| Generate report card | `verify_form_teacher_permission()` |
| Add student remarks | `verify_form_teacher_permission()` |
| Create assessment | `verify_subject_teacher_permission()` |
| View student list | `can_view_students_in_class()` |
| Admin-only action | `verify_admin_only()` |

---

## Best Practices

✅ **DO**:
- Always check permissions before data operations
- Use `verify_*` methods to automatically raise exceptions
- Cache permission results when appropriate
- Log permission denials for security auditing
- Clear cache when teacher assignments change

❌ **DON'T**:
- Bypass permission checks in endpoints
- Rely only on role checks without resource permissions
- Forget to handle AuthorizationError exceptions
- Cache permissions indefinitely
- Skip admin bypass logic

---

## Quick Decision Tree

```
Is user admin/system_admin?
├─ YES → Allow (bypass permission checks)
└─ NO → Is user a teacher?
    ├─ YES → Check specific permission
    │   ├─ Attendance/Remarks/Reports? → Check form teacher
    │   └─ Grades/Assessments? → Check subject teacher
    └─ NO → Deny (403 Forbidden)
```

---

## Support

For more details, see:
- `backend/PERMISSIONS_ENFORCEMENT.md` - Complete documentation
- `PERMISSION_SYSTEM_COMPLETE.md` - Implementation summary
- `backend/app/core/permissions.py` - Source code
- `backend/app/middleware/permissions.py` - Middleware and decorators
