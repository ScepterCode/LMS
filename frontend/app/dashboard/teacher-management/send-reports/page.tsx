'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/DashboardLayout';

interface StudentReportStatus {
  student_id: string;
  student_name: string;
  admission_number: string;
  report_card_id: string | null;
  status: string | null;
}

export default function SendReportsPage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<any[]>([]);
  const [terms, setTerms] = useState<any[]>([]);
  const [formTeacherClass, setFormTeacherClass] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [loadingStatuses, setLoadingStatuses] = useState(false);
  const [publishing, setPublishing] = useState(false);

  const [selectedSession, setSelectedSession] = useState('');
  const [selectedTerm, setSelectedTerm] = useState('');
  const [rows, setRows] = useState<StudentReportStatus[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedSession && user) {
      loadFormTeacherClass();
    }
  }, [selectedSession, user]);

  useEffect(() => {
    if (formTeacherClass && selectedSession && selectedTerm) {
      loadReportStatuses();
    }
  }, [formTeacherClass, selectedSession, selectedTerm]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [sessionsRes, termsRes] = await Promise.all([api.getSessions(), api.getTerms()]);

      const sessionsList = (sessionsRes.data as any[]) || [];
      setSessions(sessionsList);
      const currentSession = sessionsList.find((s) => s.is_current);
      if (currentSession) setSelectedSession(currentSession.id);

      const termsList = (termsRes.data as any[]) || [];
      setTerms(termsList);
      const currentTerm = termsList.find((t) => t.is_current);
      if (currentTerm) setSelectedTerm(currentTerm.id);
    } catch (error) {
      console.error('Error loading initial data:', error);
      setSessions([]);
      setTerms([]);
    } finally {
      setLoading(false);
    }
  };

  const loadFormTeacherClass = async () => {
    if (!user?.id) return;

    try {
      const teachersRes = await api.getTeachers({ limit: 100 });
      if (!teachersRes.data) return;

      const teachers = teachersRes.data as any[];
      const teacher = teachers.find((t) => t.user_id === user.id);
      if (!teacher) return;

      const classesRes = await api.getTeacherClasses(teacher.id, selectedSession);
      if (!classesRes.data) return;

      const classes = classesRes.data as any[];
      const formClass = classes.find((c) => c.is_form_teacher);

      if (formClass) {
        setFormTeacherClass(formClass);
      }
    } catch (error) {
      console.error('Error loading form teacher class:', error);
    }
  };

  const loadReportStatuses = async () => {
    if (!formTeacherClass) return;

    setLoadingStatuses(true);
    try {
      const studentsRes = await api.getClassStudents(formTeacherClass.id);
      const students = (studentsRes.data as any[]) || [];

      const statusResults = await Promise.all(
        students.map(async (s) => {
          const res = await api.get(
            `/api/v1/grading/students/${s.id}/report-cards?session_id=${selectedSession}`
          );
          const reportCards = (res.data as any[]) || [];
          const match = reportCards.find((rc) => rc.term_id === selectedTerm);
          return {
            student_id: s.id,
            student_name: `${s.first_name} ${s.last_name}`,
            admission_number: s.admission_number,
            report_card_id: match?.id || null,
            status: match?.status || null,
          } as StudentReportStatus;
        })
      );

      setRows(statusResults);
      setSelected(new Set());
    } catch (error) {
      console.error('Error loading report statuses:', error);
      setRows([]);
    } finally {
      setLoadingStatuses(false);
    }
  };

  const toggleSelected = (studentId: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(studentId)) next.delete(studentId);
      else next.add(studentId);
      return next;
    });
  };

  const publishableRows = rows.filter((r) => r.report_card_id && r.status !== 'published');

  const handlePublishSelected = async () => {
    const toPublish = publishableRows.filter((r) => selected.has(r.student_id));
    if (toPublish.length === 0) {
      alert('Select at least one student with a ready report card.');
      return;
    }

    setPublishing(true);
    try {
      const results = await Promise.all(
        toPublish.map((r) => api.publishReportCard(r.report_card_id as string))
      );
      const failed = results.filter((r) => r.error);
      if (failed.length > 0) {
        alert(`Published ${results.length - failed.length} of ${results.length}. ${failed[0].error}`);
      } else {
        alert(`Published ${results.length} report card(s) to parents!`);
      }
      await loadReportStatuses();
    } catch (error) {
      console.error('Error publishing reports:', error);
      alert('Failed to publish reports');
    } finally {
      setPublishing(false);
    }
  };

  const statusBadge = (status: string | null) => {
    if (!status) {
      return <span className="px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded-full">No report yet</span>;
    }
    const colors: Record<string, string> = {
      generated: 'bg-blue-100 text-blue-800',
      approved: 'bg-yellow-100 text-yellow-800',
      published: 'bg-green-100 text-green-800',
    };
    return (
      <span className={`px-2 py-1 text-xs rounded-full capitalize ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    );
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (!formTeacherClass) {
    return (
      <DashboardLayout>
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Send Reports</h2>
        </div>
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
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <p className="mt-4 text-gray-500">You are not assigned as a form teacher</p>
          <p className="text-sm text-gray-400 mt-2">Only form teachers can send reports to parent accounts</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Send Reports to Parents</h2>
        <p className="text-gray-600 mt-1">
          Publishing a report card makes it visible to that student's parent(s) under My Children.
          Class: {formTeacherClass.name}
        </p>
      </div>

      <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Session</label>
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

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Term</label>
            <select
              value={selectedTerm}
              onChange={(e) => setSelectedTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Select Term</option>
              {terms.map((term) => (
                <option key={term.id} value={term.id}>
                  {term.name} {term.is_current && '(Current)'}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handlePublishSelected}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              disabled={publishing || selected.size === 0}
            >
              {publishing ? 'Publishing...' : `Publish Selected (${selected.size})`}
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Students in {formTeacherClass.name}</h3>
          {publishableRows.length > 0 && (
            <button
              onClick={() => setSelected(new Set(publishableRows.map((r) => r.student_id)))}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Select all ready ({publishableRows.length})
            </button>
          )}
        </div>

        <div className="p-6">
          {loadingStatuses ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : rows.length === 0 ? (
            <p className="text-center py-12 text-gray-500">No students found in this class.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3"></th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Admission No.</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Report Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {rows.map((row) => (
                    <tr key={row.student_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selected.has(row.student_id)}
                          onChange={() => toggleSelected(row.student_id)}
                          disabled={!row.report_card_id || row.status === 'published'}
                          className="rounded"
                        />
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{row.student_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{row.admission_number}</td>
                      <td className="px-4 py-3">{statusBadge(row.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
