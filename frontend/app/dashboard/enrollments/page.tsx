'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';

interface Student {
  id: string;
  admission_number: string;
  first_name: string;
  last_name: string;
  current_class_id?: string;
}

interface Class {
  id: string;
  name: string;
  capacity: number;
  student_count?: number;
}

interface Session {
  id: string;
  name: string;
  is_current: boolean;
}

export default function EnrollmentsPage() {
  const { user } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [formData, setFormData] = useState({
    student_id: '',
    class_id: '',
    session_id: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [studentsRes, classesRes, sessionsRes] = await Promise.all([
        api.getStudents(),
        api.getClasses(),
        api.getSessions(),
      ]);
      
      setStudents(studentsRes.data ? (studentsRes.data as Student[]) : []);
      setClasses(classesRes.data ? (classesRes.data as Class[]) : []);
      
      if (sessionsRes.data) {
        const sessionData = sessionsRes.data as Session[];
        setSessions(sessionData);
        
        // Auto-select current session
        const currentSession = sessionData.find(s => s.is_current);
        if (currentSession) {
          setFormData(prev => ({ ...prev, session_id: currentSession.id }));
        }
      } else {
        setSessions([]);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      setStudents([]);
      setClasses([]);
      setSessions([]);
      setError('Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSubmitting(true);

    try {
      const response = await api.createEnrollment(formData);
      if (response.error) {
        setError(response.error);
      } else {
        setSuccess('Student enrolled successfully!');
        setFormData({
          student_id: '',
          class_id: '',
          session_id: formData.session_id,
        });
        setTimeout(() => setSuccess(''), 3000);
        loadData(); // Refresh to update counts
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to enroll student');
    } finally {
      setSubmitting(false);
    }
  };

  const getSelectedClass = () => {
    return classes.find(c => c.id === formData.class_id);
  };

  const selectedClass = getSelectedClass();
  const isClassFull = selectedClass && 
    typeof selectedClass.student_count === 'number' && 
    selectedClass.student_count >= selectedClass.capacity;

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Class Enrollments</h2>
        <p className="text-gray-600">Enroll students in classes for academic sessions</p>
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
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Academic Session *
                  </label>
                  <select
                    value={formData.session_id}
                    onChange={(e) => setFormData({ ...formData, session_id: e.target.value })}
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
                    Student *
                  </label>
                  <select
                    value={formData.student_id}
                    onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select Student</option>
                    {students.map(student => (
                      <option key={student.id} value={student.id}>
                        {student.first_name} {student.last_name} ({student.admission_number})
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
                    {classes.map(cls => {
                      const isFull = typeof cls.student_count === 'number' && cls.student_count >= cls.capacity;
                      return (
                        <option key={cls.id} value={cls.id} disabled={isFull}>
                          {cls.name} ({cls.student_count || 0}/{cls.capacity}) {isFull && '- FULL'}
                        </option>
                      );
                    })}
                  </select>
                  
                  {selectedClass && (
                    <div className="mt-2 text-sm">
                      <span className={`${isClassFull ? 'text-red-600' : 'text-green-600'}`}>
                        {selectedClass.student_count || 0} / {selectedClass.capacity} students
                        {isClassFull && ' - Class is full!'}
                      </span>
                    </div>
                  )}
                </div>

                <div className="pt-4 border-t">
                  <button
                    type="submit"
                    disabled={submitting || isClassFull}
                    className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
                  >
                    {submitting ? 'Enrolling...' : isClassFull ? 'Class is Full' : 'Enroll Student'}
                  </button>
                </div>
              </form>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="text-sm font-medium text-blue-900 mb-2">ℹ️ Enrollment Info</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• A student can only be enrolled in one class per session</li>
                  <li>• Classes have maximum capacity limits</li>
                  <li>• Enrollments are specific to academic sessions</li>
                  <li>• Student status will be updated to "active" upon enrollment</li>
                </ul>
              </div>

              {/* Class Capacity Overview */}
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Class Capacity Overview</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {classes.map(cls => {
                    const percentage = ((cls.student_count || 0) / cls.capacity) * 100;
                    const isFull = percentage >= 100;
                    const isAlmostFull = percentage >= 80;
                    
                    return (
                      <div key={cls.id} className="border rounded-lg p-3">
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-medium text-sm">{cls.name}</span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            isFull ? 'bg-red-100 text-red-800' : 
                            isAlmostFull ? 'bg-yellow-100 text-yellow-800' : 
                            'bg-green-100 text-green-800'
                          }`}>
                            {percentage.toFixed(0)}%
                          </span>
                        </div>
                        <div className="text-xs text-gray-600">
                          {cls.student_count || 0} / {cls.capacity} students
                        </div>
                        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              isFull ? 'bg-red-600' : 
                              isAlmostFull ? 'bg-yellow-600' : 
                              'bg-green-600'
                            }`}
                            style={{ width: `${Math.min(percentage, 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
    </DashboardLayout>
  );
}
