'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';

interface TeacherAssignment {
  id: string;
  teacher_id: string;
  class_id: string;
  subject_id: string;
  session_id: string;
  term_id?: string;
  is_form_teacher: boolean;
  teacher_name?: string;
  class_name?: string;
  subject_name?: string;
  created_at: string;
}

export default function TeacherAssignmentsPage() {
  const [assignments, setAssignments] = useState<TeacherAssignment[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [terms, setTerms] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filterTeacher, setFilterTeacher] = useState('');
  const [filterClass, setFilterClass] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    teacher_id: '',
    class_id: '',
    subject_id: '',
    session_id: '',
    term_id: '',
    is_form_teacher: false,
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (filterTeacher || filterClass) {
      loadAssignments();
    }
  }, [filterTeacher, filterClass]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [teachersRes, classesRes, subjectsRes, sessionsRes, termsRes, assignmentsRes] = await Promise.all([
        api.getTeachers(),
        api.getClasses(),
        api.getSubjects(),
        api.getSessions(),
        api.getTerms(),
        api.getTeacherAssignmentsPhase4(),
      ]);

      setTeachers(teachersRes.data ? (teachersRes.data as any[]) : []);
      setClasses(classesRes.data ? (classesRes.data as any[]) : []);
      setSubjects(subjectsRes.data ? (subjectsRes.data as any[]) : []);
      setSessions(sessionsRes.data ? (sessionsRes.data as any[]) : []);
      setTerms(termsRes.data ? (termsRes.data as any[]) : []);
      setAssignments(assignmentsRes.data ? (assignmentsRes.data as TeacherAssignment[]) : []);
    } catch (error) {
      console.error('Error loading data:', error);
      // Ensure states are always arrays
      setTeachers([]);
      setClasses([]);
      setSubjects([]);
      setSessions([]);
      setTerms([]);
      setAssignments([]);
    } finally {
      setLoading(false);
    }
  };

  const loadAssignments = async () => {
    try {
      const response = await api.getTeacherAssignmentsPhase4({
        teacher_id: filterTeacher || undefined,
        class_id: filterClass || undefined,
      });

      setAssignments(response.data ? (response.data as TeacherAssignment[]) : []);
    } catch (error) {
      console.error('Error loading assignments:', error);
      setAssignments([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.teacher_id || !formData.class_id || !formData.subject_id || !formData.session_id) {
      alert('Please fill all required fields');
      return;
    }

    // term_id is optional - the backend expects a real UUID or the field
    // omitted/null, not an empty string, which fails UUID validation with
    // a 422 the "Term (Optional)" dropdown's blank default value produces.
    const response = await api.createTeacherAssignment({
      ...formData,
      term_id: formData.term_id || null,
    });

    if (response.error) {
      alert(response.error);
    } else {
      await loadData();
      setShowCreateModal(false);
      resetForm();
    }
  };

  const handleDelete = async (assignmentId: string) => {
    if (!confirm('Are you sure you want to delete this assignment?')) return;

    const response = await api.deleteTeacherAssignment(assignmentId);
    if (response.error) {
      alert(response.error);
    } else {
      await loadData();
    }
  };

  const resetForm = () => {
    setFormData({
      teacher_id: '',
      class_id: '',
      subject_id: '',
      session_id: '',
      term_id: '',
      is_form_teacher: false,
    });
  };

  // Group assignments by teacher
  const groupedAssignments = assignments.reduce((acc, assignment) => {
    const key = assignment.teacher_id;
    if (!acc[key]) {
      acc[key] = {
        teacher_name: assignment.teacher_name || 'Unknown Teacher',
        teacher_id: assignment.teacher_id,
        assignments: [],
      };
    }
    acc[key].assignments.push(assignment);
    return acc;
  }, {} as Record<string, { teacher_name: string; teacher_id: string; assignments: TeacherAssignment[] }>);

  return (
    <DashboardLayout>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Teacher Assignments</h2>
        <p className="text-gray-600 mt-1">Assign teachers to classes and subjects</p>
      </div>

      <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Teacher</label>
            <select
              value={filterTeacher}
              onChange={(e) => setFilterTeacher(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">All Teachers</option>
              {teachers.map((teacher) => (
                <option key={teacher.id} value={teacher.id}>
                  {teacher.first_name} {teacher.last_name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Class</label>
            <select
              value={filterClass}
              onChange={(e) => setFilterClass(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">All Classes</option>
              {classes.map((cls) => (
                <option key={cls.id} value={cls.id}>
                  {cls.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 whitespace-nowrap"
          >
            New Assignment
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.values(groupedAssignments).length === 0 ? (
            <div className="bg-white p-12 rounded-lg shadow-sm text-center">
              <p className="text-gray-500">No assignments found. Create the first assignment to get started.</p>
            </div>
          ) : (
            Object.values(groupedAssignments).map((group) => (
              <div key={group.teacher_id} className="bg-white p-6 rounded-lg shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  {group.teacher_name}
                </h3>

                <div className="space-y-2">
                  {group.assignments.map((assignment) => (
                    <div
                      key={assignment.id}
                      className="flex items-center justify-between bg-gray-50 p-4 rounded-lg"
                    >
                      <div className="flex-1 grid grid-cols-3 gap-4">
                        <div>
                          <div className="text-xs text-gray-600">Class</div>
                          <div className="font-medium text-gray-900">{assignment.class_name}</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-600">Subject</div>
                          <div className="font-medium text-gray-900">{assignment.subject_name}</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-600">Role</div>
                          <div>
                            {assignment.is_form_teacher ? (
                              <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full font-medium">
                                Form Teacher
                              </span>
                            ) : (
                              <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">
                                Subject Teacher
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDelete(assignment.id)}
                        className="ml-4 px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-900">Create Teacher Assignment</h3>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Teacher <span className="text-red-600">*</span>
                </label>
                <select
                  value={formData.teacher_id}
                  onChange={(e) => setFormData({ ...formData, teacher_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">Select Teacher</option>
                  {teachers.map((teacher) => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.first_name} {teacher.last_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Class <span className="text-red-600">*</span>
                  </label>
                  <select
                    value={formData.class_id}
                    onChange={(e) => setFormData({ ...formData, class_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  >
                    <option value="">Select Class</option>
                    {classes.map((cls) => (
                      <option key={cls.id} value={cls.id}>
                        {cls.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subject <span className="text-red-600">*</span>
                  </label>
                  <select
                    value={formData.subject_id}
                    onChange={(e) => setFormData({ ...formData, subject_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  >
                    <option value="">Select Subject</option>
                    {subjects.map((subject) => (
                      <option key={subject.id} value={subject.id}>
                        {subject.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Session <span className="text-red-600">*</span>
                  </label>
                  <select
                    value={formData.session_id}
                    onChange={(e) => setFormData({ ...formData, session_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  >
                    <option value="">Select Session</option>
                    {sessions.map((session) => (
                      <option key={session.id} value={session.id}>
                        {session.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Term (Optional)</label>
                  <select
                    value={formData.term_id}
                    onChange={(e) => setFormData({ ...formData, term_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="">All Terms</option>
                    {terms.map((term) => (
                      <option key={term.id} value={term.id}>
                        {term.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex items-center gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <input
                  type="checkbox"
                  id="is_form_teacher"
                  checked={formData.is_form_teacher}
                  onChange={(e) => setFormData({ ...formData, is_form_teacher: e.target.checked })}
                  className="rounded"
                />
                <label htmlFor="is_form_teacher" className="text-sm text-gray-900">
                  <span className="font-medium">Designate as Form Teacher</span>
                  <p className="text-xs text-gray-600 mt-1">
                    Form teachers have special permissions for their class (mark attendance, add remarks, send reports)
                  </p>
                </label>
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Create Assignment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
