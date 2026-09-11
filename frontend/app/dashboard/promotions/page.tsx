'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { toast } from 'sonner';
import { confirm } from '@/lib/confirm';

interface Session {
  id: string;
  name: string;
  is_current: boolean;
  promotion_basis: 'third_term' | 'cumulative';
  promotion_pass_mark: number;
}

interface ClassOption {
  id: string;
  name: string;
}

interface PreviewRow {
  student_id: string;
  student_name: string;
  admission_number: string;
  from_class_id: string;
  from_class_name: string;
  basis_score: number | null;
  pass_mark: number;
  has_data: boolean;
  decision: 'promoted' | 'repeated' | 'graduated';
  to_class_id: string | null;
  to_class_name: string | null;
  is_graduating_class: boolean;
}

interface EditableRow extends PreviewRow {
  overridden: boolean;
}

const DECISION_STYLES: Record<string, string> = {
  promoted: 'bg-green-100 text-green-800',
  repeated: 'bg-red-100 text-red-800',
  graduated: 'bg-blue-100 text-blue-800',
};

export default function PromotionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionId, setSessionId] = useState('');
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [rows, setRows] = useState<EditableRow[]>([]);
  const [promotionBasis, setPromotionBasis] = useState<'third_term' | 'cumulative'>('third_term');
  const [passMark, setPassMark] = useState<number>(40);
  const [loading, setLoading] = useState(true);
  const [previewing, setPreviewing] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [committed, setCommitted] = useState(false);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const [sessionsRes, classesRes] = await Promise.all([
        api.getSessions(),
        api.getClasses(),
      ]);
      const sessionsData = (sessionsRes.data as Session[]) || [];
      setSessions(sessionsData);
      setClasses(((classesRes.data as ClassOption[]) || []).map((c) => ({ id: c.id, name: c.name })));

      const current = sessionsData.find((s) => s.is_current) || sessionsData[0];
      if (current) {
        setSessionId(current.id);
      }
    } catch {
      toast.error('Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (sessionId) loadPreview(sessionId);
  }, [sessionId]);

  const loadPreview = async (id: string) => {
    setPreviewing(true);
    setCommitted(false);
    try {
      const res = await api.previewPromotions(id);
      if (res.error) {
        toast.error(res.error);
        setRows([]);
        return;
      }
      const data = res.data as { promotion_basis: string; default_pass_mark: number; rows: PreviewRow[] };
      setPromotionBasis(data.promotion_basis as 'third_term' | 'cumulative');
      setPassMark(data.default_pass_mark);
      setRows(data.rows.map((r) => ({ ...r, overridden: false })));
    } catch {
      toast.error('Failed to compute promotion preview');
    } finally {
      setPreviewing(false);
    }
  };

  const updateRow = (studentId: string, changes: Partial<EditableRow>) => {
    setRows((prev) => prev.map((r) => (r.student_id === studentId ? { ...r, ...changes, overridden: true } : r)));
  };

  const handleDecisionChange = (row: EditableRow, decision: 'promoted' | 'repeated' | 'graduated') => {
    updateRow(row.student_id, {
      decision,
      to_class_id: decision === 'promoted' ? row.to_class_id : null,
      to_class_name: decision === 'promoted' ? row.to_class_name : null,
    });
  };

  const handleToClassChange = (row: EditableRow, classId: string) => {
    const cls = classes.find((c) => c.id === classId);
    updateRow(row.student_id, { to_class_id: classId || null, to_class_name: cls?.name || null });
  };

  const rowsMissingTarget = rows.filter((r) => r.decision === 'promoted' && !r.to_class_id);
  const summary = rows.reduce(
    (acc, r) => {
      acc[r.decision] = (acc[r.decision] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const handleCommit = async () => {
    if (rows.length === 0) return;
    if (rowsMissingTarget.length > 0) {
      toast.error(`${rowsMissingTarget.length} student(s) marked "Promoted" have no target class selected`);
      return;
    }

    const ok = await confirm({
      title: 'Commit promotions?',
      message: `This will move ${summary.promoted || 0} student(s) to their next class, mark ${summary.graduated || 0} as graduated, and keep ${summary.repeated || 0} in their current class. This cannot be undone from here.`,
      confirmLabel: 'Commit',
      danger: true,
    });
    if (!ok) return;

    setCommitting(true);
    try {
      const res = await api.commitPromotions({
        session_id: sessionId,
        decisions: rows.map((r) => ({
          student_id: r.student_id,
          decision: r.decision,
          to_class_id: r.decision === 'promoted' ? r.to_class_id : undefined,
          basis_score: r.basis_score,
          override_reason: r.overridden ? 'Admin adjusted the computed outcome' : undefined,
        })),
      });

      if (res.error) {
        toast.error(res.error);
        return;
      }

      const body = res.data as { promoted: number; repeated: number; graduated: number; failed: number };
      if (body.failed > 0) {
        toast.warning(`Committed with ${body.failed} failure(s): ${body.promoted} promoted, ${body.repeated} repeated, ${body.graduated} graduated`);
      } else {
        toast.success(`Done: ${body.promoted} promoted, ${body.repeated} repeated, ${body.graduated} graduated`);
      }
      setCommitted(true);
    } catch {
      toast.error('Failed to commit promotions');
    } finally {
      setCommitting(false);
    }
  };

  const rowsByClass = rows.reduce((acc, r) => {
    (acc[r.from_class_name] = acc[r.from_class_name] || []).push(r);
    return acc;
  }, {} as Record<string, EditableRow[]>);

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Promotions</h1>
          <p className="text-sm text-gray-600 mt-1">
            Review and commit end-of-session promotion, repeat, and graduation decisions.
          </p>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500">Loading...</p>
        ) : sessions.length === 0 ? (
          <p className="text-sm text-gray-500">No academic sessions found. Create one under Academic Setup first.</p>
        ) : (
          <>
            <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6 flex flex-wrap items-end gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Session</label>
                <select
                  value={sessionId}
                  onChange={(e) => setSessionId(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 min-w-[200px]"
                >
                  {sessions.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}{s.is_current ? ' (Current)' : ''}</option>
                  ))}
                </select>
              </div>
              <div className="text-sm text-gray-600">
                <p>
                  Basis: <span className="font-medium">{promotionBasis === 'third_term' ? '3rd term only' : 'Average of all 3 terms'}</span>
                </p>
                <p>Pass mark: <span className="font-medium">{passMark}%</span></p>
              </div>
              <div className="ml-auto text-sm text-gray-600">
                {rows.length > 0 && (
                  <span>
                    {summary.promoted || 0} promoted &middot; {summary.repeated || 0} repeated &middot; {summary.graduated || 0} graduated
                  </span>
                )}
              </div>
            </div>

            {previewing ? (
              <p className="text-sm text-gray-500">Computing outcomes...</p>
            ) : rows.length === 0 ? (
              <p className="text-sm text-gray-500">No active students with a current class found for this session.</p>
            ) : (
              <>
                {Object.entries(rowsByClass).map(([className, classRows]) => (
                  <div key={className} className="bg-white rounded-lg border border-gray-200 mb-4 overflow-hidden">
                    <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 font-medium text-sm text-gray-700">
                      {className} ({classRows.length})
                    </div>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 text-sm">
                        <thead>
                          <tr className="text-left text-xs text-gray-500 uppercase">
                            <th className="px-4 py-2">Student</th>
                            <th className="px-4 py-2">Score</th>
                            <th className="px-4 py-2">Decision</th>
                            <th className="px-4 py-2">Next class</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {classRows.map((row) => (
                            <tr key={row.student_id}>
                              <td className="px-4 py-2">
                                <div className="font-medium text-gray-900">{row.student_name}</div>
                                <div className="text-xs text-gray-500">{row.admission_number}</div>
                              </td>
                              <td className="px-4 py-2">
                                {row.has_data ? `${row.basis_score?.toFixed(1)}%` : (
                                  <span className="text-xs text-amber-600">No score</span>
                                )}
                              </td>
                              <td className="px-4 py-2">
                                <select
                                  value={row.decision}
                                  onChange={(e) => handleDecisionChange(row, e.target.value as 'promoted' | 'repeated' | 'graduated')}
                                  className={`px-2 py-1 rounded text-xs font-medium border-0 ${DECISION_STYLES[row.decision]}`}
                                >
                                  <option value="promoted">Promoted</option>
                                  <option value="repeated">Repeated</option>
                                  <option value="graduated">Graduated</option>
                                </select>
                              </td>
                              <td className="px-4 py-2">
                                {row.decision === 'promoted' ? (
                                  <select
                                    value={row.to_class_id || ''}
                                    onChange={(e) => handleToClassChange(row, e.target.value)}
                                    className={`px-2 py-1 border rounded text-xs ${!row.to_class_id ? 'border-red-400' : 'border-gray-300'}`}
                                  >
                                    <option value="">Select class...</option>
                                    {classes.filter((c) => c.id !== row.from_class_id).map((c) => (
                                      <option key={c.id} value={c.id}>{c.name}</option>
                                    ))}
                                  </select>
                                ) : (
                                  <span className="text-gray-400 text-xs">&mdash;</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}

                <div className="flex items-center gap-4 sticky bottom-4">
                  <button
                    onClick={handleCommit}
                    disabled={committing || committed}
                    className="bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium shadow-lg"
                  >
                    {committing ? 'Committing...' : committed ? 'Committed' : 'Commit promotions'}
                  </button>
                  {rowsMissingTarget.length > 0 && (
                    <span className="text-sm text-red-600">
                      {rowsMissingTarget.length} promoted student(s) still need a target class
                    </span>
                  )}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
