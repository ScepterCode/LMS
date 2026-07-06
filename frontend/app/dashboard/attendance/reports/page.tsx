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

interface AttendanceSummary {
  student_id: string;
  student_name?: string;
  student_admission_number?: string;
  days_present: number;
  days_absent: number;
  days_late: number;
  days_excused: number;
  total_school_days: number;
  attendance_percentage: number;
  punctuality_percentage: number;
}

export default function AttendanceReportsPage() {
  const [reportType, setReportType] = useState<'class' | 'student'>('class');
  const [classes, setClasses] = useState<Class[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [selectedStudent, setSelectedStudent] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [summaries, setSummaries] = useState<AttendanceSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState('');
  const [currentTermId, setCurrentTermId] = useState('');

  useEffect(() => {
    fetchClasses();
    fetchStudents();
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

  const fetchClasses = async () => {
    try {
      const response = await api.get('/api/v1/classes');
      setClasses(response.data ? (response.data as Class[]) : []);
    } catch (error) {
      console.error('Error fetching classes:', error);
      setClasses([]);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await api.get('/api/v1/students');
      setStudents(response.data ? (response.data as Student[]) : []);
    } catch (error) {
      console.error('Error fetching students:', error);
      setStudents([]);
    }
  };

  const handleGenerateReport = async () => {
    if (reportType === 'class' && !selectedClass) {
      alert('Please select a class');
      return;
    }
    if (reportType === 'student' && !selectedStudent) {
      alert('Please select a student');
      return;
    }

    try {
      setLoading(true);
      
      if (reportType === 'class') {
        if (!currentSessionId || !currentTermId) {
          alert('No current academic session/term is set. Set one as current under Sessions & Terms first.');
          return;
        }
        // Get class attendance summaries
        const response = await api.get(
          `/api/v1/attendance/summary/class/${selectedClass}?session_id=${currentSessionId}&term_id=${currentTermId}`
        );
        setSummaries(response.data || []);
      } else {
        // Get student attendance history
        let url = `/api/v1/attendance/student/${selectedStudent}`;
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (params.toString()) url += `?${params.toString()}`;
        
        const response = await api.get(url);
        // Calculate summary from records
        const records = response.data;
        const summary = calculateStudentSummary(records);
        setSummaries([summary]);
      }
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Failed to generate attendance report');
    } finally {
      setLoading(false);
    }
  };

  const calculateStudentSummary = (records: any[]): AttendanceSummary => {
    const present = records.filter(r => r.status === 'present').length;
    const absent = records.filter(r => r.status === 'absent').length;
    const late = records.filter(r => r.status === 'late').length;
    const excused = records.filter(r => r.status === 'excused').length;
    const total = records.length;
    
    return {
      student_id: selectedStudent,
      days_present: present,
      days_absent: absent,
      days_late: late,
      days_excused: excused,
      total_school_days: total,
      attendance_percentage: total > 0 ? ((present + late) / total * 100) : 0,
      punctuality_percentage: (present + late) > 0 ? (present / (present + late) * 100) : 0
    };
  };

  const getAttendanceColor = (percentage: number) => {
    if (percentage >= 90) return 'text-green-600';
    if (percentage >= 75) return 'text-yellow-600';
    return 'text-red-600';
  };

  const classStats = summaries.length > 0 ? {
    totalStudents: summaries.length,
    averageAttendance: (summaries.reduce((acc, s) => acc + s.attendance_percentage, 0) / summaries.length).toFixed(1),
    perfectAttendance: summaries.filter(s => s.attendance_percentage === 100).length,
    poorAttendance: summaries.filter(s => s.attendance_percentage < 75).length
  } : null;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Attendance Reports</h1>
          <p className="text-gray-600 mt-1">View attendance statistics and summaries</p>
        </div>

        {/* Report Configuration */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="space-y-4">
            {/* Report Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Report Type</label>
              <div className="flex gap-4">
                <button
                  onClick={() => {
                    setReportType('class');
                    setSummaries([]);
                  }}
                  className={`px-4 py-2 rounded-lg border-2 transition-colors ${
                    reportType === 'class'
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Class Summary
                </button>
                <button
                  onClick={() => {
                    setReportType('student');
                    setSummaries([]);
                  }}
                  className={`px-4 py-2 rounded-lg border-2 transition-colors ${
                    reportType === 'student'
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Individual Student
                </button>
              </div>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {reportType === 'class' ? (
                <div className="md:col-span-2">
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
              ) : (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Select Student *</label>
                    <select
                      value={selectedStudent}
                      onChange={(e) => setSelectedStudent(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="">Choose a student...</option>
                      {students.map(student => (
                        <option key={student.id} value={student.id}>
                          {student.admission_number} - {student.first_name} {student.last_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </>
              )}
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleGenerateReport}
                disabled={loading}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Generating...' : 'Generate Report'}
              </button>
            </div>
          </div>
        </div>

        {/* Class Statistics */}
        {reportType === 'class' && classStats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Total Students</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">{classStats.totalStudents}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Average Attendance</div>
              <div className="text-2xl font-bold text-blue-600 mt-1">{classStats.averageAttendance}%</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Perfect Attendance</div>
              <div className="text-2xl font-bold text-green-600 mt-1">{classStats.perfectAttendance}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Poor Attendance (below 75%)</div>
              <div className="text-2xl font-bold text-red-600 mt-1">{classStats.poorAttendance}</div>
            </div>
          </div>
        )}

        {/* Report Results */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-500">Generating report...</div>
          </div>
        ) : summaries.length > 0 ? (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                {reportType === 'class' ? 'Class Attendance Summary' : 'Student Attendance Summary'}
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {reportType === 'class' && (
                      <>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Admission No.</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student Name</th>
                      </>
                    )}
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Present</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Absent</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Late</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Excused</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Days</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Attendance %</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Punctuality %</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {summaries.map((summary, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      {reportType === 'class' && (
                        <>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {summary.student_admission_number || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {summary.student_name || 'N/A'}
                          </td>
                        </>
                      )}
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-medium">
                        {summary.days_present}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 font-medium">
                        {summary.days_absent}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600 font-medium">
                        {summary.days_late}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 font-medium">
                        {summary.days_excused}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {summary.total_school_days}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold">
                        <span className={getAttendanceColor(summary.attendance_percentage)}>
                          {summary.attendance_percentage.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold">
                        <span className={getAttendanceColor(summary.punctuality_percentage)}>
                          {summary.punctuality_percentage.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
            Configure report parameters and click "Generate Report" to view attendance data
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
