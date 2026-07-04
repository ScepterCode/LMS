'use client';

import { useState, useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';

interface Student {
  id: string;
  admission_number: string;
  first_name: string;
  last_name: string;
}

interface ReportCard {
  id: string;
  student_id: string;
  student_name?: string;
  session_name?: string;
  term_name?: string;
  average_score: number;
  overall_grade: string;
  overall_position: number;
  class_size: number;
  days_present: number;
  days_absent: number;
  total_school_days: number;
  status: string;
  class_teacher_remark?: string;
  principal_remark?: string;
}

interface SubjectGrade {
  subject_name: string;
  total_score: number;
  grade_letter: string;
  class_position: number;
  teacher_remark?: string;
}

export default function ReportCardsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [reportCards, setReportCards] = useState<ReportCard[]>([]);
  const [selectedStudent, setSelectedStudent] = useState('');
  const [selectedReport, setSelectedReport] = useState<ReportCard | null>(null);
  const [subjectGrades, setSubjectGrades] = useState<SubjectGrade[]>([]);
  const [loading, setLoading] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [isFormTeacher, setIsFormTeacher] = useState(false);
  const [formClassInfo, setFormClassInfo] = useState<any>(null);
  const [viewMode, setViewMode] = useState<'individual' | 'class'>('individual');
  const [classStudents, setClassStudents] = useState<Student[]>([]);
  const [allClassReports, setAllClassReports] = useState<any[]>([]);

  useEffect(() => {
    fetchStudents();
    checkFormTeacherStatus();
  }, []);

  const checkFormTeacherStatus = async () => {
    try {
      const response = await api.get('/api/v1/teacher-management/teacher-assignments/my-classes');
      const classes = response.data || [];
      const formClass = classes.find((c: any) => c.is_form_teacher);
      if (formClass) {
        setIsFormTeacher(true);
        setFormClassInfo(formClass);
      }
    } catch (error) {
      console.error('Error checking form teacher status:', error);
      setIsFormTeacher(false);
      setFormClassInfo(null);
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

  const fetchClassStudents = async () => {
    if (!formClassInfo) return;
    
    setLoading(true);
    try {
      const response = await api.get(`/api/v1/students?class_id=${formClassInfo.class_id}`);
      setClassStudents(response.data ? (response.data as Student[]) : []);
    } catch (error) {
      console.error('Error fetching class students:', error);
      setClassStudents([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllClassReports = async () => {
    if (!formClassInfo) return;
    
    setLoading(true);
    try {
      // Fetch all students in the class
      const studentsResponse = await api.get(`/api/v1/students?class_id=${formClassInfo.class_id}`);
      const classStudentsList = studentsResponse.data || [];
      
      // Fetch report cards for each student
      const reportsPromises = classStudentsList.map((student: Student) =>
        api.get(`/api/v1/grading/students/${student.id}/report-cards`)
          .then(res => ({
            student,
            reports: res.data || []
          }))
          .catch(() => ({ student, reports: [] }))
      );
      
      const allReports = await Promise.all(reportsPromises);
      setAllClassReports(allReports);
    } catch (error) {
      console.error('Error fetching all class reports:', error);
      setAllClassReports([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleViewMode = async () => {
    const newMode = viewMode === 'individual' ? 'class' : 'individual';
    setViewMode(newMode);
    
    if (newMode === 'class' && isFormTeacher) {
      await fetchAllClassReports();
    }
  };

  const fetchStudentReports = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/api/v1/grading/students/${selectedStudent}/report-cards`);
      setReportCards(response.data ? (response.data as ReportCard[]) : []);
    } catch (error) {
      console.error('Error fetching report cards:', error);
      setReportCards([]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewReport = async (reportId: string) => {
    setLoading(true);
    try {
      const response = await api.get(`/api/v1/grading/report-cards/${reportId}`);
      if (response.data) {
        setSelectedReport(response.data);
        setSubjectGrades(response.data.subject_grades || []);
      } else {
        setSelectedReport(null);
        setSubjectGrades([]);
      }
    } catch (error) {
      console.error('Error fetching report details:', error);
      setSelectedReport(null);
      setSubjectGrades([]);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedStudent) {
      alert('Please select a student');
      return;
    }

    try {
      setGenerating(true);
      // You'll need to get current session and term IDs
      await api.post('/api/v1/grading/report-cards/generate', {
        student_id: selectedStudent,
        session_id: '', // Add current session
        term_id: '' // Add current term
      });
      alert('Report card generated successfully!');
      setShowGenerateModal(false);
      fetchStudentReports();
    } catch (error: any) {
      console.error('Error generating report:', error);
      alert(error.response?.data?.detail || 'Failed to generate report card');
    } finally {
      setGenerating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-800',
      generated: 'bg-blue-100 text-blue-800',
      approved: 'bg-green-100 text-green-800',
      published: 'bg-purple-100 text-purple-800'
    };
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const attendancePercentage = selectedReport
    ? ((selectedReport.days_present / selectedReport.total_school_days) * 100).toFixed(1)
    : 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Report Cards</h1>
            <p className="text-gray-600 mt-1">View and generate student report cards</p>
          </div>
          <button
            onClick={() => setShowGenerateModal(true)}
            disabled={!selectedStudent}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            Generate Report Card
          </button>
        </div>

        {/* Form Teacher Quick Access */}
        {isFormTeacher && formClassInfo && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 bg-blue-600 text-white text-xs font-semibold rounded">
                    FORM TEACHER
                  </span>
                  <h3 className="text-lg font-semibold text-gray-900">{formClassInfo.class_name}</h3>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {viewMode === 'class' 
                    ? 'Viewing all report cards for your form class'
                    : 'View all grades for students in your form class'}
                </p>
              </div>
              <button
                onClick={toggleViewMode}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm disabled:opacity-50"
              >
                {loading ? 'Loading...' : (viewMode === 'individual' ? 'View All Class Grades' : 'Back to Individual View')}
              </button>
            </div>
          </div>
        )}

        {/* Student Selection */}
        {viewMode === 'individual' && (
          <div className="bg-white rounded-lg shadow p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Student</label>
            <select
              value={selectedStudent}
              onChange={(e) => {
                setSelectedStudent(e.target.value);
                setSelectedReport(null);
              }}
              className="w-full max-w-2xl px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Choose a student...</option>
              {students.map(student => (
                <option key={student.id} value={student.id}>
                  {student.admission_number} - {student.first_name} {student.last_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Class View - All Students Reports */}
        {viewMode === 'class' && isFormTeacher && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                All Report Cards - {formClassInfo.class_name}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Viewing report cards for all students in your form class
              </p>
            </div>
            {loading ? (
              <div className="p-12 text-center text-gray-500">Loading class reports...</div>
            ) : allClassReports.length === 0 ? (
              <div className="p-12 text-center text-gray-500">
                No report cards found for students in this class.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Admission No.</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reports Count</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Latest Average</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Latest Grade</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {allClassReports.map((item: any) => {
                      const latestReport = item.reports && item.reports.length > 0 ? item.reports[0] : null;
                      return (
                        <tr key={item.student.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {item.student.first_name} {item.student.last_name}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {item.student.admission_number}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {item.reports?.length || 0} report(s)
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {latestReport ? `${latestReport.average_score?.toFixed(1)}%` : '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {latestReport?.overall_grade || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {latestReport ? getStatusBadge(latestReport.status) : (
                              <span className="text-sm text-gray-400">No reports</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            {item.reports && item.reports.length > 0 ? (
                              <button
                                onClick={() => {
                                  setViewMode('individual');
                                  setSelectedStudent(item.student.id);
                                }}
                                className="text-blue-600 hover:text-blue-900"
                              >
                                View Details
                              </button>
                            ) : (
                              <span className="text-gray-400">No reports</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Report Cards List */}
        {viewMode === 'individual' && selectedStudent && !selectedReport && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Report Cards History</h2>
            </div>
            {loading ? (
              <div className="p-12 text-center text-gray-500">Loading...</div>
            ) : reportCards.length === 0 ? (
              <div className="p-12 text-center text-gray-500">
                No report cards found. Generate a report card to get started.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Session</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Term</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Average</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grade</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Position</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reportCards.map((report) => (
                      <tr key={report.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {report.session_name || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {report.term_name || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {report.average_score?.toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {report.overall_grade || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {report.overall_position}/{report.class_size}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(report.status)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => handleViewReport(report.id)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Report Card Details */}
        {viewMode === 'individual' && selectedReport && (
          <div className="space-y-6">
            <button
              onClick={() => setSelectedReport(null)}
              className="text-blue-600 hover:text-blue-800 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to list
            </button>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-600">Average Score</div>
                <div className="text-2xl font-bold text-blue-600 mt-1">
                  {selectedReport.average_score?.toFixed(1)}%
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-600">Overall Grade</div>
                <div className="text-2xl font-bold text-green-600 mt-1">
                  {selectedReport.overall_grade || 'N/A'}
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-600">Class Position</div>
                <div className="text-2xl font-bold text-purple-600 mt-1">
                  {selectedReport.overall_position}/{selectedReport.class_size}
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-600">Attendance</div>
                <div className="text-2xl font-bold text-yellow-600 mt-1">
                  {attendancePercentage}%
                </div>
              </div>
            </div>

            {/* Subject Grades */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Subject Performance</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grade</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Position</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Remark</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {subjectGrades.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                          No subject grades available
                        </td>
                      </tr>
                    ) : (
                      subjectGrades.map((grade, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {grade.subject_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {grade.total_score?.toFixed(1)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {grade.grade_letter}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {grade.class_position || 'N/A'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {grade.teacher_remark || '-'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Attendance Summary */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Attendance Summary</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-gray-600">Days Present</div>
                  <div className="text-xl font-bold text-green-600 mt-1">{selectedReport.days_present}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Days Absent</div>
                  <div className="text-xl font-bold text-red-600 mt-1">{selectedReport.days_absent}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Total School Days</div>
                  <div className="text-xl font-bold text-gray-900 mt-1">{selectedReport.total_school_days}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Attendance Rate</div>
                  <div className="text-xl font-bold text-blue-600 mt-1">{attendancePercentage}%</div>
                </div>
              </div>
            </div>

            {/* Remarks */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Remarks</h2>
              <div className="space-y-4">
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-1">Class Teacher's Remark</div>
                  <p className="text-gray-900">{selectedReport.class_teacher_remark || 'No remark yet'}</p>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-1">Principal's Remark</div>
                  <p className="text-gray-900">{selectedReport.principal_remark || 'No remark yet'}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Generate Report Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Generate Report Card</h2>
            <p className="text-gray-600 mb-6">
              This will generate a report card for the selected student for the current term. 
              All grades and attendance records will be compiled.
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleGenerateReport}
                disabled={generating}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {generating ? 'Generating...' : 'Generate'}
              </button>
              <button
                onClick={() => setShowGenerateModal(false)}
                className="flex-1 bg-gray-200 text-gray-800 py-2 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
