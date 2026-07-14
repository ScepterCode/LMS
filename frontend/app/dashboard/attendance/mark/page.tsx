'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';

interface Class {
  id: string;
  name: string;
}

interface Student {
  id: string;
  admission_number: string;
  first_name: string;
  last_name: string;
}

interface AttendanceRecord {
  student_id: string;
  status: 'present' | 'absent' | 'late' | 'excused';
  check_in_time?: string;
  minutes_late?: number;
  reason?: string;
}

function MarkAttendancePageContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const [classes, setClasses] = useState<Class[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedClass, setSelectedClass] = useState(() => searchParams.get('class_id') || '');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [attendance, setAttendance] = useState<Record<string, AttendanceRecord>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [existingAttendance, setExistingAttendance] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState('');
  const [currentTermId, setCurrentTermId] = useState('');

  useEffect(() => {
    if (user) fetchClasses();
    fetchCurrentSessionAndTerm();
  }, [user]);

  const fetchCurrentSessionAndTerm = async () => {
    try {
      const sessionsRes = await api.getSessions({ is_current: true });
      const sessions = sessionsRes.data as any[] | undefined;
      const currentSession = sessions?.[0];
      if (currentSession) {
        setCurrentSessionId(currentSession.id);

        const termsRes = await api.getTerms({ is_current: true, session_id: currentSession.id });
        const terms = termsRes.data as any[] | undefined;
        if (terms?.[0]) {
          setCurrentTermId(terms[0].id);
        }
      }
    } catch (error) {
      console.error('Error fetching current session/term:', error);
    }
  };

  useEffect(() => {
    if (selectedClass && selectedDate) {
      fetchStudentsAndAttendance();
    }
  }, [selectedClass, selectedDate]);

  const fetchClasses = async () => {
    try {
      // Teachers can only mark attendance for a class they're the form
      // teacher of - the backend already enforces this, but the class
      // picker previously listed every class in the school regardless of
      // role, so a non-form-teacher could select a class just to be
      // rejected on save. Scope the picker itself to match.
      if (user?.role === 'teacher') {
        if (!user.teacher_id) {
          setClasses([]);
          return;
        }
        const response = await api.getTeacherClasses(user.teacher_id);
        const teacherClasses = (response.data as any[]) || [];
        setClasses(teacherClasses.filter((c) => c.is_form_teacher));
        return;
      }

      const response = await api.get('/api/v1/classes');
      setClasses(response.data ? (response.data as Class[]) : []);
    } catch (error) {
      console.error('Error fetching classes:', error);
      setClasses([]);
    }
  };

  const fetchStudentsAndAttendance = async () => {
    setLoading(true);
    try {
      // Fetch students in class
      const studentsRes = await api.get(`/api/v1/classes/${selectedClass}/students`);
      const studentsData = studentsRes.data ? (studentsRes.data as Student[]) : [];
      setStudents(studentsData);
      
      // Try to fetch existing attendance for this date
      try {
        const attendanceRes = await api.get(
          `/api/v1/attendance/class/${selectedClass}/date/${selectedDate}`
        );
        
        if (attendanceRes.data?.records && attendanceRes.data.records.length > 0) {
          setExistingAttendance(true);
          const attendanceMap: Record<string, AttendanceRecord> = {};
          attendanceRes.data.records.forEach((record: any) => {
            attendanceMap[record.student_id] = {
              student_id: record.student_id,
              status: record.status,
              check_in_time: record.check_in_time,
              minutes_late: record.minutes_late,
              reason: record.reason
            };
          });
          setAttendance(attendanceMap);
        } else {
          // Initialize with all present
          initializeAttendance(studentsData);
          setExistingAttendance(false);
        }
      } catch (error) {
        // No existing attendance, initialize with all present
        initializeAttendance(studentsData);
        setExistingAttendance(false);
      }
      
    } catch (error) {
      console.error('Error fetching data:', error);
      setStudents([]);
      setAttendance({});
      setExistingAttendance(false);
    } finally {
      setLoading(false);
    }
  };

  const initializeAttendance = (studentsList: Student[]) => {
    const attendanceMap: Record<string, AttendanceRecord> = {};
    studentsList.forEach((student) => {
      attendanceMap[student.id] = {
        student_id: student.id,
        status: 'present',
        check_in_time: '08:00',
        minutes_late: 0
      };
    });
    setAttendance(attendanceMap);
  };

  const handleStatusChange = (studentId: string, status: 'present' | 'absent' | 'late' | 'excused') => {
    setAttendance({
      ...attendance,
      [studentId]: {
        ...attendance[studentId],
        status,
        minutes_late: status === 'late' ? (attendance[studentId]?.minutes_late || 15) : 0
      }
    });
  };

  const handleMarkAll = (status: 'present' | 'absent') => {
    const updatedAttendance: Record<string, AttendanceRecord> = {};
    students.forEach(student => {
      updatedAttendance[student.id] = {
        student_id: student.id,
        status,
        check_in_time: status === 'present' ? '08:00' : undefined,
        minutes_late: 0
      };
    });
    setAttendance(updatedAttendance);
  };

  const handleSave = async () => {
    if (!selectedClass || !selectedDate) {
      alert('Please select a class and date');
      return;
    }

    if (!currentSessionId || !currentTermId) {
      alert('No current academic session/term is set. Set one as current under Sessions & Terms first.');
      return;
    }

    try {
      setSaving(true);

      const records = Object.values(attendance);

      const response = await api.post('/api/v1/attendance/mark', {
        class_id: selectedClass,
        session_id: currentSessionId,
        term_id: currentTermId,
        attendance_date: selectedDate,
        records: records
      });

      if (response.error) {
        alert(response.error);
        return;
      }

      alert('Attendance saved successfully!');
      setExistingAttendance(true);
    } catch (error: any) {
      console.error('Error saving attendance:', error);
      alert('Failed to save attendance');
    } finally {
      setSaving(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      present: 'bg-success-100 text-success-700 border-success-600',
      absent: 'bg-danger-100 text-danger-700 border-danger-600',
      late: 'bg-warning-100 text-warning-700 border-warning-600',
      excused: 'bg-info-100 text-info-700 border-info-600'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const stats = {
    present: Object.values(attendance).filter(a => a.status === 'present').length,
    absent: Object.values(attendance).filter(a => a.status === 'absent').length,
    late: Object.values(attendance).filter(a => a.status === 'late').length,
    excused: Object.values(attendance).filter(a => a.status === 'excused').length
  };

  const attendanceRate = students.length > 0 
    ? ((stats.present + stats.late) / students.length * 100).toFixed(1)
    : 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <PageHeader title="Mark Attendance" subtitle="Record daily attendance for students" />

        {/* Selection */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Class *</label>
              <select
                value={selectedClass}
                onChange={(e) => setSelectedClass(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              >
                <option value="">Choose a class...</option>
                {classes.map(cls => (
                  <option key={cls.id} value={cls.id}>{cls.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Date *</label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div className="flex items-end gap-2">
              <Button
                onClick={() => handleMarkAll('present')}
                disabled={!selectedClass}
                className="flex-1"
              >
                Mark All Present
              </Button>
            </div>
          </div>

          {existingAttendance && (
            <div className="mt-4 p-3 bg-info-50 border border-info-100 rounded-lg">
              <p className="text-sm text-info-700">
                Attendance has already been marked for this date. You can update it below.
              </p>
            </div>
          )}
        </div>

        {/* Statistics */}
        {selectedClass && students.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <div className="text-sm text-gray-500">Total Students</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">{students.length}</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <div className="text-sm text-gray-500">Present</div>
              <div className="text-2xl font-bold text-success-600 mt-1">{stats.present}</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <div className="text-sm text-gray-500">Absent</div>
              <div className="text-2xl font-bold text-danger-600 mt-1">{stats.absent}</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <div className="text-sm text-gray-500">Late</div>
              <div className="text-2xl font-bold text-warning-600 mt-1">{stats.late}</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <div className="text-sm text-gray-500">Attendance Rate</div>
              <div className="text-2xl font-bold text-brand-600 mt-1">{attendanceRate}%</div>
            </div>
          </div>
        )}

        {/* Attendance Grid */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
          </div>
        ) : selectedClass && students.length > 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Admission No.</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student Name</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason (Optional)</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {students.map((student, index) => {
                    const record = attendance[student.id];
                    
                    return (
                      <tr key={student.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {student.admission_number}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {student.first_name} {student.last_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex justify-center gap-2">
                            {(['present', 'absent', 'late', 'excused'] as const).map(status => (
                              <button
                                key={status}
                                onClick={() => handleStatusChange(student.id, status)}
                                className={`px-3 py-1 text-xs font-medium rounded-lg border-2 transition-colors ${
                                  record?.status === status
                                    ? getStatusColor(status)
                                    : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
                                }`}
                              >
                                {status.charAt(0).toUpperCase() + status.slice(1)}
                              </button>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <input
                            type="text"
                            value={record?.reason || ''}
                            onChange={(e) => setAttendance({
                              ...attendance,
                              [student.id]: {...record, reason: e.target.value}
                            })}
                            placeholder="Optional reason for absence/lateness"
                            className="w-full px-3 py-1 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end">
              <Button onClick={handleSave} disabled={saving || !selectedClass}>
                {saving ? 'Saving...' : 'Save Attendance'}
              </Button>
            </div>
          </div>
        ) : selectedClass ? (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-12 text-center text-gray-500">
            No students found in this class
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-12 text-center text-gray-500">
            Select a class to mark attendance
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default function MarkAttendancePage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
        </div>
      </DashboardLayout>
    }>
      <MarkAttendancePageContent />
    </Suspense>
  );
}
