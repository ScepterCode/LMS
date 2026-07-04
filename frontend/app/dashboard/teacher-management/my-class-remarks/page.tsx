'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/DashboardLayout';

interface Remark {
  id: string;
  student_id: string;
  student_name?: string;
  remark_text: string;
  remarks_category: string;
  created_at: string;
  updated_at: string;
}

export default function MyClassRemarksPage() {
  const { user } = useAuth();
  const [remarks, setRemarks] = useState<Remark[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [terms, setTerms] = useState<any[]>([]);
  const [formTeacherClass, setFormTeacherClass] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingRemark, setEditingRemark] = useState<Remark | null>(null);
  
  const [selectedSession, setSelectedSession] = useState('');
  const [selectedTerm, setSelectedTerm] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    student_id: '',
    remark_text: '',
    remarks_category: 'form_teacher_comment',
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedSession && user) {
      loadFormTeacherClass();
    }
  }, [selectedSession, user]);

  useEffect(() => {
    if (formTeacherClass && selectedSession && selectedTerm) {
      loadRemarks();
    }
  }, [formTeacherClass, selectedSession, selectedTerm]);

  const loadInitialData = async () => {
    setLoading(true);
    
    try {
      // Get sessions and terms
      const [sessionsRes, termsRes] = await Promise.all([
        api.getSessions(),
        api.getTerms(),
      ]);

      if (sessionsRes.data) {
        const sessions = sessionsRes.data as any[];
        setSessions(sessions);
        const currentSession = sessions.find(s => s.is_current);
        if (currentSession) setSelectedSession(currentSession.id);
      } else {
        setSessions([]);
      }

      if (termsRes.data) {
        const terms = termsRes.data as any[];
        setTerms(terms);
        const currentTerm = terms.find(t => t.is_current);
        if (currentTerm) setSelectedTerm(currentTerm.id);
      } else {
        setTerms([]);
      }
    } catch (error) {
      console.error('Error loading initial data:', error);
      setSessions([]);
      setTerms([]);
    } finally {
      setLoading(false);
    }
  };

  const loadFormTeacherClass = async () => {
    if (!user?.id) return;

    try {
      // Get teacher record
      const teachersRes = await api.getTeachers({ limit: 100 });
      if (!teachersRes.data) return;

      const teachers = teachersRes.data as any[];
      const teacher = teachers.find(t => t.user_id === user.id);
      if (!teacher) return;

      // Get teacher's classes
      const classesRes = await api.getTeacherClasses(teacher.id, selectedSession);
      if (!classesRes.data) return;

      const classes = classesRes.data as any[];
      const formClass = classes.find(c => c.is_form_teacher);
      
      if (formClass) {
        setFormTeacherClass(formClass);
        // Load students in this class
        const studentsRes = await api.getClassStudents(formClass.id);
        setStudents(studentsRes.data ? (studentsRes.data as any[]) : []);
      }
    } catch (error) {
      console.error('Error loading form teacher class:', error);
      setStudents([]);
    }
  };

  const loadRemarks = async () => {
    if (!formTeacherClass) return;

    try {
      const response = await api.getClassRemarks(formTeacherClass.id, {
        session_id: selectedSession,
        term_id: selectedTerm,
      });

      setRemarks(response.data ? (response.data as Remark[]) : []);
    } catch (error) {
      console.error('Error loading remarks:', error);
      setRemarks([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.student_id || !formData.remark_text) {
      alert('Please fill all required fields');
      return;
    }

    const data = {
      student_id: formData.student_id,
      class_id: formTeacherClass.id,
      session_id: selectedSession,
      term_id: selectedTerm,
      remark_text: formData.remark_text,
      remarks_category: formData.remarks_category,
    };

    const response = editingRemark
      ? await api.updateRemark(editingRemark.id, { remark_text: formData.remark_text, remarks_category: formData.remarks_category })
      : await api.createRemark(data);

    if (response.error) {
      alert(response.error);
    } else {
      await loadRemarks();
      setShowAddModal(false);
      setEditingRemark(null);
      resetForm();
    }
  };

  const handleEdit = (remark: Remark) => {
    setEditingRemark(remark);
    setFormData({
      student_id: remark.student_id,
      remark_text: remark.remark_text,
      remarks_category: remark.remarks_category,
    });
    setShowAddModal(true);
  };

  const handleDelete = async (remarkId: string) => {
    if (!confirm('Are you sure you want to delete this remark?')) return;

    const response = await api.deleteRemark(remarkId);
    if (response.error) {
      alert(response.error);
    } else {
      await loadRemarks();
    }
  };

  const resetForm = () => {
    setFormData({
      student_id: '',
      remark_text: '',
      remarks_category: 'form_teacher_comment',
    });
  };

  const handleCloseModal = () => {
    setShowAddModal(false);
    setEditingRemark(null);
    resetForm();
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (!formTeacherClass) {
    return (
      <DashboardLayout>
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Class Remarks</h2>
        </div>
        <div className="bg-white p-12 rounded-lg shadow-sm text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <p className="mt-4 text-gray-500">You are not assigned as a form teacher</p>
          <p className="text-sm text-gray-400 mt-2">Only form teachers can add remarks to student report cards</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Class Remarks</h2>
        <p className="text-gray-600 mt-1">Add remarks to your form teacher class: {formTeacherClass.name}</p>
      </div>

      <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Session</label>
            <select
              value={selectedSession}
              onChange={(e) => setSelectedSession(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Select Session</option>
              {sessions.map((session) => (
                <option key={session.id} value={session.id}>
                  {session.name} {session.is_current && '(Current)'}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Term</label>
            <select
              value={selectedTerm}
              onChange={(e) => setSelectedTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Select Term</option>
              {terms.map((term) => (
                <option key={term.id} value={term.id}>
                  {term.name} {term.is_current && '(Current)'}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => setShowAddModal(true)}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Add Remark
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Remarks for {formTeacherClass.name}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {remarks.length} remark{remarks.length !== 1 ? 's' : ''} added
          </p>
        </div>

        <div className="p-6">
          {remarks.length === 0 ? (
            <div className="text-center py-12">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
                />
              </svg>
              <p className="mt-4 text-gray-500">No remarks added yet</p>
              <button
                onClick={() => setShowAddModal(true)}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Add First Remark
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {remarks.map((remark) => (
                <div key={remark.id} className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-medium text-gray-900">{remark.student_name}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(remark.created_at).toLocaleDateString()} · {remark.remarks_category}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(remark)}
                        className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(remark.id)}
                        className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <p className="text-gray-700 text-sm">{remark.remark_text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-900">
                {editingRemark ? 'Edit Remark' : 'Add Remark'}
              </h3>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Student <span className="text-red-600">*</span>
                </label>
                <select
                  value={formData.student_id}
                  onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                  disabled={!!editingRemark}
                >
                  <option value="">Select Student</option>
                  {students.map((student) => (
                    <option key={student.id} value={student.id}>
                      {student.first_name} {student.last_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  value={formData.remarks_category}
                  onChange={(e) => setFormData({ ...formData, remarks_category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="form_teacher_comment">Form Teacher Comment</option>
                  <option value="conduct">Conduct</option>
                  <option value="academic">Academic Performance</option>
                  <option value="behavioral">Behavioral</option>
                  <option value="general">General</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Remark <span className="text-red-600">*</span>
                </label>
                <textarea
                  value={formData.remark_text}
                  onChange={(e) => setFormData({ ...formData, remark_text: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  rows={4}
                  placeholder="Enter your remark about the student..."
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  This will appear on the student's report card
                </p>
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {editingRemark ? 'Update Remark' : 'Add Remark'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
