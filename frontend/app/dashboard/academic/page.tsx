'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';

interface Session {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
}

interface Class {
  id: string;
  name: string;
  level: string;
  section?: string;
  capacity: number;
  student_count?: number;
  class_teacher_name?: string;
}

interface Subject {
  id: string;
  name: string;
  code?: string;
  subject_type: string;
  teacher_count?: number;
}

type ModalType = 'session' | 'class' | 'subject' | null;

export default function AcademicPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'sessions' | 'classes' | 'subjects'>('sessions');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState<ModalType>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [loadError, setLoadError] = useState('');  // New: for API load errors
  
  // Form states
  const [sessionForm, setSessionForm] = useState({
    name: '',
    start_date: '',
    end_date: '',
    is_current: false,
  });
  
  const [classForm, setClassForm] = useState({
    name: '',
    level: 'Junior',
    section: '',
    capacity: 40,
    selected_subjects: [] as string[],
  });
  
  const [subjectForm, setSubjectForm] = useState({
    name: '',
    code: '',
    subject_type: 'core',
    description: '',
  });

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    setLoadError('');
    try {
      if (activeTab === 'sessions') {
        const response = await api.getSessions();
        if (response.error) {
          // Check for authentication errors
          const isAuthError = response.error.toLowerCase().includes('unauthorized') || 
                             response.error.toLowerCase().includes('forbidden') ||
                             response.error.toLowerCase().includes('authentication');
          
          if (isAuthError) {
            setLoadError('Authentication required. Please log out and log in again.');
            setSessions([]);
          } else {
            setLoadError(response.error);
            setSessions([]);
          }
        } else {
          setSessions(response.data ? (response.data as Session[]) : []);
        }
      } else if (activeTab === 'classes') {
        const response = await api.getClasses();
        if (response.error) {
          setLoadError(response.error);
          setClasses([]);
        } else {
          setClasses(response.data ? (response.data as Class[]) : []);
        }
      } else if (activeTab === 'subjects') {
        const response = await api.getSubjects();
        if (response.error) {
          setLoadError(response.error);
          setSubjects([]);
        } else {
          setSubjects(response.data ? (response.data as Subject[]) : []);
        }
      }
    } catch (error) {
      console.error('Error loading data:', error);
      setLoadError('Failed to load data');
      if (activeTab === 'sessions') {
        setSessions([]);
      } else if (activeTab === 'classes') {
        setClasses([]);
      } else if (activeTab === 'subjects') {
        setSubjects([]);
      }
    } finally {
      setLoading(false);
    }
  };
  
  const resetForms = () => {
    setSessionForm({ name: '', start_date: '', end_date: '', is_current: false });
    setClassForm({ name: '', level: 'Junior', section: '', capacity: 40, selected_subjects: [] });
    setSubjectForm({ name: '', code: '', subject_type: 'core', description: '' });
    setError('');
  };
  
  const handleOpenModal = (type: ModalType) => {
    resetForms();
    setShowModal(type);
  };
  
  const handleCloseModal = () => {
    setShowModal(null);
    resetForms();
  };
  
  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // Validate session name format (YYYY/YYYY)
    const namePattern = /^\d{4}\/\d{4}$/;
    if (!namePattern.test(sessionForm.name)) {
      setError('Session name must be in format YYYY/YYYY (e.g., 2024/2025)');
      return;
    }
    
    // Validate that second year is one year after first
    const [year1, year2] = sessionForm.name.split('/').map(Number);
    if (year2 !== year1 + 1) {
      setError('Second year must be exactly one year after the first year');
      return;
    }
    
    // Validate dates
    if (!sessionForm.start_date || !sessionForm.end_date) {
      setError('Both start and end dates are required');
      return;
    }
    
    if (new Date(sessionForm.end_date) <= new Date(sessionForm.start_date)) {
      setError('End date must be after start date');
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
  
  const handleCreateClass = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    
    try {
      // Step 1: Create the class
      const response = await api.createClass({
        name: classForm.name,
        level: classForm.level,
        section: classForm.section || undefined,
        capacity: classForm.capacity,
      });
      
      if (response.error) {
        setError(response.error);
        setSubmitting(false);
        return;
      }
      
      // Step 2: Add selected subjects to the class
      const classId = (response.data as any)?.id;
      if (classId && classForm.selected_subjects.length > 0) {
        // Get current session
        const sessionsResponse = await api.getSessions();
        const currentSession = (sessionsResponse.data as Session[] | undefined)?.find((s: Session) => s.is_current);
        
        if (currentSession) {
          // Add each subject to the class
          for (const subjectId of classForm.selected_subjects) {
            await api.addSubjectToClass(classId, {
              subject_id: subjectId,
              session_id: currentSession.id,
              is_mandatory: true,
            });
          }
        }
      }
      
      handleCloseModal();
      loadData();
    } catch (err) {
      setError('Failed to create class');
    } finally {
      setSubmitting(false);
    }
  };
  
  const handleCreateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    
    try {
      const response = await api.createSubject({
        ...subjectForm,
        code: subjectForm.code || undefined,
        description: subjectForm.description || undefined,
      });
      if (response.error) {
        setError(response.error);
      } else {
        handleCloseModal();
        loadData();
      }
    } catch (err) {
      setError('Failed to create subject');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Academic Management</h2>
        <p className="text-gray-600">Manage sessions, classes, and subjects</p>
      </div>

      {/* Authentication Error Alert */}
      {loadError && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="text-sm font-medium text-red-800">Error Loading Data</h3>
              <p className="mt-1 text-sm text-red-700">{loadError}</p>
              {loadError.toLowerCase().includes('authentication') && (
                <button 
                  onClick={() => window.location.href = '/login'}
                  className="mt-2 text-sm font-medium text-red-600 hover:text-red-800 underline"
                >
                  Click here to log in again
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('sessions')}
                className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'sessions'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Academic Sessions
              </button>
              <button
                onClick={() => setActiveTab('classes')}
                className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'classes'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Classes
              </button>
              <button
                onClick={() => setActiveTab('subjects')}
                className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'subjects'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Subjects
              </button>
            </nav>
          </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {/* Sessions Tab */}
              {activeTab === 'sessions' && (
                <div>
                  <div className="mb-4 flex justify-end">
                    <button 
                      onClick={() => handleOpenModal('session')}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      + Add Session
                    </button>
                  </div>

                  {sessions.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                      <h3 className="text-sm font-medium text-gray-900">No sessions found</h3>
                      <p className="mt-1 text-sm text-gray-500">Create your first academic session.</p>
                    </div>
                  ) : (
                    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Session</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Start Date</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">End Date</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {sessions.map((session) => (
                            <tr key={session.id} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {session.name}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {new Date(session.start_date).toLocaleDateString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {new Date(session.end_date).toLocaleDateString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                {session.is_current ? (
                                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                    Current
                                  </span>
                                ) : (
                                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                                    Inactive
                                  </span>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <button className="text-blue-600 hover:text-blue-900 mr-4">Edit</button>
                                <button className="text-gray-600 hover:text-gray-900">Delete</button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Classes Tab */}
              {activeTab === 'classes' && (
                <div>
                  <div className="mb-4 flex justify-end">
                    <button 
                      onClick={() => handleOpenModal('class')}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      + Add Class
                    </button>
                  </div>

                  {classes.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                      <h3 className="text-sm font-medium text-gray-900">No classes found</h3>
                      <p className="mt-1 text-sm text-gray-500">Create your first class.</p>
                    </div>
                  ) : (
                    <div className="grid md:grid-cols-3 gap-4">
                      {classes.map((cls) => (
                        <div key={cls.id} className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <h3 className="text-lg font-semibold text-gray-900">{cls.name}</h3>
                              <p className="text-sm text-gray-500">{cls.level}</p>
                            </div>
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                              {cls.section || 'Main'}
                            </span>
                          </div>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Students:</span>
                              <span className="font-medium">{cls.student_count || 0} / {cls.capacity}</span>
                            </div>
                            {cls.class_teacher_name && (
                              <div className="flex justify-between">
                                <span className="text-gray-600">Teacher:</span>
                                <span className="font-medium">{cls.class_teacher_name}</span>
                              </div>
                            )}
                          </div>
                          <div className="mt-4 pt-4 border-t flex justify-end gap-2">
                            <button className="text-sm text-blue-600 hover:text-blue-800">Edit</button>
                            <button className="text-sm text-gray-600 hover:text-gray-800">Delete</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Subjects Tab */}
              {activeTab === 'subjects' && (
                <div>
                  <div className="mb-4 flex justify-end">
                    <button 
                      onClick={() => handleOpenModal('subject')}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      + Add Subject
                    </button>
                  </div>

                  {subjects.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                      <h3 className="text-sm font-medium text-gray-900">No subjects found</h3>
                      <p className="mt-1 text-sm text-gray-500">Create your first subject.</p>
                    </div>
                  ) : (
                    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject Name</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Teachers</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {subjects.map((subject) => (
                            <tr key={subject.id} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {subject.name}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {subject.code || '-'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                  subject.subject_type === 'core' 
                                    ? 'bg-blue-100 text-blue-800' 
                                    : 'bg-purple-100 text-purple-800'
                                }`}>
                                  {subject.subject_type}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {subject.teacher_count || 0}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <button className="text-blue-600 hover:text-blue-900 mr-4">Edit</button>
                                <button className="text-gray-600 hover:text-gray-900">Delete</button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

        {/* Session Modal */}
        {showModal === 'session' && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">Create Academic Session</h3>
              
              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                  {error}
                </div>
              )}
              
              <form onSubmit={handleCreateSession}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Session Name *
                    </label>
                    <input
                      type="text"
                      value={sessionForm.name}
                      onChange={(e) => setSessionForm({ ...sessionForm, name: e.target.value })}
                      placeholder="e.g., 2024/2025"
                      required
                      pattern="\d{4}/\d{4}"
                      title="Format: YYYY/YYYY (e.g., 2024/2025)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="mt-1 text-xs text-gray-500">Format: YYYY/YYYY (e.g., 2024/2025)</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date *
                    </label>
                    <input
                      type="date"
                      value={sessionForm.start_date}
                      onChange={(e) => setSessionForm({ ...sessionForm, start_date: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Date *
                    </label>
                    <input
                      type="date"
                      value={sessionForm.end_date}
                      onChange={(e) => setSessionForm({ ...sessionForm, end_date: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_current"
                      checked={sessionForm.is_current}
                      onChange={(e) => setSessionForm({ ...sessionForm, is_current: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="is_current" className="ml-2 block text-sm text-gray-700">
                      Set as current session
                    </label>
                  </div>
                </div>
                
                <div className="mt-6 flex gap-3">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    {submitting ? 'Creating...' : 'Create Session'}
                  </button>
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Class Modal */}
        {showModal === 'class' && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">Create Class</h3>
              
              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                  {error}
                </div>
              )}
              
              <form onSubmit={handleCreateClass}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Class Name *
                    </label>
                    <input
                      type="text"
                      value={classForm.name}
                      onChange={(e) => setClassForm({ ...classForm, name: e.target.value })}
                      placeholder="e.g., JSS 1, SS 2"
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Level *
                    </label>
                    <select
                      value={classForm.level}
                      onChange={(e) => setClassForm({ ...classForm, level: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="Junior">Junior</option>
                      <option value="Senior">Senior</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Section
                    </label>
                    <input
                      type="text"
                      value={classForm.section}
                      onChange={(e) => setClassForm({ ...classForm, section: e.target.value })}
                      placeholder="e.g., A, B, C (optional)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Capacity *
                    </label>
                    <input
                      type="number"
                      value={classForm.capacity}
                      onChange={(e) => setClassForm({ ...classForm, capacity: parseInt(e.target.value) })}
                      min="1"
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Subjects Offered in This Class
                    </label>
                    <div className="border border-gray-300 rounded-lg p-3 max-h-48 overflow-y-auto">
                      {subjects.length === 0 ? (
                        <p className="text-sm text-gray-500">No subjects available. Create subjects first.</p>
                      ) : (
                        <div className="space-y-2">
                          {subjects.map((subject) => (
                            <label key={subject.id} className="flex items-center">
                              <input
                                type="checkbox"
                                checked={classForm.selected_subjects.includes(subject.id)}
                                onChange={(e) => {
                                  const newSelected = e.target.checked
                                    ? [...classForm.selected_subjects, subject.id]
                                    : classForm.selected_subjects.filter(id => id !== subject.id);
                                  setClassForm({ ...classForm, selected_subjects: newSelected });
                                }}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                              />
                              <span className="ml-2 text-sm text-gray-700">{subject.name}</span>
                            </label>
                          ))}
                        </div>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-gray-500">
                      {classForm.selected_subjects.length} subject{classForm.selected_subjects.length !== 1 ? 's' : ''} selected
                    </p>
                  </div>
                </div>
                
                <div className="mt-6 flex gap-3">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    {submitting ? 'Creating...' : 'Create Class'}
                  </button>
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Subject Modal */}
        {showModal === 'subject' && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">Create Subject</h3>
              
              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                  {error}
                </div>
              )}
              
              <form onSubmit={handleCreateSubject}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Subject Name *
                    </label>
                    <input
                      type="text"
                      value={subjectForm.name}
                      onChange={(e) => setSubjectForm({ ...subjectForm, name: e.target.value })}
                      placeholder="e.g., Mathematics, English"
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Subject Code
                    </label>
                    <input
                      type="text"
                      value={subjectForm.code}
                      onChange={(e) => setSubjectForm({ ...subjectForm, code: e.target.value })}
                      placeholder="e.g., MATH101 (optional)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Subject Type *
                    </label>
                    <select
                      value={subjectForm.subject_type}
                      onChange={(e) => setSubjectForm({ ...subjectForm, subject_type: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="core">Core</option>
                      <option value="elective">Elective</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={subjectForm.description}
                      onChange={(e) => setSubjectForm({ ...subjectForm, description: e.target.value })}
                      rows={3}
                      placeholder="Brief description (optional)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                
                <div className="mt-6 flex gap-3">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    {submitting ? 'Creating...' : 'Create Subject'}
                  </button>
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
    </DashboardLayout>
  );
}
