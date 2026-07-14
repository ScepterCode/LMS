'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';

interface Child {
  student_id: string;
  student_name: string;
  admission_number: string;
  class_name?: string;
  relationship: string;
  is_primary: boolean;
}

interface ReportCardSummary {
  id: string;
  session_name?: string;
  term_name?: string;
  average_score?: number;
  overall_grade?: string;
  overall_position?: number;
  class_size?: number;
  status: string;
}

interface SubjectGrade {
  id: string;
  subject_name?: string;
  total_score?: number;
  grade?: string;
  remark?: string;
}

interface ReportCardDetail extends ReportCardSummary {
  class_teacher_remark?: string;
  attendance_percentage?: number;
  days_present: number;
  days_absent: number;
  days_late: number;
  subject_grades: SubjectGrade[];
  skill_ratings: { category_name: string; domain: string; rating: string }[];
}

interface AttendanceRecord {
  id: string;
  attendance_date: string;
  status: string;
}

export default function MyChildrenPage() {
  const [children, setChildren] = useState<Child[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedChild, setSelectedChild] = useState<string>('');

  const [reportCards, setReportCards] = useState<ReportCardSummary[]>([]);
  const [selectedReportCard, setSelectedReportCard] = useState<ReportCardDetail | null>(null);
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    loadChildren();
  }, []);

  useEffect(() => {
    if (selectedChild) loadChildDetail(selectedChild);
  }, [selectedChild]);

  const loadChildren = async () => {
    setLoading(true);
    const res = await api.get('/api/v1/parents/me/children');
    if (res.error) {
      setError(res.error);
    } else {
      const data = (res.data as Child[]) || [];
      setChildren(data);
      if (data.length > 0) setSelectedChild(data[0].student_id);
    }
    setLoading(false);
  };

  const loadChildDetail = async (studentId: string) => {
    setLoadingDetail(true);
    setSelectedReportCard(null);
    const [reportCardsRes, attendanceRes] = await Promise.all([
      api.get(`/api/v1/grading/students/${studentId}/report-cards`),
      api.get(`/api/v1/attendance/student/${studentId}`),
    ]);
    setReportCards((reportCardsRes.data as ReportCardSummary[]) || []);
    setAttendance((attendanceRes.data as AttendanceRecord[]) || []);
    setLoadingDetail(false);
  };

  const openReportCard = async (id: string) => {
    const res = await api.get(`/api/v1/grading/report-cards/${id}`);
    if (res.data) setSelectedReportCard(res.data as ReportCardDetail);
  };

  const attendanceCounts = attendance.reduce(
    (acc, r) => {
      acc[r.status] = (acc[r.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      present: 'bg-green-100 text-green-800',
      absent: 'bg-red-100 text-red-800',
      late: 'bg-yellow-100 text-yellow-800',
      excused: 'bg-blue-100 text-blue-800',
    };
    return (
      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    );
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Children</h1>
          <p className="text-gray-600 mt-1">View grades, report cards, and attendance for your children</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>
        )}

        {children.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
            No children are linked to your account yet. Contact your school's administrator to have your child linked.
          </div>
        ) : (
          <>
            {children.length > 1 && (
              <div className="flex gap-2 flex-wrap">
                {children.map((child) => (
                  <button
                    key={child.student_id}
                    onClick={() => setSelectedChild(child.student_id)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium border ${
                      selectedChild === child.student_id
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {child.student_name}
                  </button>
                ))}
              </div>
            )}

            {(() => {
              const child = children.find((c) => c.student_id === selectedChild);
              if (!child) return null;
              return (
                <div className="bg-white rounded-lg shadow p-4">
                  <h2 className="text-lg font-semibold text-gray-900">{child.student_name}</h2>
                  <p className="text-sm text-gray-500">
                    {child.admission_number} {child.class_name && `• ${child.class_name}`} • You are their {child.relationship}
                    {child.is_primary && ' (Primary Guardian)'}
                  </p>
                </div>
              );
            })()}

            {loadingDetail ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="grid lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="px-6 py-4 border-b">
                    <h3 className="font-semibold text-gray-900">Report Cards</h3>
                  </div>
                  {reportCards.length === 0 ? (
                    <p className="p-6 text-sm text-gray-500 text-center">No report cards published yet</p>
                  ) : (
                    <div className="divide-y">
                      {reportCards.map((rc) => (
                        <button
                          key={rc.id}
                          onClick={() => openReportCard(rc.id)}
                          className="w-full text-left px-6 py-3 hover:bg-gray-50 flex items-center justify-between"
                        >
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {rc.session_name} - {rc.term_name}
                            </p>
                            <p className="text-xs text-gray-500 capitalize">{rc.status}</p>
                          </div>
                          {rc.overall_grade && (
                            <span className="text-sm font-semibold text-gray-700">{rc.overall_grade}</span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="px-6 py-4 border-b flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900">Attendance</h3>
                    <div className="flex gap-2 text-xs text-gray-500">
                      <span>{attendanceCounts.present || 0} present</span>
                      <span>{attendanceCounts.absent || 0} absent</span>
                      <span>{attendanceCounts.late || 0} late</span>
                    </div>
                  </div>
                  {attendance.length === 0 ? (
                    <p className="p-6 text-sm text-gray-500 text-center">No attendance records yet</p>
                  ) : (
                    <div className="divide-y max-h-96 overflow-y-auto">
                      {attendance.slice(0, 30).map((r) => (
                        <div key={r.id} className="px-6 py-2 flex items-center justify-between text-sm">
                          <span className="text-gray-600">{new Date(r.attendance_date).toLocaleDateString()}</span>
                          {statusBadge(r.status)}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}

        {selectedReportCard && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold">
                  {selectedReportCard.session_name} - {selectedReportCard.term_name} Report Card
                </h3>
                <button onClick={() => setSelectedReportCard(null)} className="text-gray-400 hover:text-gray-600">
                  ✕
                </button>
              </div>

              <div className="p-6 space-y-6">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">Average</p>
                    <p className="text-lg font-semibold text-gray-900">{selectedReportCard.average_score ?? '-'}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">Grade</p>
                    <p className="text-lg font-semibold text-gray-900">{selectedReportCard.overall_grade ?? '-'}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">Position</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {selectedReportCard.overall_position ? `${selectedReportCard.overall_position} / ${selectedReportCard.class_size}` : '-'}
                    </p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Subject Grades</h4>
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Grade</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {selectedReportCard.subject_grades.map((g) => (
                        <tr key={g.id}>
                          <td className="px-3 py-2 text-sm text-gray-900">{g.subject_name}</td>
                          <td className="px-3 py-2 text-sm text-gray-600">{g.total_score ?? '-'}</td>
                          <td className="px-3 py-2 text-sm text-gray-600">{g.grade ?? '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {selectedReportCard.skill_ratings.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Skills</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      {selectedReportCard.skill_ratings.map((s, i) => (
                        <div key={i} className="flex justify-between">
                          <span className="text-gray-600">{s.category_name}</span>
                          <span className="font-medium text-gray-900">{s.rating}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedReportCard.class_teacher_remark && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Class Teacher's Remark</h4>
                    <p className="text-sm text-gray-600">{selectedReportCard.class_teacher_remark}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
