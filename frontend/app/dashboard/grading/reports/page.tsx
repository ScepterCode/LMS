'use client';

import { useState, useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

interface Student {
  id: string;
  admission_number: string;
  first_name: string;
  last_name: string;
}

interface ReportCard {
  id: string;
  student_id: string;
  class_id?: string;
  session_id?: string;
  term_id?: string;
  student_name?: string;
  session_name?: string;
  term_name?: string;
  average_score: number;
  overall_grade: string;
  overall_position: number;
  class_size: number;
  days_present: number;
  days_absent: number;
  days_late: number;
  days_excused?: number;
  total_school_days: number;
  attendance_percentage?: number | string;
  punctuality_percentage?: number | string;
  status: string;
  class_teacher_remark?: string;
  principal_remark?: string;
  subject_grades?: SubjectGrade[];
  skill_ratings?: SkillRating[];
}

interface SubjectGrade {
  subject_name: string;
  total_score: number;
  grade_letter: string;
  class_position: number;
  teacher_remark?: string;
}

interface SkillRating {
  category_name: string;
  domain: 'psychomotor' | 'affective';
  rating: number;
}

interface SkillCategory {
  id: string;
  name: string;
  domain: 'psychomotor' | 'affective';
}

interface Organization {
  name: string;
  address?: string;
  motto?: string;
  logo_url?: string;
}

const RATING_LABELS: Record<number, string> = {
  5: 'Excellent',
  4: 'Very Good',
  3: 'Good',
  2: 'Fair',
  1: 'Poor',
};

export default function ReportCardsPage() {
  const { user } = useAuth();
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
  const [formTeacherCheckDone, setFormTeacherCheckDone] = useState(false);
  const [viewMode, setViewMode] = useState<'individual' | 'class'>('individual');
  const [classStudents, setClassStudents] = useState<Student[]>([]);
  const [allClassReports, setAllClassReports] = useState<any[]>([]);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [skillCategories, setSkillCategories] = useState<SkillCategory[]>([]);
  const [ratingsDraft, setRatingsDraft] = useState<Record<string, number>>({});
  const [savingRatings, setSavingRatings] = useState(false);

  useEffect(() => {
    fetchSkillCategories();
  }, []);

  // Wait for the form-teacher check to settle before fetching students -
  // for a teacher this determines which class (if any) they're scoped to,
  // and the backend now rejects a non-form-teacher's request for any
  // student's report card, so there's no point listing students they
  // couldn't actually view.
  useEffect(() => {
    if (!user) return;
    if (user.role !== 'teacher') {
      fetchStudents();
    } else if (formTeacherCheckDone) {
      fetchStudents();
    }
  }, [user, formTeacherCheckDone]);

  useEffect(() => {
    if (user?.school_id) {
      fetchOrganization();
    }
  }, [user?.school_id]);

  const fetchOrganization = async () => {
    if (!user?.school_id) return;
    try {
      const response = await api.getOrganization(user.school_id);
      const org = (response.data as any)?.organization as Organization | undefined;
      if (org) setOrganization(org);
    } catch (error) {
      console.error('Error fetching organization:', error);
    }
  };

  const fetchSkillCategories = async () => {
    try {
      const response = await api.getSkillCategories();
      setSkillCategories(response.data ? (response.data as SkillCategory[]) : []);
    } catch (error) {
      console.error('Error fetching skill categories:', error);
      setSkillCategories([]);
    }
  };

  useEffect(() => {
    if (selectedStudent) {
      fetchStudentReports();
    } else {
      setReportCards([]);
    }
  }, [selectedStudent]);

  useEffect(() => {
    if (user) {
      checkFormTeacherStatus();
    }
  }, [user]);

  const checkFormTeacherStatus = async () => {
    if (!user?.id || user.role !== 'teacher') {
      setFormTeacherCheckDone(true);
      return;
    }

    try {
      const teachersRes = await api.getTeachers({ limit: 100 });
      const teachers = (teachersRes.data as any[]) || [];
      const teacher = teachers.find((t) => t.user_id === user.id);
      if (!teacher) return;

      const classesRes = await api.getTeacherClasses(teacher.id);
      const classes = (classesRes.data as any[]) || [];
      const formClass = classes.find((c: any) => c.is_form_teacher);
      if (formClass) {
        setIsFormTeacher(true);
        setFormClassInfo(formClass);
      }
    } catch (error) {
      console.error('Error checking form teacher status:', error);
      setIsFormTeacher(false);
      setFormClassInfo(null);
    } finally {
      setFormTeacherCheckDone(true);
    }
  };

  const fetchStudents = async () => {
    try {
      // A teacher can only view report cards for students in a class they
      // are the form teacher of (backend-enforced) - no point listing
      // every student in the school when only one class is actually
      // reachable. A teacher with no form class sees an empty picker.
      if (user?.role === 'teacher') {
        if (!formClassInfo) {
          setStudents([]);
          return;
        }
        const response = await api.get(`/api/v1/students?class_id=${formClassInfo.id}`);
        setStudents(response.data ? (response.data as Student[]) : []);
        return;
      }

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
      const response = await api.get(`/api/v1/students?class_id=${formClassInfo.id}`);
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
      const studentsResponse = await api.get(`/api/v1/students?class_id=${formClassInfo.id}`);
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
        const report = response.data as ReportCard;
        setSelectedReport(report);
        setSubjectGrades(report.subject_grades || []);
        if (canCompileFor(report) && report.session_id && report.term_id) {
          await loadRatingsDraft(report.student_id, report.session_id, report.term_id);
        }
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

  const canCompileFor = (report: ReportCard | null) => {
    return !!(isFormTeacher && formClassInfo && report && report.class_id === formClassInfo.id);
  };

  const loadRatingsDraft = async (studentId: string, sessionId: string, termId: string) => {
    try {
      const response = await api.getStudentSkillRatings(studentId, sessionId, termId);
      const existing = (response.data as any[]) || [];
      const draft: Record<string, number> = {};
      existing.forEach((r) => {
        if (r.skill_category_id) draft[r.skill_category_id] = r.rating;
      });
      setRatingsDraft(draft);
    } catch (error) {
      console.error('Error loading skill ratings:', error);
      setRatingsDraft({});
    }
  };

  const handleSaveRatings = async () => {
    if (!selectedReport?.session_id || !selectedReport?.term_id) return;

    const ratings = Object.entries(ratingsDraft)
      .filter(([, rating]) => !!rating)
      .map(([skill_category_id, rating]) => ({ skill_category_id, rating }));

    if (ratings.length === 0) {
      alert('Please rate at least one skill');
      return;
    }

    setSavingRatings(true);
    try {
      const response = await api.submitSkillRatings({
        student_id: selectedReport.student_id,
        session_id: selectedReport.session_id,
        term_id: selectedReport.term_id,
        ratings,
      });

      if (response.error) {
        alert(response.error);
        return;
      }

      alert('Skill ratings saved!');
      handleViewReport(selectedReport.id);
    } catch (error) {
      console.error('Error saving skill ratings:', error);
      alert('Failed to save skill ratings');
    } finally {
      setSavingRatings(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedStudent) {
      alert('Please select a student');
      return;
    }

    try {
      setGenerating(true);

      const [sessionsRes, termsRes] = await Promise.all([api.getSessions(), api.getTerms()]);
      const currentSession = ((sessionsRes.data as any[]) || []).find((s) => s.is_current);
      const currentTerm = ((termsRes.data as any[]) || []).find((t) => t.is_current);

      if (!currentSession || !currentTerm) {
        alert('No current academic session/term is set up. Please configure one first.');
        return;
      }

      const response = await api.post('/api/v1/grading/report-cards/generate', {
        student_id: selectedStudent,
        session_id: currentSession.id,
        term_id: currentTerm.id,
      });

      if (response.error) {
        alert(response.error);
        return;
      }

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
    const tones: Record<string, 'neutral' | 'info' | 'success' | 'brand'> = {
      draft: 'neutral',
      generated: 'info',
      approved: 'success',
      published: 'brand',
    };
    return <Badge tone={tones[status] || 'neutral'}>{status}</Badge>;
  };

  const attendancePercentage = selectedReport
    ? (selectedReport.attendance_percentage != null
        ? Number(selectedReport.attendance_percentage).toFixed(1)
        : selectedReport.total_school_days > 0
          ? ((selectedReport.days_present / selectedReport.total_school_days) * 100).toFixed(1)
          : '0.0')
    : 0;

  const punctualityPercentage = selectedReport
    ? (selectedReport.punctuality_percentage != null
        ? Number(selectedReport.punctuality_percentage).toFixed(1)
        : (selectedReport.days_present + selectedReport.days_late) > 0
          ? ((selectedReport.days_present / (selectedReport.days_present + selectedReport.days_late)) * 100).toFixed(1)
          : '0.0')
    : 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <PageHeader
          title="Report Cards"
          subtitle="View and generate student report cards"
          actions={
            <Button onClick={() => setShowGenerateModal(true)} disabled={!selectedStudent}>
              Generate Report Card
            </Button>
          }
        />

        {/* Form Teacher Quick Access */}
        {isFormTeacher && formClassInfo && (
          <div className="bg-brand-50 border border-brand-100 rounded-lg p-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 bg-brand-600 text-white text-xs font-semibold rounded">
                    FORM TEACHER
                  </span>
                  <h3 className="text-lg font-semibold text-gray-900">{formClassInfo.name}</h3>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  {viewMode === 'class'
                    ? 'Viewing all report cards for your form class'
                    : 'View all grades for students in your form class'}
                </p>
              </div>
              <Button onClick={toggleViewMode} disabled={loading} size="sm">
                {loading ? 'Loading...' : (viewMode === 'individual' ? 'View All Class Grades' : 'Back to Individual View')}
              </Button>
            </div>
          </div>
        )}

        {/* Student Selection */}
        {viewMode === 'individual' && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Student</label>
            <select
              value={selectedStudent}
              onChange={(e) => {
                setSelectedStudent(e.target.value);
                setSelectedReport(null);
              }}
              className="w-full max-w-2xl px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
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
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                All Report Cards - {formClassInfo.name}
              </h2>
              <p className="text-sm text-gray-500 mt-1">
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
                            {latestReport ? `${Number(latestReport.average_score || 0).toFixed(1)}%` : '-'}
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
                                className="text-brand-600 hover:text-brand-800"
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
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
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
                          {Number(report.average_score || 0).toFixed(1)}%
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
            <div className="no-print flex items-center justify-between">
              <button
                onClick={() => setSelectedReport(null)}
                className="text-brand-600 hover:text-brand-800 flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to list
              </button>
              <Button onClick={() => window.print()} icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
              }>
                Print Report Card
              </Button>
            </div>

            {canCompileFor(selectedReport) && skillCategories.length > 0 && (
              <div className="no-print bg-brand-50 border border-brand-100 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-1">Compile Skill Ratings</h2>
                <p className="text-sm text-gray-500 mb-4">
                  As form teacher of {formClassInfo.name}, rate this student on each trait (1-5).
                </p>
                {(['psychomotor', 'affective'] as const).map((domain) => {
                  const items = skillCategories.filter((c) => c.domain === domain);
                  if (items.length === 0) return null;
                  return (
                    <div key={domain} className="mb-4 last:mb-0">
                      <h3 className="text-sm font-semibold text-gray-700 uppercase mb-2">
                        {domain === 'psychomotor' ? 'Psychomotor Domain' : 'Affective Domain'}
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {items.map((category) => (
                          <div key={category.id} className="flex items-center justify-between gap-3">
                            <span className="text-sm text-gray-700">{category.name}</span>
                            <select
                              value={ratingsDraft[category.id] || ''}
                              onChange={(e) =>
                                setRatingsDraft({ ...ratingsDraft, [category.id]: Number(e.target.value) })
                              }
                              className="px-2 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                            >
                              <option value="">Not rated</option>
                              {[5, 4, 3, 2, 1].map((v) => (
                                <option key={v} value={v}>
                                  {v} - {RATING_LABELS[v]}
                                </option>
                              ))}
                            </select>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
                <Button onClick={handleSaveRatings} disabled={savingRatings} className="mt-2">
                  {savingRatings ? 'Saving...' : 'Save Skill Ratings'}
                </Button>
              </div>
            )}

            <div id="printable-report-card" className="space-y-6">
            {/* Report Header */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 text-center border-b-4 border-b-brand-600">
              {organization?.logo_url && (
                <img
                  src={organization.logo_url}
                  alt="School logo"
                  className="w-16 h-16 object-contain mx-auto mb-2"
                />
              )}
              <h1 className="text-xl font-bold text-gray-900">{organization?.name || 'Student Report Card'}</h1>
              {organization?.motto && (
                <p className="text-sm italic text-gray-500 mt-1">"{organization.motto}"</p>
              )}
              {organization?.address && (
                <p className="text-xs text-gray-500 mt-1">{organization.address}</p>
              )}
              <p className="text-lg font-semibold text-gray-800 mt-3">{selectedReport.student_name || 'N/A'}</p>
              <p className="text-sm text-gray-500 mt-1">
                {selectedReport.session_name || 'N/A'} &middot; {selectedReport.term_name || 'N/A'}
              </p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                <div className="text-sm text-gray-500">Average Score</div>
                <div className="text-2xl font-bold text-brand-600 mt-1">
                  {Number(selectedReport.average_score || 0).toFixed(1)}%
                </div>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                <div className="text-sm text-gray-500">Overall Grade</div>
                <div className="text-2xl font-bold text-success-600 mt-1">
                  {selectedReport.overall_grade || 'N/A'}
                </div>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                <div className="text-sm text-gray-500">Class Position</div>
                <div className="text-2xl font-bold text-info-600 mt-1">
                  {selectedReport.overall_position}/{selectedReport.class_size}
                </div>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                <div className="text-sm text-gray-500">Attendance</div>
                <div className="text-2xl font-bold text-warning-600 mt-1">
                  {attendancePercentage}%
                </div>
              </div>
            </div>

            {/* Subject Grades */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
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
                            {Number(grade.total_score || 0).toFixed(1)}
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
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Attendance Summary</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <div className="text-sm text-gray-500">Days Present</div>
                  <div className="text-xl font-bold text-success-600 mt-1">{selectedReport.days_present}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Days Absent</div>
                  <div className="text-xl font-bold text-danger-600 mt-1">{selectedReport.days_absent}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Days Excused</div>
                  <div className="text-xl font-bold text-warning-600 mt-1">{selectedReport.days_excused ?? 0}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Total School Days</div>
                  <div className="text-xl font-bold text-gray-900 mt-1">{selectedReport.total_school_days}</div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                <div>
                  <div className="text-sm text-gray-500">Regularity (Attendance Rate)</div>
                  <div className="text-xl font-bold text-brand-600 mt-1">{attendancePercentage}%</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Punctuality Rate</div>
                  <div className="text-xl font-bold text-info-600 mt-1">{punctualityPercentage}%</div>
                </div>
              </div>
            </div>

            {/* Skills & Extracurricular Activities */}
            {selectedReport.skill_ratings && selectedReport.skill_ratings.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Skills & Extracurricular Activities</h2>
                {(['psychomotor', 'affective'] as const).map((domain) => {
                  const items = selectedReport.skill_ratings!.filter((r) => r.domain === domain);
                  if (items.length === 0) return null;
                  return (
                    <div key={domain} className="mb-4 last:mb-0">
                      <h3 className="text-sm font-semibold text-gray-700 uppercase mb-2">
                        {domain === 'psychomotor' ? 'Psychomotor Domain' : 'Affective Domain'}
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {items.map((item, idx) => (
                          <div key={idx} className="flex justify-between border-b border-gray-100 py-1">
                            <span className="text-sm text-gray-700">{item.category_name}</span>
                            <span className="text-sm font-medium text-gray-900">
                              {RATING_LABELS[item.rating] || item.rating}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Remarks */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
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
          </div>
        )}
      </div>

      <style jsx global>{`
        @media print {
          body * {
            visibility: hidden;
          }
          #printable-report-card,
          #printable-report-card * {
            visibility: visible;
          }
          #printable-report-card {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
          }
          .no-print {
            display: none !important;
          }
        }
      `}</style>

      {/* Generate Report Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4 text-gray-900">Generate Report Card</h2>
            <p className="text-gray-500 mb-6">
              This will generate a report card for the selected student for the current term.
              All grades and attendance records will be compiled.
            </p>
            <div className="flex gap-3">
              <Button onClick={handleGenerateReport} disabled={generating} className="flex-1">
                {generating ? 'Generating...' : 'Generate'}
              </Button>
              <Button variant="secondary" onClick={() => setShowGenerateModal(false)} className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
