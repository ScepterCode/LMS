# 🎯 PHASE 1 MVP - FRESH START

## **CORE OBJECTIVES**
1. ✅ Working authentication (login/logout)
2. ✅ School registration with trial
3. ✅ Basic dashboard for system admin
4. ✅ Simple school admin dashboard
5. ✅ Clean, minimal codebase

## **ARCHITECTURE**
```
┌─────────────────┐
│   Frontend      │  Next.js 15 + TypeScript
│   (localhost:3000) │  Tailwind CSS
└────────┬────────┘
         │
┌────────▼────────┐
│   Backend       │  FastAPI + Python
│   (127.0.0.1:8000) │  PostgreSQL (Supabase)
└─────────────────┘
```

## **DATABASE - MINIMAL SCHEMA**

### **1. users** (All user accounts)
```sql
id UUID PRIMARY KEY
email VARCHAR UNIQUE NOT NULL
password_hash VARCHAR NOT NULL
full_name VARCHAR NOT NULL
role VARCHAR NOT NULL  -- 'system_admin', 'admin', 'teacher', 'bursar', 'parent'
school_id UUID REFERENCES organizations(id)  -- NULL for system_admin
is_active BOOLEAN DEFAULT true
created_at TIMESTAMP DEFAULT NOW()
```

### **2. organizations** (Schools)
```sql
id UUID PRIMARY KEY
name VARCHAR NOT NULL
slug VARCHAR UNIQUE NOT NULL
email VARCHAR UNIQUE NOT NULL
subscription_plan_id VARCHAR
subscription_status VARCHAR DEFAULT 'trial'
trial_ends_at TIMESTAMP
is_active BOOLEAN DEFAULT true
created_at TIMESTAMP DEFAULT NOW()
```

### **3. subscription_plans** (Simple plans)
```sql
id VARCHAR PRIMARY KEY  -- 'trial', 'basic', 'standard', 'premium'
name VARCHAR NOT NULL
price_monthly DECIMAL
price_yearly DECIMAL
max_students INTEGER
features JSONB
```

## **API ENDPOINTS - PHASE 1 ONLY**

### **Authentication**
- `POST /api/v1/auth/login` - Login all users
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user

### **School Registration**
- `POST /api/v1/auth/register-school` - Public school registration

### **System Admin**
- `GET /api/v1/system-admin/organizations` - List all schools
- `GET /api/v1/system-admin/analytics` - Basic platform stats

### **School Admin**
- `GET /api/v1/organizations/{id}` - Get school details
- `GET /api/v1/organizations/{id}/users` - List school users

## **FRONTEND PAGES - PHASE 1 ONLY**

### **Public Pages**
1. `/` - Landing page
2. `/login` - Login page
3. `/register-school` - School registration

### **Protected Pages**
4. `/system-admin` - Platform dashboard
5. `/dashboard` - School admin dashboard
6. `/dashboard/students` - Student list (placeholder)
7. `/dashboard/teachers` - Teacher list (placeholder)

## **DEVELOPMENT ORDER**

### **Day 1: Database & Backend Foundation**
1. Create minimal database schema
2. Set up FastAPI backend with CORS
3. Implement authentication endpoints
4. Implement school registration

### **Day 2: Frontend Foundation**
1. Set up Next.js with TypeScript
2. Create AuthContext with login/logout
3. Build login page
4. Build school registration page

### **Day 3: Dashboard Structure**
1. Create system admin dashboard
2. Create school admin dashboard
3. Implement protected routes
4. Add basic navigation

### **Day 4: Polish & Testing**
1. Test complete flow
2. Fix any bugs
3. Add basic styling
4. Document everything

## **SUCCESS CRITERIA**
- ✅ User can register a school
- ✅ User can login as system admin
- ✅ User can login as school admin
- ✅ Protected routes work correctly
- ✅ No broken links or errors
- ✅ Clean, maintainable code

## **TECHNICAL DECISIONS**

### **Authentication**
- Use HttpOnly cookies for security
- JWT tokens for authorization
- Simple role-based access control

### **Styling**
- Tailwind CSS for rapid development
- Simple, clean design
- Mobile-responsive from start

### **State Management**
- React Context for auth state
- Server-side props where needed
- Minimal client-side state

### **Error Handling**
- Consistent error responses
- User-friendly error messages
- Logging for debugging

## **NEXT PHASES (AFTER MVP)**
- Phase 2: Student/Teacher management
- Phase 3: Attendance system
- Phase 4: Grading system
- Phase 5: Payment processing
- Phase 6: Advanced features

Let's build this clean and simple! 🚀
