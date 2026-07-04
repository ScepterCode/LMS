# 🧑‍🏫 Teachers API Testing Guide

## **Overview**
The Teachers API provides complete CRUD operations for managing teacher records in the Nigerian LMS.

## **Base URL**
```
http://127.0.0.1:8000/api/v1/teachers
```

## **Authentication**
All endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### **Get Auth Token**
```bash
POST http://127.0.0.1:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@demohighschool.edu.ng",
  "password": "DemoSchool123!@#"
}
```

---

## **API Endpoints**

### **1. List All Teachers**
```bash
GET /api/v1/teachers
```

**Query Parameters:**
- `skip` (int, default: 0) - Pagination offset
- `limit` (int, default: 100) - Max results
- `status` (string, optional) - Filter by status: "active", "on-leave", "terminated", "retired"
- `search` (string, optional) - Search by name or staff number

**Example Request:**
```bash
GET /api/v1/teachers?status=active&search=john
Authorization: Bearer <token>
```

**Example Response:**
```json
[
  {
    "id": "uuid-here",
    "user_id": "uuid-here",
    "organization_id": "uuid-here",
    "staff_number": "TCH/2024/001",
    "first_name": "John",
    "middle_name": "Chigozie",
    "last_name": "Okafor",
    "date_of_birth": "1985-03-15",
    "gender": "Male",
    "email": "john.okafor@demohighschool.edu.ng",
    "phone": "+234 803 111 2222",
    "address": "123 Lagos Street, Lagos",
    "state_of_origin": "Anambra",
    "lga": "Awka South",
    "nationality": "Nigerian",
    "photo_url": null,
    "qualification": "B.Ed Mathematics",
    "specialization": "Mathematics and Further Mathematics",
    "employment_date": "2020-09-01",
    "employment_type": "full-time",
    "status": "active",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z",
    "full_name": "John Chigozie Okafor",
    "age": 41,
    "years_of_service": 5,
    "subject_count": 3
  }
]
```

**Computed Fields:**
- `full_name` - Combined first, middle, and last name
- `age` - Calculated from date of birth
- `years_of_service` - Calculated from employment date
- `subject_count` - Number of subject assignments

---

### **2. Create New Teacher**
```bash
POST /api/v1/teachers
```

**Required Fields:**
- `user_id` - UUID of existing user account (must have role "teacher")
- `staff_number` - Unique staff identifier
- `first_name`, `last_name` - Teacher's name
- `gender` - "Male", "Female", or "Other"
- `email` - Unique email address
- `phone` - Contact number

**Optional Fields:**
- `middle_name`, `date_of_birth`, `address`
- `state_of_origin`, `lga`, `nationality` (defaults to "Nigerian")
- `qualification` (e.g., "B.Ed Mathematics", "M.Ed Physics")
- `specialization` (e.g., "Mathematics", "English Language")
- `employment_date` (defaults to today)
- `employment_type` - "full-time" (default), "part-time", "contract"

**Example Request:**
```json
POST /api/v1/teachers
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "uuid-of-existing-user",
  "staff_number": "TCH/2024/001",
  "first_name": "John",
  "middle_name": "Chigozie",
  "last_name": "Okafor",
  "date_of_birth": "1985-03-15",
  "gender": "Male",
  "email": "john.okafor@demohighschool.edu.ng",
  "phone": "+234 803 111 2222",
  "address": "123 Lagos Street, Lagos",
  "state_of_origin": "Anambra",
  "lga": "Awka South",
  "nationality": "Nigerian",
  "qualification": "B.Ed Mathematics",
  "specialization": "Mathematics and Further Mathematics",
  "employment_date": "2020-09-01",
  "employment_type": "full-time"
}
```

**Validation Rules:**
- Staff number must be unique
- User ID must exist and belong to your organization
- User ID can only have one teacher record
- Teacher must be at least 18 years old
- Email must be unique
- Gender must be "Male", "Female", or "Other"
- Employment type must be "full-time", "part-time", or "contract"

---

### **3. Get Teacher by ID**
```bash
GET /api/v1/teachers/{teacher_id}
```

**Example Request:**
```bash
GET /api/v1/teachers/uuid-here
Authorization: Bearer <token>
```

**Response:** Same format as list endpoint with full details

---

### **4. Update Teacher**
```bash
PUT /api/v1/teachers/{teacher_id}
```

**Updatable Fields:**
- Personal info: `first_name`, `middle_name`, `last_name`, `date_of_birth`, `gender`
- Contact: `email`, `phone`, `address`
- Location: `state_of_origin`, `lga`, `nationality`
- Professional: `qualification`, `specialization`, `employment_date`, `employment_type`
- Status: `status` - "active", "on-leave", "terminated", "retired"
- Media: `photo_url`

**Example Request:**
```json
PUT /api/v1/teachers/uuid-here
Authorization: Bearer <token>
Content-Type: application/json

{
  "phone": "+234 803 999 8888",
  "qualification": "M.Ed Mathematics",
  "status": "active"
}
```

**Note:** Only provide fields you want to update. All fields are optional.

---

### **5. Delete Teacher**
```bash
DELETE /api/v1/teachers/{teacher_id}
```

**Example Request:**
```bash
DELETE /api/v1/teachers/uuid-here
Authorization: Bearer <token>
```

**Protection:**
- Cannot delete teacher with active subject assignments
- Must remove all assignments first

**Response:** 204 No Content on success

---

### **6. Get Teacher Assignments**
```bash
GET /api/v1/teachers/{teacher_id}/assignments
```

**Purpose:** View all subject-class assignments for a teacher

**Example Request:**
```bash
GET /api/v1/teachers/uuid-here/assignments
Authorization: Bearer <token>
```

**Example Response:**
```json
[
  {
    "id": "assignment-uuid",
    "teacher_id": "teacher-uuid",
    "subject_id": "subject-uuid",
    "class_id": "class-uuid",
    "session_id": "session-uuid",
    "term_id": "term-uuid",
    "created_at": "2024-01-15T10:00:00Z",
    "subject_name": "Mathematics",
    "class_name": "JSS 1A"
  }
]
```

---

## **Authorization**

### **Who Can Do What**

| Action | System Admin | School Admin | Teacher | Student | Parent |
|--------|-------------|--------------|---------|---------|--------|
| List teachers | ✅ | ✅ | ✅ | ✅ | ✅ |
| Get teacher details | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create teacher | ✅ | ✅ | ❌ | ❌ | ❌ |
| Update teacher | ✅ | ✅ | ❌ | ❌ | ❌ |
| Delete teacher | ✅ | ✅ | ❌ | ❌ | ❌ |
| View assignments | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## **Testing Workflow**

### **Step 1: Create a User Account for Teacher**
First, you need to create a user account with role "teacher":

```json
POST /api/v1/organizations/{org_id}/users
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "email": "teacher@demohighschool.edu.ng",
  "password": "Teacher123!@#",
  "role": "teacher",
  "first_name": "John",
  "last_name": "Okafor"
}
```

**Save the returned `user_id` for the next step.**

### **Step 2: Create Teacher Record**
```json
POST /api/v1/teachers
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "user_id": "uuid-from-step-1",
  "staff_number": "TCH/2024/001",
  "first_name": "John",
  "middle_name": "Chigozie",
  "last_name": "Okafor",
  "date_of_birth": "1985-03-15",
  "gender": "Male",
  "email": "john.okafor@demohighschool.edu.ng",
  "phone": "+234 803 111 2222",
  "address": "123 Lagos Street, Lagos",
  "state_of_origin": "Anambra",
  "lga": "Awka South",
  "qualification": "B.Ed Mathematics",
  "specialization": "Mathematics",
  "employment_date": "2020-09-01",
  "employment_type": "full-time"
}
```

### **Step 3: List Teachers**
```bash
GET /api/v1/teachers
Authorization: Bearer <token>
```

### **Step 4: Update Teacher**
```json
PUT /api/v1/teachers/{teacher_id}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "qualification": "M.Ed Mathematics",
  "phone": "+234 803 999 8888"
}
```

### **Step 5: View Teacher Assignments**
```bash
GET /api/v1/teachers/{teacher_id}/assignments
Authorization: Bearer <token>
```

---

## **Error Handling**

### **Common Error Responses**

**404 - Teacher Not Found**
```json
{
  "detail": "Teacher with ID uuid-here not found"
}
```

**409 - Duplicate Staff Number**
```json
{
  "detail": "Teacher with staff_number 'TCH/2024/001' already exists"
}
```

**400 - Validation Error**
```json
{
  "detail": "This user already has a teacher record"
}
```

**400 - Cannot Delete with Dependencies**
```json
{
  "detail": "Cannot delete teacher with 5 active subject assignments. Remove assignments first."
}
```

**403 - Insufficient Permissions**
```json
{
  "detail": "Insufficient permissions to manage teachers"
}
```

---

## **Sample Staff Numbers**

Use these formats:
- `TCH/2024/001` - Teacher hired in 2024, sequential number
- `TCH/2024/002` 
- `TCH/SCI/001` - Science department teacher
- `TCH/MATH/001` - Math department teacher

---

## **Testing Checklist**

- [ ] Create teacher with valid data
- [ ] List all teachers
- [ ] Filter teachers by status
- [ ] Search teachers by name
- [ ] Get single teacher details
- [ ] Update teacher information
- [ ] View teacher's subject assignments
- [ ] Try to delete teacher (should work if no assignments)
- [ ] Try to create duplicate staff number (should fail)
- [ ] Try to link same user_id twice (should fail)
- [ ] Verify computed fields (age, years_of_service, full_name)
- [ ] Test authorization (non-admin shouldn't be able to create/update)

---

## **Quick Test with cURL**

```bash
# 1. Login
TOKEN=$(curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demohighschool.edu.ng","password":"DemoSchool123!@#"}' \
  | jq -r '.access_token')

# 2. List teachers
curl http://127.0.0.1:8000/api/v1/teachers \
  -H "Authorization: Bearer $TOKEN" | jq

# 3. Create teacher
curl -X POST http://127.0.0.1:8000/api/v1/teachers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"uuid-here",
    "staff_number":"TCH/2024/001",
    "first_name":"John",
    "last_name":"Okafor",
    "gender":"Male",
    "email":"john@school.com",
    "phone":"+234 803 111 2222",
    "qualification":"B.Ed Mathematics",
    "specialization":"Mathematics"
  }' | jq
```

---

## **Next Steps**

After testing the Teachers API:
1. Test Terms API (if created)
2. Test Subject Assignments API (linking teachers to subjects/classes)
3. Begin frontend development for teacher management
4. Build teacher portal dashboard

---

**API Documentation:** http://127.0.0.1:8000/docs
**Teachers API Status:** ✅ Fully Operational (6 endpoints)
