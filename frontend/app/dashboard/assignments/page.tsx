'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';

interface Teacher {
  id: string;
  staff_number: string;
  first_name: string;
  last_name: string;
}

interface Subject {
  id: string;
  name: string;
  code?: string;
}

interface Class {
  id: string;
  name: string;
}

interface Session {
  id: string;
  name: string;
  is_current: boolean;
}

interface Term {
  id: string;
  name: string;
  is_current: boolean;
}

export default function AssignmentsPage() {
  const { user } = useAuth();
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [terms, setTerms] = useState<Term[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [formData, setFormData] = useState({
    teacher_id: '',
    subject_id: '',
    class_id: '',
    session_id: '',
    term_id: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [teachersRes, subjectsRes, classesRes, sessionsRes] = await Promise.all([
        api.getTeachers(),
        api.getSubjects(),
        api.getClasses(),
        api.getSessions(),
      ]);
      
      setTeachers(teachersRes.data ? (teachersRes.data as Teacher[]) : []);
      setSubjects(subjectsRes.data ? (subjectsRes.data as Subject[]) : []);
      setClasses(classesRes.data ? (classesRes.data as Class[]) : []);
      
      if (sessionsRes.data) {
        const sessionData = sessionsRes.data as Session[];
        setSessions(sessionData);
        
        // Auto-select current session
        const currentSession = sessionData.find(s => s.is_current);
        if (currentSession) {
          setFormData(prev => ({ ...prev, session_id: currentSession.id }));
          // Load terms for current session
          loadTerms(currentSession.id);
        }
      } else {
        setSessions([]);
      }
    } catch (err) {
      console.error('Failed to load data:', err);
      setTeachers([]);
      setSubjects([]);
      setClasses([]);
      setSessions([]);
      setError('Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadTerms = async (sessionId: string) => {
    try {
      const response = await api.getTerms({ session_id: sessionId });
      const termData = response.data ? (response.data as Term[]) : [];
      setTerms(termData);
      
      // Auto-select current term
      const currentTerm = termData.find(t => t.is_current);
      if (currentTerm) {
        setFormData(prev => ({ ...prev, term_id: currentTerm.id }));
      }
    } catch (err) {
      console.error('Failed to load terms:', err);
    }
  };

  const handleSessionChange = (sessionId: string) => {
    setFormData(prev => ({ ...prev, session_id: sessionId, term_id: '' }));
    if (sessionId) {
      loadTerms(sessionId);
    } else {
      setTerms([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSubmitting(true);

    try {
      const response = await api.createSubjectAssignment(formData);
      if (response.error) {
        setError(response.error);
      } else {
        setSuccess('Teacher assigned to subject successfully!');
        setFormData({
          teacher_id: '',
          subject_id: '',
          class_id: '',
          session_id: formData.session_id,
          term_id: formData.term_id,
        });
        setTimeout(() => setSuccess(''), 3000);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create assignment');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Subject Assignments</h2>
        <p className="text-gray-600">Assign teachers to subjects for specific classes and terms</p>
      </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                  {error}
                </div>
              )}

              {success && (
                <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
                  {success}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Academic Session *
                    </label>
                    <select
                      value={formData.session_id}
                      onChange={(e) => handleSessionChange(e.target.value)}
                      required
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Session</option>
                      {sessions.map(session => (
                        <option key={session.id} value={session.id}>
                          {session.name} {session.is_current && '(Current)'}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Term *
                    </label>
                    <select
                      value={formData.term_id}
                      onChange={(e) => setFormData({ ...formData, term_id: e.target.value })}
                      required
                      disabled={!formData.session_id}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                    >
                      <option value="">Select Term</option>
                      {terms.map(term => (
                        <option key={term.id} value={term.id}>
                          {term.name} {term.is_current && '(Current)'}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Teacher *
                  </label>
                  <select
                    value={formData.teacher_id}
                    onChange={(e) => setFormData({ ...formData, teacher_id: e.target.value })}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select Teacher</option>
                    {teachers.map(teacher => (
                      <option key={teacher.id} value={teacher.id}>
                        {teacher.first_name} {teacher.last_name} ({teacher.staff_number})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Subject *
                    </label>
                    <select
                      value={formData.subject_id}
                      onChange={(e) => setFormData({ ...formData, subject_id: e.target.value })}
                      required
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Subject</option>
                      {subjects.map(subject => (
                        <option key={subject.id} value={subject.id}>
                          {subject.name} {subject.code && `(${subject.code})`}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Class *
                    </label>
                    <select
                      value={formData.class_id}
                      onChange={(e) => setFormData({ ...formData, class_id: e.target.value })}
                      required
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Class</option>
                      {classes.map(cls => (
                        <option key={cls.id} value={cls.id}>
                          {cls.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
                  >
                    {submitting ? 'Assigning...' : 'Assign Teacher to Subject'}
                  </button>
                </div>
              </form>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="text-sm font-medium text-blue-900 mb-2">ℹ️ Assignment Info</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• One teacher can teach multiple subjects</li>
                  <li>• One subject can be taught by multiple teachers (different classes)</li>
                  <li>• Assignments are specific to a session and term</li>
                  <li>• Teachers must be registered before assignment</li>
                </ul>
              </div>
            </div>
          )}
    </DashboardLayout>
  );
}
