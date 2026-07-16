/**
 * API client for Nigerian LMS
 */

// Always same-origin: next.config.ts rewrites /api/v1/* to the backend so
// the auth cookie (SameSite=Lax) stays same-site regardless of whether the
// browser opened the app via localhost or 127.0.0.1.
const API_URL = '';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  school_id: string | null;
  phone: string | null;
  is_active: boolean;
  email_verified: boolean;
  user_type?: string;
  teacher_id?: string;
  student_id?: string;
  parent_id?: string;
  is_impersonating?: boolean;
  impersonated_by?: { name: string; email: string } | null;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  status?: number;
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json();
        // Custom app exceptions (ValidationError, DuplicateRecordError, etc.)
        // are wrapped as {"error": {"message": "..."}} by the backend's
        // exception handler - only FastAPI's own validation errors use the
        // flatter {"detail": "..."} shape. Without checking error.error.message
        // first, every real backend error message was silently swallowed and
        // replaced with the generic fallback below.
        return {
          error: error.error?.message || error.detail || error.message || 'An error occurred',
          status: response.status,
        };
      }

      // Many DELETE endpoints (and a few others) return 204 No Content with
      // an empty body. Calling response.json() on that throws a SyntaxError,
      // which the catch below turned into a fake "error" even though the
      // request had already succeeded - every delete/unlink action in the
      // app showed a scary error message despite working correctly. Read as
      // text first and only parse if there's actually something to parse.
      const text = await response.text();
      const data = text ? JSON.parse(text) : undefined;
      return { data, status: response.status };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  private async requestFormData<T>(endpoint: string, formData: FormData): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        return {
          error: error.error?.message || error.detail || error.message || 'An error occurred',
        };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Generic HTTP methods
  async get<T = any>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T = any>(endpoint: string, data?: any) {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T = any>(endpoint: string, data?: any) {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T = any>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async login(credentials: LoginCredentials) {
    return this.request<{ access_token: string; user: User }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async logout() {
    return this.request<{ message: string }>('/api/v1/auth/logout', {
      method: 'POST',
    });
  }

  async getCurrentUser() {
    return this.request<User>('/api/v1/auth/me', {
      method: 'GET',
    });
  }

  async createUser(data: {
    email: string;
    password: string;
    full_name: string;
    role: string;
    phone?: string;
  }) {
    return this.request<{ id: string }>('/api/v1/users', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getUsers(params?: { skip?: number; limit?: number; role?: string; is_active?: boolean }) {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.role) queryParams.append('role', params.role);
    if (params?.is_active !== undefined) queryParams.append('is_active', String(params.is_active));

    return this.request(`/api/v1/users?${queryParams}`, { method: 'GET' });
  }

  async registerSchool(data: {
    school_name: string;
    school_email: string;
    school_phone?: string;
    school_address?: string;
    admin_name: string;
    admin_email: string;
    admin_password: string;
    admin_phone?: string;
    subscription_plan_id?: string;
  }) {
    return this.request('/api/v1/auth/register-school', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getOrganizations(params?: { skip?: number; limit?: number; status?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);
    
    return this.request(`/api/v1/system-admin/organizations?${queryParams}`, {
      method: 'GET',
    });
  }

  async getOrganization(orgId: string) {
    return this.request(`/api/v1/organizations/${orgId}`, {
      method: 'GET',
    });
  }

  async updateOrganization(orgId: string, data: { name?: string; address?: string; phone?: string; motto?: string }) {
    return this.request(`/api/v1/organizations/${orgId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async uploadOrganizationLogo(orgId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    // Don't set Content-Type here - the browser must set it (with the
    // multipart boundary) itself, which it can't do if we override it.
    return this.requestFormData<{ logo_url: string }>(`/api/v1/organizations/${orgId}/logo`, formData);
  }

  async getPlatformAnalytics() {
    return this.request('/api/v1/system-admin/analytics', {
      method: 'GET',
    });
  }

  async getSubscriptionPlans() {
    return this.request('/api/v1/system-admin/subscription-plans', {
      method: 'GET',
    });
  }

  async createSubscriptionPlan(data: {
    id: string; name: string; description?: string;
    price_monthly: number; price_yearly: number; max_students: number; features?: string[];
  }) {
    return this.request('/api/v1/system-admin/subscription-plans', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateSubscriptionPlan(planId: string, data: {
    name?: string; description?: string; price_monthly?: number; price_yearly?: number;
    max_students?: number; features?: string[]; is_active?: boolean;
  }) {
    return this.request(`/api/v1/system-admin/subscription-plans/${planId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Richer than getOrganization() above - includes cross-tenant user/campus
  // counts, system-admin only.
  async getSystemAdminOrganization(orgId: string) {
    return this.request(`/api/v1/system-admin/organizations/${orgId}`, {
      method: 'GET',
    });
  }

  async updateOrganizationStatus(orgId: string, newStatus: string) {
    return this.request(`/api/v1/system-admin/organizations/${orgId}/status?new_status=${encodeURIComponent(newStatus)}`, {
      method: 'PATCH',
    });
  }

  async createOrganizationBySystemAdmin(data: {
    school_name: string; school_email: string; school_phone?: string; school_address?: string;
    admin_name: string; admin_email: string; admin_password: string; admin_phone?: string;
    subscription_plan_id?: string; subscription_status?: string;
  }) {
    return this.request('/api/v1/system-admin/organizations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getSystemAdminUsers(params?: { skip?: number; limit?: number; role?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.role) queryParams.append('role', params.role);

    return this.request(`/api/v1/system-admin/users?${queryParams}`, {
      method: 'GET',
    });
  }

  // Generic user update/deactivate - backend already bypasses org-scoping
  // for system_admin callers, so these work cross-tenant with no backend change.
  async updateUser(userId: string, data: { full_name?: string; phone?: string; is_active?: boolean; email_verified?: boolean }) {
    return this.request(`/api/v1/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deactivateUser(userId: string) {
    return this.request(`/api/v1/users/${userId}`, {
      method: 'DELETE',
    });
  }

  async getAuditLogs(params?: { skip?: number; limit?: number; organization_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.organization_id) queryParams.append('organization_id', params.organization_id);

    return this.request(`/api/v1/system-admin/audit-logs?${queryParams}`, {
      method: 'GET',
    });
  }

  async startImpersonation(userId: string) {
    return this.request(`/api/v1/system-admin/impersonate/${userId}`, {
      method: 'POST',
    });
  }

  async exitImpersonation() {
    return this.request('/api/v1/system-admin/impersonate/exit', {
      method: 'POST',
    });
  }

  // Phase 2: Academic Sessions
  async getSessions(params?: { is_current?: boolean }) {
    const queryParams = new URLSearchParams();
    if (params?.is_current !== undefined) queryParams.append('is_current', params.is_current.toString());
    return this.request(`/api/v1/sessions?${queryParams}`, { method: 'GET' });
  }

  async getSession(sessionId: string) {
    return this.request(`/api/v1/sessions/${sessionId}`, { method: 'GET' });
  }

  async createSession(data: any) {
    return this.request('/api/v1/sessions', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateSession(sessionId: string, data: any) {
    return this.request(`/api/v1/sessions/${sessionId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteSession(sessionId: string) {
    return this.request(`/api/v1/sessions/${sessionId}`, { method: 'DELETE' });
  }

  async setCurrentSession(sessionId: string) {
    return this.request(`/api/v1/sessions/${sessionId}/set-current`, { method: 'POST' });
  }

  // Phase 2: Terms
  async getTerms(params?: { is_current?: boolean; session_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.is_current !== undefined) queryParams.append('is_current', params.is_current.toString());
    if (params?.session_id) queryParams.append('session_id', params.session_id);
    return this.request(`/api/v1/terms?${queryParams}`, { method: 'GET' });
  }

  async getTerm(termId: string) {
    return this.request(`/api/v1/terms/${termId}`, { method: 'GET' });
  }

  async createTerm(data: any) {
    return this.request('/api/v1/terms', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateTerm(termId: string, data: any) {
    return this.request(`/api/v1/terms/${termId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteTerm(termId: string) {
    return this.request(`/api/v1/terms/${termId}`, { method: 'DELETE' });
  }

  async setCurrentTerm(termId: string) {
    return this.request(`/api/v1/terms/${termId}/set-current`, { method: 'POST' });
  }

  // Phase 2: Classes
  async getClasses(params?: { level?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.level) queryParams.append('level', params.level);
    return this.request(`/api/v1/classes?${queryParams}`, { method: 'GET' });
  }

  async getClass(classId: string) {
    return this.request(`/api/v1/classes/${classId}`, { method: 'GET' });
  }

  async createClass(data: any) {
    return this.request('/api/v1/classes', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateClass(classId: string, data: any) {
    return this.request(`/api/v1/classes/${classId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteClass(classId: string) {
    return this.request(`/api/v1/classes/${classId}`, { method: 'DELETE' });
  }

  async getClassStudents(classId: string) {
    return this.request(`/api/v1/classes/${classId}/students`, { method: 'GET' });
  }

  // Phase 2: Subjects
  async getSubjects(params?: { subject_type?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.subject_type) queryParams.append('subject_type', params.subject_type);
    return this.request(`/api/v1/subjects?${queryParams}`, { method: 'GET' });
  }

  async getSubject(subjectId: string) {
    return this.request(`/api/v1/subjects/${subjectId}`, { method: 'GET' });
  }

  async createSubject(data: any) {
    return this.request('/api/v1/subjects', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateSubject(subjectId: string, data: any) {
    return this.request(`/api/v1/subjects/${subjectId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteSubject(subjectId: string) {
    return this.request(`/api/v1/subjects/${subjectId}`, { method: 'DELETE' });
  }

  // Phase 2: Students
  async getStudents(params?: { skip?: number; limit?: number; class_id?: string; status?: string; search?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.class_id) queryParams.append('class_id', params.class_id);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.search) queryParams.append('search', params.search);
    return this.request(`/api/v1/students?${queryParams}`, { method: 'GET' });
  }

  async getStudent(studentId: string) {
    return this.request(`/api/v1/students/${studentId}`, { method: 'GET' });
  }

  async createStudent(data: any) {
    return this.request('/api/v1/students', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateStudent(studentId: string, data: any) {
    return this.request(`/api/v1/students/${studentId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteStudent(studentId: string) {
    return this.request(`/api/v1/students/${studentId}`, { method: 'DELETE' });
  }

  async getStudentGuardians(studentId: string) {
    return this.request(`/api/v1/students/${studentId}/guardians`, { method: 'GET' });
  }

  async addGuardian(studentId: string, data: any) {
    return this.request(`/api/v1/students/${studentId}/guardians`, { method: 'POST', body: JSON.stringify(data) });
  }

  async updateGuardian(studentId: string, guardianId: string, data: any) {
    return this.request(`/api/v1/students/${studentId}/guardians/${guardianId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteGuardian(studentId: string, guardianId: string) {
    return this.request(`/api/v1/students/${studentId}/guardians/${guardianId}`, { method: 'DELETE' });
  }

  // Phase 2: Teachers
  async getTeachers(params?: { skip?: number; limit?: number; status?: string; search?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);
    if (params?.search) queryParams.append('search', params.search);
    return this.request(`/api/v1/teachers?${queryParams}`, { method: 'GET' });
  }

  async getTeacher(teacherId: string) {
    return this.request(`/api/v1/teachers/${teacherId}`, { method: 'GET' });
  }

  async createTeacher(data: any) {
    return this.request('/api/v1/teachers', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateTeacher(teacherId: string, data: any) {
    return this.request(`/api/v1/teachers/${teacherId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteTeacher(teacherId: string) {
    return this.request(`/api/v1/teachers/${teacherId}`, { method: 'DELETE' });
  }

  async getTeacherAssignments(teacherId: string) {
    return this.request(`/api/v1/teachers/${teacherId}/assignments`, { method: 'GET' });
  }

  async uploadTeacherPhoto(teacherId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.baseURL}/api/v1/teachers/${teacherId}/photo`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      return { error: error.detail || 'Photo upload failed' };
    }

    const data = await response.json();
    return { data };
  }

  // Phase 2: Parents
  async getParents(params?: { skip?: number; limit?: number; search?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.search) queryParams.append('search', params.search);
    return this.request(`/api/v1/parents?${queryParams}`, { method: 'GET' });
  }

  async getParent(parentId: string) {
    return this.request(`/api/v1/parents/${parentId}`, { method: 'GET' });
  }

  async createParent(data: any) {
    return this.request('/api/v1/parents', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateParent(parentId: string, data: any) {
    return this.request(`/api/v1/parents/${parentId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteParent(parentId: string) {
    return this.request(`/api/v1/parents/${parentId}`, { method: 'DELETE' });
  }

  async getParentChildren(parentId: string) {
    return this.request(`/api/v1/parents/${parentId}/children`, { method: 'GET' });
  }

  async linkParentToStudent(parentId: string, data: { student_id: string; relationship: string; is_primary?: boolean }) {
    return this.request(`/api/v1/parents/${parentId}/children`, { method: 'POST', body: JSON.stringify(data) });
  }

  async unlinkParentFromStudent(parentId: string, studentId: string) {
    return this.request(`/api/v1/parents/${parentId}/children/${studentId}`, { method: 'DELETE' });
  }

  // Phase 2: Subject Assignments
  async getSubjectAssignments(params?: { teacher_id?: string; subject_id?: string; class_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.teacher_id) queryParams.append('teacher_id', params.teacher_id);
    if (params?.subject_id) queryParams.append('subject_id', params.subject_id);
    if (params?.class_id) queryParams.append('class_id', params.class_id);
    return this.request(`/api/v1/assignments/subject?${queryParams}`, { method: 'GET' });
  }

  async createSubjectAssignment(data: any) {
    return this.request('/api/v1/assignments/subject', { method: 'POST', body: JSON.stringify(data) });
  }

  async deleteSubjectAssignment(assignmentId: string) {
    return this.request(`/api/v1/assignments/subject/${assignmentId}`, { method: 'DELETE' });
  }

  // Phase 2: Class Enrollments
  async getEnrollments(params?: { student_id?: string; class_id?: string; session_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.student_id) queryParams.append('student_id', params.student_id);
    if (params?.class_id) queryParams.append('class_id', params.class_id);
    if (params?.session_id) queryParams.append('session_id', params.session_id);
    return this.request(`/api/v1/assignments/enrollment?${queryParams}`, { method: 'GET' });
  }

  async createEnrollment(data: any) {
    return this.request('/api/v1/assignments/enrollment', { method: 'POST', body: JSON.stringify(data) });
  }

  async deleteEnrollment(enrollmentId: string) {
    return this.request(`/api/v1/assignments/enrollment/${enrollmentId}`, { method: 'DELETE' });
  }

  // Phase 4: Teacher Management - Grading Schemes
  async getGradingSchemes(params?: { session_id?: string; is_active?: boolean }) {
    const queryParams = new URLSearchParams();
    if (params?.session_id) queryParams.append('session_id', params.session_id);
    if (params?.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());
    return this.request(`/api/v1/teacher-management/grading-schemes?${queryParams}`, { method: 'GET' });
  }

  async getGradingScheme(schemeId: string) {
    return this.request(`/api/v1/teacher-management/grading-schemes/${schemeId}`, { method: 'GET' });
  }

  async createGradingScheme(data: any) {
    return this.request('/api/v1/teacher-management/grading-schemes', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateGradingScheme(schemeId: string, data: any) {
    return this.request(`/api/v1/teacher-management/grading-schemes/${schemeId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteGradingScheme(schemeId: string) {
    return this.request(`/api/v1/teacher-management/grading-schemes/${schemeId}`, { method: 'DELETE' });
  }

  // Phase 4: Class Subjects
  async getClassSubjects(classId: string, sessionId?: string) {
    const queryParams = new URLSearchParams();
    if (sessionId) queryParams.append('session_id', sessionId);
    return this.request(`/api/v1/teacher-management/classes/${classId}/subjects?${queryParams}`, { method: 'GET' });
  }

  async addSubjectToClass(classId: string, data: any) {
    return this.request(`/api/v1/teacher-management/classes/${classId}/subjects`, { method: 'POST', body: JSON.stringify(data) });
  }

  async removeSubjectFromClass(classId: string, subjectId: string, sessionId: string) {
    return this.request(`/api/v1/teacher-management/classes/${classId}/subjects/${subjectId}?session_id=${sessionId}`, { method: 'DELETE' });
  }

  // Phase 4: Teacher Class Assignments
  async getTeacherAssignmentsPhase4(params?: { teacher_id?: string; class_id?: string; session_id?: string; is_form_teacher?: boolean }) {
    const queryParams = new URLSearchParams();
    if (params?.teacher_id) queryParams.append('teacher_id', params.teacher_id);
    if (params?.class_id) queryParams.append('class_id', params.class_id);
    if (params?.session_id) queryParams.append('session_id', params.session_id);
    if (params?.is_form_teacher !== undefined) queryParams.append('is_form_teacher', params.is_form_teacher.toString());
    return this.request(`/api/v1/teacher-management/teacher-assignments?${queryParams}`, { method: 'GET' });
  }

  async getTeacherAssignmentPhase4(assignmentId: string) {
    return this.request(`/api/v1/teacher-management/teacher-assignments/${assignmentId}`, { method: 'GET' });
  }

  async createTeacherAssignment(data: any) {
    return this.request('/api/v1/teacher-management/teacher-assignments', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateTeacherAssignment(assignmentId: string, data: any) {
    return this.request(`/api/v1/teacher-management/teacher-assignments/${assignmentId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteTeacherAssignment(assignmentId: string) {
    return this.request(`/api/v1/teacher-management/teacher-assignments/${assignmentId}`, { method: 'DELETE' });
  }

  async getTeacherClasses(teacherId: string, sessionId?: string) {
    const queryParams = new URLSearchParams();
    if (sessionId) queryParams.append('session_id', sessionId);
    return this.request(`/api/v1/teacher-management/teacher-assignments/teacher/${teacherId}/classes?${queryParams}`, { method: 'GET' });
  }

  async getFormTeachers(sessionId?: string) {
    const queryParams = new URLSearchParams();
    if (sessionId) queryParams.append('session_id', sessionId);
    return this.request(`/api/v1/teacher-management/form-teachers?${queryParams}`, { method: 'GET' });
  }

  // Phase 4: Student Remarks
  async createRemark(data: any) {
    return this.request('/api/v1/teacher-management/remarks', { method: 'POST', body: JSON.stringify(data) });
  }

  async getStudentRemarks(studentId: string, params?: { session_id?: string; term_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.session_id) queryParams.append('session_id', params.session_id);
    if (params?.term_id) queryParams.append('term_id', params.term_id);
    return this.request(`/api/v1/teacher-management/remarks/student/${studentId}?${queryParams}`, { method: 'GET' });
  }

  async getClassRemarks(classId: string, params?: { session_id?: string; term_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.session_id) queryParams.append('session_id', params.session_id);
    if (params?.term_id) queryParams.append('term_id', params.term_id);
    return this.request(`/api/v1/teacher-management/remarks/class/${classId}?${queryParams}`, { method: 'GET' });
  }

  async updateRemark(remarkId: string, data: any) {
    return this.request(`/api/v1/teacher-management/remarks/${remarkId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteRemark(remarkId: string) {
    return this.request(`/api/v1/teacher-management/remarks/${remarkId}`, { method: 'DELETE' });
  }

  // Phase 5: Skill Categories & Ratings (psychomotor/affective report card domain)
  async getSkillCategories(includeInactive = false) {
    return this.request(`/api/v1/skills/categories?include_inactive=${includeInactive}`, { method: 'GET' });
  }

  async createSkillCategory(data: { name: string; domain: string; display_order?: number }) {
    return this.request('/api/v1/skills/categories', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateSkillCategory(categoryId: string, data: { name?: string; domain?: string; display_order?: number; is_active?: boolean }) {
    return this.request(`/api/v1/skills/categories/${categoryId}`, { method: 'PATCH', body: JSON.stringify(data) });
  }

  async getStudentSkillRatings(studentId: string, sessionId: string, termId: string) {
    return this.request(`/api/v1/skills/student/${studentId}?session_id=${sessionId}&term_id=${termId}`, { method: 'GET' });
  }

  async submitSkillRatings(data: { student_id: string; session_id: string; term_id: string; ratings: { skill_category_id: string; rating: number }[] }) {
    return this.request('/api/v1/skills/ratings/bulk', { method: 'POST', body: JSON.stringify(data) });
  }

  // Note: the old createReport/bulkSendReports/getReports methods (school_reports
  // table) never actually delivered report card content to parents - they
  // referenced a stale parent_student_relationships table from before the
  // parent_student_links rebuild, and logged a "pending" recipient row that
  // nothing ever marked delivered. Send Reports now works by publishing the
  // real report_cards rows directly (see publishReportCard below), which is
  // what my-children/report-cards already gate on.
  async publishReportCard(reportCardId: string) {
    return this.request(`/api/v1/grading/report-cards/${reportCardId}/publish`, { method: 'POST' });
  }

  async getReport(reportId: string) {
    return this.request(`/api/v1/teacher-management/reports/${reportId}`, { method: 'GET' });
  }

  // Phase 3: Grading
  async createAssessment(data: any) {
    return this.request('/api/v1/grading/assessments', { method: 'POST', body: JSON.stringify(data) });
  }

  async getAssessments(params?: { class_id?: string; subject_id?: string; session_id?: string; term_id?: string; assessment_type?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.class_id) queryParams.append('class_id', params.class_id);
    if (params?.subject_id) queryParams.append('subject_id', params.subject_id);
    if (params?.session_id) queryParams.append('session_id', params.session_id);
    if (params?.term_id) queryParams.append('term_id', params.term_id);
    if (params?.assessment_type) queryParams.append('assessment_type', params.assessment_type);
    return this.request(`/api/v1/grading/assessments?${queryParams}`, { method: 'GET' });
  }

  async bulkGradeEntry(data: any) {
    return this.request('/api/v1/grading/grades/bulk', { method: 'POST', body: JSON.stringify(data) });
  }

  async getStudentGrades(studentId: string, params?: { session_id?: string; term_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.session_id) queryParams.append('session_id', params.session_id);
    if (params?.term_id) queryParams.append('term_id', params.term_id);
    return this.request(`/api/v1/grading/students/${studentId}/grades?${queryParams}`, { method: 'GET' });
  }

  // Phase 3: Attendance
  async markAttendance(data: any) {
    return this.request('/api/v1/attendance/mark', { method: 'POST', body: JSON.stringify(data) });
  }

  async getAttendanceRecords(params?: { student_id?: string; class_id?: string; date?: string; status?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.student_id) queryParams.append('student_id', params.student_id);
    if (params?.class_id) queryParams.append('class_id', params.class_id);
    if (params?.date) queryParams.append('date', params.date);
    if (params?.status) queryParams.append('status', params.status);
    return this.request(`/api/v1/attendance/records?${queryParams}`, { method: 'GET' });
  }

  async getAttendanceSummary(params: { student_id?: string; class_id?: string; start_date?: string; end_date?: string }) {
    const queryParams = new URLSearchParams();
    if (params.student_id) queryParams.append('student_id', params.student_id);
    if (params.class_id) queryParams.append('class_id', params.class_id);
    if (params.start_date) queryParams.append('start_date', params.start_date);
    if (params.end_date) queryParams.append('end_date', params.end_date);
    return this.request(`/api/v1/attendance/summary?${queryParams}`, { method: 'GET' });
  }

  // Phase 3: Fees
  async createFeeStructure(data: any) {
    return this.request('/api/v1/fees/structures', { method: 'POST', body: JSON.stringify(data) });
  }

  async getFeeStructures(params?: { class_id?: string; session_id?: string; term_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.class_id) queryParams.append('class_id', params.class_id);
    if (params?.session_id) queryParams.append('session_id', params.session_id);
    if (params?.term_id) queryParams.append('term_id', params.term_id);
    return this.request(`/api/v1/fees/structures?${queryParams}`, { method: 'GET' });
  }

  async recordPayment(data: any) {
    return this.request('/api/v1/fees/payments', { method: 'POST', body: JSON.stringify(data) });
  }

  async getStudentPayments(studentId: string, params?: { session_id?: string; term_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.session_id) queryParams.append('session_id', params.session_id);
    if (params?.term_id) queryParams.append('term_id', params.term_id);
    return this.request(`/api/v1/fees/students/${studentId}/payments?${queryParams}`, { method: 'GET' });
  }
}

export const api = new ApiClient(API_URL);
