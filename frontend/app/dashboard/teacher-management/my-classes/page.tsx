'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/DashboardLayout';
import Link from 'next/link';

interface TeacherClass {
  id: string;
  name: string;
  level: string;
  section?: string;
  is_form_teacher: boolean;
  subjects: Array<{
    id: string;
    name: string;
  }>;
}

export default function MyClassesPage() {
  const { user } = useAuth();
  const [classes, setClasses] = useState<TeacherClass[]>([]);
  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState<any[]>([]);
  const [selectedSession, setSelectedSession] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedSession && user) {
      loadTeacherClasses();
    }
  }, [selectedSession, user]);

  const loadData = async () => {
    setLoading(true);
    try {
      const sessionsRes = await api.getSessions();
      
      if (sessionsRes.data) {
        const sessions = sessionsRes.data as any[];
        setSessions(sessions);
        // Auto-select current session
        const currentSession = sessions.find(s => s.is_current);
        if (currentSession) {
          setSelectedSession(currentSession.id);
        }
      } else {
        setSessions([]);
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  const loadTeacherClasses = async () => {
    if (!user?.id) return;
    
    try {
      // Get teacher record to find teacher_id
      const teachersRes = await api.getTeachers({ limit: 100 });
      if (!teachersRes.data) {
        setClasses([]);
        return;
      }
      
      const teachers = teachersRes.data as any[];
      const teacher = teachers.find(t => t.user_id === user.id);
      
      if (!teacher) {
        console.log('No teacher record found for user');
        setClasses([]);
        return;
      }

      const response = await api.getTeacherClasses(teacher.id, selectedSession);
      setClasses(response.data ? (response.data as TeacherClass[]) : []);
    } catch (error) {
      console.error('Error loading teacher classes:', error);
      setClasses([]);
    }
  };

  const formTeacherClass = classes.find(c => c.is_form_teacher);
  const otherClasses = classes.filter(c => !c.is_form_teacher);

  return (
    <DashboardLayout>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">My Classes</h2>
        <p className="text-gray-600 mt-1">View your teaching assignments</p>
      </div>

      <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
        <div className="max-w-md">
          <label className="block text-sm font-medium text-gray-700 mb-1">Academic Session</label>
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
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : classes.length === 0 ? (
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
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
          <p className="mt-4 text-gray-500">No classes assigned for this session</p>
          <p className="text-sm text-gray-400 mt-2">Contact your admin if you believe this is an error</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Form Teacher Class */}
          {formTeacherClass && (
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-lg border-2 border-blue-200">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-xl font-bold text-gray-900">{formTeacherClass.name}</h3>
                    <span className="px-3 py-1 text-xs font-semibold bg-blue-600 text-white rounded-full">
                      Form Teacher
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">You have special responsibilities for this class</p>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div className="bg-white p-4 rounded-lg">
                  <div className="text-sm text-gray-600 mb-2">Subjects Teaching</div>
                  <div className="flex flex-wrap gap-2">
                    {formTeacherClass.subjects.map((subject) => (
                      <span
                        key={subject.id}
                        className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full"
                      >
                        {subject.name}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg">
                  <div className="text-sm text-gray-600 mb-2">Form Teacher Capabilities</div>
                  <ul className="text-xs text-gray-700 space-y-1">
                    <li>✓ Mark attendance</li>
                    <li>✓ Add student remarks</li>
                    <li>✓ Send reports to parents</li>
                    <li>✓ View all class grades</li>
                  </ul>
                </div>
              </div>

              <div className="flex gap-2">
                <Link
                  href={`/dashboard/attendance/mark?class_id=${formTeacherClass.id}`}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                >
                  Mark Attendance
                </Link>
                <Link
                  href={`/dashboard/classes/${formTeacherClass.id}/students`}
                  className="px-4 py-2 bg-white text-blue-600 text-sm rounded-lg border border-blue-600 hover:bg-blue-50"
                >
                  View Students
                </Link>
              </div>
            </div>
          )}

          {/* Other Classes */}
          {otherClasses.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Other Teaching Assignments</h3>
              <div className="grid md:grid-cols-2 gap-4">
                {otherClasses.map((cls) => (
                  <div key={cls.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h4 className="text-lg font-semibold text-gray-900 mb-3">{cls.name}</h4>
                    
                    <div className="mb-4">
                      <div className="text-sm text-gray-600 mb-2">Subjects Teaching:</div>
                      <div className="flex flex-wrap gap-2">
                        {cls.subjects.map((subject) => (
                          <span
                            key={subject.id}
                            className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full"
                          >
                            {subject.name}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Link
                        href={`/dashboard/grading/entry?class_id=${cls.id}`}
                        className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                      >
                        Enter Grades
                      </Link>
                      <Link
                        href={`/dashboard/classes/${cls.id}/students`}
                        className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
                      >
                        View Students
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </DashboardLayout>
  );
}
