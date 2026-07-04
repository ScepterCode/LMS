'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';

interface ClassSubject {
  id: string;
  class_id: string;
  subject_id: string;
  subject_name?: string;
  session_id: string;
  is_mandatory: boolean;
  display_order: number;
}

export default function ClassSubjectsPage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [selectedSession, setSelectedSession] = useState('');
  const [classSubjects, setClassSubjects] = useState<ClassSubject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    subject_id: '',
    is_mandatory: true,
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedClass && selectedSession) {
      loadClassSubjects();
    }
  }, [selectedClass, selectedSession]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [classesRes, subjectsRes, sessionsRes] = await Promise.all([
        api.getClasses(),
        api.getSubjects(),
        api.getSessions(),
      ]);

      setClasses(classesRes.data ? (classesRes.data as any[]) : []);
      setSubjects(subjectsRes.data ? (subjectsRes.data as any[]) : []);
      
      if (sessionsRes.data) {
        const sessions = sessionsRes.data as any[];
        setSessions(sessions);
        // Auto-select current session if exists
        const currentSession = sessions.find(s => s.is_current);
        if (currentSession) setSelectedSession(currentSession.id);
      } else {
        setSessions([]);
      }
    } catch (error) {
      console.error('Error loading initial data:', error);
      setClasses([]);
      setSubjects([]);
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  const loadClassSubjects = async () => {
    if (!selectedClass || !selectedSession) return;

    try {
      const response = await api.getClassSubjects(selectedClass, selectedSession);
      setClassSubjects(response.data ? (response.data as ClassSubject[]) : []);
    } catch (error) {
      console.error('Error loading class subjects:', error);
      setClassSubjects([]);
    }
  };

  const handleAddSubject = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.subject_id) {
      alert('Please select a subject');
      return;
    }

    // Calculate next display order
    const nextOrder = classSubjects.length + 1;

    const data = {
      subject_id: formData.subject_id,
      session_id: selectedSession,
      is_mandatory: formData.is_mandatory,
      display_order: nextOrder,
    };

    const response = await api.addSubjectToClass(selectedClass, data);

    if (response.error) {
      alert(response.error);
    } else {
      await loadClassSubjects();
      setShowAddModal(false);
      setFormData({ subject_id: '', is_mandatory: true });
    }
  };

  const handleRemoveSubject = async (subjectId: string) => {
    if (!confirm('Are you sure you want to remove this subject from the class?')) return;

    const response = await api.removeSubjectFromClass(selectedClass, subjectId, selectedSession);

    if (response.error) {
      alert(response.error);
    } else {
      await loadClassSubjects();
    }
  };

  const getAvailableSubjects = () => {
    const assignedSubjectIds = classSubjects.map(cs => cs.subject_id);
    return subjects.filter(s => !assignedSubjectIds.includes(s.id));
  };

  const getClassName = () => {
    const cls = classes.find(c => c.id === selectedClass);
    return cls ? cls.name : '';
  };

  return (
    <DashboardLayout>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Class Subjects Configuration</h2>
        <p className="text-gray-600 mt-1">Define the curriculum for each class</p>
      </div>

      <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Class</label>
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Choose a class</option>
              {classes.map((cls) => (
                <option key={cls.id} value={cls.id}>
                  {cls.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Session</label>
            <select
              value={selectedSession}
              onChange={(e) => setSelectedSession(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Choose a session</option>
              {sessions.map((session) => (
                <option key={session.id} value={session.id}>
                  {session.name} {session.is_current && '(Current)'}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {selectedClass && selectedSession ? (
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-6 border-b border-gray-200 flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Subjects for {getClassName()}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {classSubjects.length} subject{classSubjects.length !== 1 ? 's' : ''} configured
              </p>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              disabled={getAvailableSubjects().length === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Add Subject
            </button>
          </div>

          <div className="p-6">
            {classSubjects.length === 0 ? (
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
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                  />
                </svg>
                <p className="mt-4 text-gray-500">No subjects configured for this class yet</p>
                <button
                  onClick={() => setShowAddModal(true)}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add First Subject
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {classSubjects
                  .sort((a, b) => a.display_order - b.display_order)
                  .map((classSubject, index) => (
                    <div
                      key={classSubject.id}
                      className="flex items-center justify-between bg-gray-50 p-4 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-semibold text-sm">
                          {index + 1}
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">
                            {classSubject.subject_name}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            {classSubject.is_mandatory ? (
                              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                                Mandatory
                              </span>
                            ) : (
                              <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded-full">
                                Optional
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveSubject(classSubject.subject_id)}
                        className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      ) : (
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
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <p className="mt-4 text-gray-500">Select a class and session to configure subjects</p>
        </div>
      )}

      {/* Add Subject Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-900">Add Subject to Class</h3>
            </div>

            <form onSubmit={handleAddSubject} className="p-6 space-y-4">
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
                  {getAvailableSubjects().map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name}
                    </option>
                  ))}
                </select>
                {getAvailableSubjects().length === 0 && (
                  <p className="text-sm text-gray-500 mt-1">All subjects have been added to this class</p>
                )}
              </div>

              <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                <input
                  type="checkbox"
                  id="is_mandatory"
                  checked={formData.is_mandatory}
                  onChange={(e) => setFormData({ ...formData, is_mandatory: e.target.checked })}
                  className="rounded"
                />
                <label htmlFor="is_mandatory" className="text-sm text-gray-700">
                  This is a mandatory subject for this class
                </label>
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    setFormData({ subject_id: '', is_mandatory: true });
                  }}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  disabled={!formData.subject_id}
                >
                  Add Subject
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
