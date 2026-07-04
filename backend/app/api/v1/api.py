"""
API router for version 1 of the Nigerian LMS API.
This module combines all endpoint routers.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, 
    system_admin, 
    organizations, 
    sessions, 
    terms,
    classes, 
    subjects, 
    students, 
    teachers,
    parents,
    assignments,
    grading,
    attendance,
    fees,
    teacher_management,
    users,
    registration
)

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(system_admin.router, prefix="/system-admin", tags=["System Administration"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Academic Sessions"])
api_router.include_router(terms.router, prefix="/terms", tags=["Terms"])
api_router.include_router(classes.router, prefix="/classes", tags=["Classes"])
api_router.include_router(subjects.router, prefix="/subjects", tags=["Subjects"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(teachers.router, prefix="/teachers", tags=["Teachers"])
api_router.include_router(parents.router, prefix="/parents", tags=["Parents"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["Assignments & Enrollments"])
api_router.include_router(grading.router, prefix="/grading", tags=["Grading & Assessments"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance Management"])
api_router.include_router(fees.router, prefix="/fees", tags=["Fee Management"])
api_router.include_router(teacher_management.router, prefix="/teacher-management", tags=["Phase 4: Teacher Management"])

# NEW: User Management & Integrated Registration
from app.api.v1.endpoints import users, registration
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(registration.router, prefix="/registration", tags=["Integrated Registration"])

# Health check endpoint (not versioned)
@api_router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for API v1."""
    return {
        "status": "healthy",
        "version": "v1",
        "phase": "Phase 4 In Progress - Teacher Class Management",
        "endpoints": {
            "auth": ["/auth/login", "/auth/logout", "/auth/me", "/auth/register-school"],
            "system_admin": ["/system-admin/organizations", "/system-admin/analytics"],
            "organizations": ["/organizations/{id}", "/organizations/{id}/users"],
            "sessions": ["/sessions", "/sessions/{id}", "/sessions/{id}/set-current"],
            "terms": ["/terms", "/terms/{id}", "/terms/{id}/set-current"],
            "classes": ["/classes", "/classes/{id}", "/classes/{id}/students"],
            "subjects": ["/subjects", "/subjects/{id}"],
            "students": ["/students", "/students/{id}", "/students/{id}/guardians"],
            "teachers": ["/teachers", "/teachers/{id}", "/teachers/{id}/assignments"],
            "parents": ["/parents", "/parents/{id}", "/parents/{id}/children"],
            "assignments": ["/assignments/subject", "/assignments/enrollment"],
            "grading": ["/grading/assessment-types", "/grading/assessments", "/grading/grades", "/grading/report-cards"],
            "attendance": ["/attendance/mark", "/attendance/class/{id}", "/attendance/student/{id}", "/attendance/leave-requests"],
            "fees": ["/fees/categories", "/fees/structures", "/fees/student-fees", "/fees/payments"],
            "teacher_management": [
                "/teacher-management/grading-schemes", 
                "/teacher-management/classes/{id}/subjects",
                "/teacher-management/teacher-assignments",
                "/teacher-management/remarks",
                "/teacher-management/reports"
            ]
        }
    }