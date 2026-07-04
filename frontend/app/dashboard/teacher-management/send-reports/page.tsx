'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/DashboardLayout';

interface Report {
  id: string;
  report_type: string;
  class_name?: string;
  recipient_count?: number;
  created_at: string;
}

export default function SendReportsPage() {
  const { user } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [parents, setParents] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [terms, setTerms] = useState<any[]>([]);
  const [formTeacherClass, setFormTeacherClass] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showSendModal, setShowSendModal] = useState(false);
  const [sendingReport, setSendingReport] = useState(false);

  const [selectedSession, setSelectedSession] = useState('');
  const [selectedTerm, setSelectedTerm] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    report_type: 'end_of_term',
    selected_parents: [] as string[],
    send_to_all: true,
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (formTeacherClass && selectedSession && selectedTerm) {
      loadReports();
      loadStudentsAndParents();
    }
  }, [formTeacherClass, selectedSession, selectedTerm]);

  const loadInitialData = async () => {
    setLoading(true);

    try {
      const [sessionsRes, termsRes] = await Promise.all([
        api.getSessions(),
        api.getTerms(),
      ]);

      if (sessionsRes.data) {
        const sessions = sessionsRes.data as any[];
        setSessions(sessions);
        const currentSession = sessions.find(s => s.is_current);
        if (currentSession) setSelectedSession(currentSession.id);
      } else {
        setSessions([]);
      }

      if (termsRes.data) {
        const terms = termsRes.data as any[];
        setTerms(terms);
        const currentTerm = terms.find(t => t.is_current);
        if (currentTerm) setSelectedTerm(currentTerm.id);
      } else {
        setTerms([]);
      }

      await loadFormTeacherClass();
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
      const teacher = teachers.find(t => t.user_id === user.id);
      if (!teacher) return;

      const classesRes = await api.getTeacherClasses(teacher.id, selectedSession);
      if (!classesRes.data) return;

      const classes = classesRes.data as any[];
      const formClass = classes.find(c => c.is_form_teacher);
      
      if (formClass) {
        setFormTeacherClass(formClass);
      }
    } catch (error) {
      console.error('Error loading form teacher class:', error);
    }
  };

  const loadStudentsAndParents = async () => {
    if (!formTeacherClass) return;

    try {
      const studentsRes = await api.getClassStudents(formTeacherClass.id);
      if (studentsRes.data) {
        const students = studentsRes.data as any[];
        setStudents(students);

        // Get all parents for these students
        const parentsPromises = students.map(s => api.getStudentGuardians(s.id));
        const parentsResults = await Promise.all(parentsPromises);
        
        const allParents: any[] = [];
        parentsResults.forEach((result, index) => {
          if (result.data) {
            const studentParents = result.data as any[];
            studentParents.forEach(p => {
              if (!allParents.find(ap => ap.id === p.id)) {
                allParents.push({
                  ...p,
                  student_name: `${students[index].first_name} ${students[index].last_name}`,
                });
              }
            });
          }
        });
        setParents(allParents);
      } else {
        setStudents([]);
        setParents([]);
      }
    } catch (error) {
      console.error('Error loading students and parents:', error);
      setStudents([]);
      setParents([]);
    }
  };

  const loadReports = async () => {
    if (!formTeacherClass) return;

    try {
      const response = await api.getReports({
        class_id: formTeacherClass.id,
        session_id: selectedSession,
        term_id: selectedTerm,
      });

      setReports(response.data ? (response.data as Report[]) : []);
    } catch (error) {
      console.error('Error loading reports:', error);
      setReports([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSendingReport(true);

    try {
      let response;

      if (formData.send_to_all) {
        // Bulk send to all parents
        response = await api.bulkSendReports({
          class_id: formTeacherClass.id,
          session_id: selectedSession,
          term_id: selectedTerm,
          report_type: formData.report_type,
          include_all_parents: true,
        });
      } else {
        // Send to selected parents
        if (formData.selected_parents.length === 0) {
          alert('Please select at least one parent');
          setSendingReport(false);
          return;
        }

        response = await api.createReport({
          class_id: formTeacherClass.id,
          session_id: selectedSession,
          term_id: selectedTerm,
          report_type: formData.report_type,
          parent_ids: formData.selected_parents,
        });
      }

      if (response.error) {
        alert(response.error);
      } else {
        alert('Reports sent successfully!');
        await loadReports();
        setShowSendModal(false);
        resetForm();
      }
    } catch (error) {
      alert('Failed to send reports');
    } finally {
      setSendingReport(false);
    }
  };

  const toggleParent = (parentId: string) => {
    if (formData.selected_parents.includes(parentId)) {
      setFormData({
        ...formData,
        selected_parents: formData.selected_parents.filter(id => id !== parentId),
      });
    } else {
      setFormData({
        ...formData,
        selected_parents: [...formData.selected_parents, parentId],
      });
    }
  };

  const resetForm = () => {
    setFormData({
      report_type: 'end_of_term',
      selected_parents: [],
      send_to_all: true,
    });
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
        <p className="text-gray-600 mt-1">Send reports for your form teacher class: {formTeacherClass.name}</p>
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
              onClick={() => setShowSendModal(true)}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              disabled={parents.length === 0}
            >
              Send Report
            </button>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-sm text-gray-600 mb-1">Students in Class</div>
          <div className="text-3xl font-bold text-gray-900">{students.length}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-sm text-gray-600 mb-1">Parent Accounts</div>
          <div className="text-3xl font-bold text-gray-900">{parents.length}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-sm text-gray-600 mb-1">Reports Sent</div>
          <div className="text-3xl font-bold text-blue-600">{reports.length}</div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Report History</h3>
        </div>

        <div className="p-6">
          {reports.length === 0 ? (
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
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="mt-4 text-gray-500">No reports sent yet for this term</p>
              <button
                onClick={() => setShowSendModal(true)}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                disabled={parents.length === 0}
              >
                Send First Report
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {reports.map((report) => (
                <div key={report.id} className="bg-gray-50 p-4 rounded-lg flex justify-between items-center">
                  <div>
                    <div className="font-medium text-gray-900 capitalize">
                      {report.report_type.replace(/_/g, ' ')}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      Sent {new Date(report.created_at).toLocaleDateString()} · {report.recipient_count} recipients
                    </div>
                  </div>
                  <span className="px-3 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                    Sent
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Send Report Modal */}
      {showSendModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-900">Send Report to Parents</h3>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Report Type <span className="text-red-600">*</span>
                </label>
                <select
                  value={formData.report_type}
                  onChange={(e) => setFormData({ ...formData, report_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="mid_term">Mid-Term Report</option>
                  <option value="end_of_term">End of Term Report</option>
                  <option value="annual">Annual Report</option>
                  <option value="progress_report">Progress Report</option>
                  <option value="custom">Custom Report</option>
                </select>
              </div>

              <div className="border-t pt-4">
                <div className="flex items-center gap-2 mb-4">
                  <input
                    type="checkbox"
                    id="send_to_all"
                    checked={formData.send_to_all}
                    onChange={(e) => setFormData({ ...formData, send_to_all: e.target.checked, selected_parents: [] })}
                    className="rounded"
                  />
                  <label htmlFor="send_to_all" className="text-sm font-medium text-gray-700">
                    Send to all parents ({parents.length} recipients)
                  </label>
                </div>

                {!formData.send_to_all && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Parents
                    </label>
                    <div className="border border-gray-300 rounded-lg max-h-64 overflow-y-auto">
                      {parents.length === 0 ? (
                        <div className="p-4 text-center text-gray-500 text-sm">
                          No parent accounts found for students in this class
                        </div>
                      ) : (
                        <div className="p-2 space-y-1">
                          {parents.map((parent) => (
                            <div
                              key={parent.id}
                              className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded"
                            >
                              <input
                                type="checkbox"
                                id={`parent-${parent.id}`}
                                checked={formData.selected_parents.includes(parent.id)}
                                onChange={() => toggleParent(parent.id)}
                                className="rounded"
                              />
                              <label htmlFor={`parent-${parent.id}`} className="flex-1 text-sm cursor-pointer">
                                {parent.first_name} {parent.last_name}
                                <span className="text-gray-500 ml-2">({parent.student_name})</span>
                              </label>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    {!formData.send_to_all && (
                      <p className="text-xs text-gray-500 mt-2">
                        Selected: {formData.selected_parents.length} parent{formData.selected_parents.length !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                )}
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-900">
                  <strong>Note:</strong> This will send {formData.send_to_all ? `reports to all ${parents.length} parent accounts` : `reports to ${formData.selected_parents.length} selected parent${formData.selected_parents.length !== 1 ? 's' : ''}`} for students in {formTeacherClass.name}.
                </p>
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t">
                <button
                  type="button"
                  onClick={() => {
                    setShowSendModal(false);
                    resetForm();
                  }}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                  disabled={sendingReport}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  disabled={sendingReport || (!formData.send_to_all && formData.selected_parents.length === 0)}
                >
                  {sendingReport ? 'Sending...' : 'Send Reports'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
