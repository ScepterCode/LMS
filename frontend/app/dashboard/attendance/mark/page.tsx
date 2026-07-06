'use client';

import { useState, useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';

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

export default function MarkAttendancePage() {
  const [classes, setClasses] = useState<Class[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [attendance, setAttendance] = useState<Record<string, AttendanceRecord>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [existingAttendance, setExistingAttendance] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState('');
  const [currentTermId, setCurrentTermId] = useState('');

  useEffect(() => {
    fetchClasses();
    fetchCurrentSessionAndTerm();
  }, []);

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
      present: 'bg-green-100 text-green-800 border-green-300',
      absent: 'bg-red-100 text-red-800 border-red-300',
      late: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      excused: 'bg-blue-100 text-blue-800 border-blue-300'
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
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mark Attendance</h1>
          <p className="text-gray-600 mt-1">Record daily attendance for students</p>
        </div>

        {/* Selection */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Class *</label>
              <select
                value={selectedClass}
                onChange={(e) => setSelectedClass(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            
            <div className="flex items-end gap-2">
              <button
                onClick={() => handleMarkAll('present')}
                disabled={!selectedClass}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Mark All Present
              </button>
            </div>
          </div>
          
          {existingAttendance && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                ℹ️ Attendance has already been marked for this date. You can update it below.
              </p>
            </div>
          )}
        </div>

        {/* Statistics */}
        {selectedClass && students.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Total Students</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">{students.length}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Present</div>
              <div className="text-2xl font-bold text-green-600 mt-1">{stats.present}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Absent</div>
              <div className="text-2xl font-bold text-red-600 mt-1">{stats.absent}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Late</div>
              <div className="text-2xl font-bold text-yellow-600 mt-1">{stats.late}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Attendance Rate</div>
              <div className="text-2xl font-bold text-blue-600 mt-1">{attendanceRate}%</div>
            </div>
          </div>
        )}

        {/* Attendance Grid */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-500">Loading students...</div>
          </div>
        ) : selectedClass && students.length > 0 ? (
          <div className="bg-white rounded-lg shadow overflow-hidden">
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
                            className="w-full px-3 py-1 text-sm border border-gray-300 rounded-lg"
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            
            <div className="px-6 py-4 bg-gray-50 border-t flex justify-end">
              <button
                onClick={handleSave}
                disabled={saving || !selectedClass}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Attendance'}
              </button>
            </div>
          </div>
        ) : selectedClass ? (
          <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
            No students found in this class
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
            Select a class to mark attendance
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
