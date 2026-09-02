'use client';

import { useState, useEffect, useMemo } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';

interface FinancialAnalytics {
  total_expected: number;
  total_collected: number;
  total_outstanding: number;
  collection_rate: number;
  students_fully_paid: number;
  students_partial_payment: number;
  students_no_payment: number;
  students_overdue: number;
  total_students: number;
}

interface StudentFeesSummary {
  student_id: string;
  student_name: string;
  total_fees: number;
  total_paid: number;
  total_outstanding: number;
  fees: Array<{
    category_name: string;
    final_amount: number;
    amount_paid: number;
    balance: number;
    status: string;
  }>;
}

interface StructureRow {
  id: string;
  category_name?: string;
  class_name?: string;
  class_level?: string;
  session_id?: string;
  amount: number;
  payment_frequency: string;
  is_active: boolean;
}

export default function FinancialReportsPage() {
  const [analytics, setAnalytics] = useState<FinancialAnalytics | null>(null);
  const [studentSummary, setStudentSummary] = useState<StudentFeesSummary | null>(null);
  const [selectedStudent, setSelectedStudent] = useState('');
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState<'overview' | 'structures' | 'compare' | 'student'>('overview');
  const [currentSessionId, setCurrentSessionId] = useState('');
  const [sessions, setSessions] = useState<any[]>([]);
  const [structures, setStructures] = useState<StructureRow[]>([]);
  const [compareA, setCompareA] = useState('');
  const [compareB, setCompareB] = useState('');

  useEffect(() => {
    fetchStudents();
    fetchCurrentSessionAndAnalytics();
    fetchSessions();
    fetchStructures();
  }, []);

  useEffect(() => {
    if (selectedStudent && currentSessionId) {
      fetchStudentSummary();
    }
  }, [selectedStudent, currentSessionId]);

  const fetchStudents = async () => {
    try {
      const response = await api.get('/api/v1/students');
      setStudents(response.data || []);
    } catch (error) {
      console.error('Error fetching students:', error);
      setStudents([]); // Ensure students is always an array
    }
  };

  const fetchSessions = async () => {
    try {
      const res = await api.getSessions();
      const list = (res.data as any[]) || [];
      setSessions(list);
      // Default the comparison to (previous vs current) when possible.
      const currentIdx = list.findIndex((s) => s.is_current);
      if (currentIdx !== -1) {
        setCompareB(list[currentIdx].id);
        const prev = list[currentIdx + 1] || list[currentIdx - 1];
        if (prev) setCompareA(prev.id);
      } else if (list.length >= 2) {
        setCompareA(list[1].id);
        setCompareB(list[0].id);
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
      setSessions([]);
    }
  };

  const fetchStructures = async () => {
    try {
      const res = await api.get('/api/v1/fees/structures');
      setStructures((res.data as StructureRow[]) || []);
    } catch (error) {
      console.error('Error fetching fee structures:', error);
      setStructures([]);
    }
  };

  const fetchCurrentSessionAndAnalytics = async () => {
    try {
      const sessionsRes = await api.getSessions({ is_current: true });
      const sessions = sessionsRes.data as any[] | undefined;
      const currentSession = sessions?.[0];
      if (currentSession) {
        setCurrentSessionId(currentSession.id);
        await fetchFinancialAnalytics(currentSession.id);
      }
    } catch (error) {
      console.error('Error fetching current session:', error);
    }
  };

  const fetchFinancialAnalytics = async (sessionId: string) => {
    try {
      setLoading(true);
      const response = await api.get(`/api/v1/fees/analytics/financial?session_id=${sessionId}`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStudentSummary = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/v1/fees/analytics/student/${selectedStudent}?session_id=${currentSessionId}`);
      setStudentSummary(response.data);
    } catch (error) {
      console.error('Error fetching student summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return `₦${Number(amount).toLocaleString()}`;
  };

  const structureStats = useMemo(() => {
    const scoped = currentSessionId
      ? structures.filter((s) => !s.session_id || s.session_id === currentSessionId)
      : structures;
    const active = scoped.filter((s) => s.is_active);
    const amounts = scoped.map((s) => Number(s.amount) || 0);
    const highest = scoped.reduce<StructureRow | null>(
      (max, s) => (!max || Number(s.amount) > Number(max.amount) ? s : max),
      null,
    );

    const byCategory = new Map<string, { count: number; total: number }>();
    for (const s of scoped) {
      const key = s.category_name || 'Uncategorised';
      const entry = byCategory.get(key) || { count: 0, total: 0 };
      entry.count += 1;
      entry.total += Number(s.amount) || 0;
      byCategory.set(key, entry);
    }
    const categoryRows = [...byCategory.entries()]
      .map(([name, v]) => ({ name, ...v }))
      .sort((a, b) => b.total - a.total);
    const categoryMax = categoryRows.reduce((m, r) => Math.max(m, r.total), 0);

    const byClass = new Map<string, { count: number; total: number }>();
    for (const s of scoped) {
      const key = s.class_name || (s.class_level ? `All ${s.class_level} Classes` : 'All Classes');
      const entry = byClass.get(key) || { count: 0, total: 0 };
      entry.count += 1;
      entry.total += Number(s.amount) || 0;
      byClass.set(key, entry);
    }
    const classRows = [...byClass.entries()]
      .map(([name, v]) => ({ name, ...v }))
      .sort((a, b) => b.total - a.total);

    return {
      total: scoped.length,
      activeCount: active.length,
      average: amounts.length ? amounts.reduce((a, b) => a + b, 0) / amounts.length : 0,
      highest,
      categoryRows,
      categoryMax,
      classRows,
    };
  }, [structures, currentSessionId]);

  const comparison = useMemo(() => {
    if (!compareA || !compareB || compareA === compareB) return [];
    const scopeLabel = (s: StructureRow) =>
      s.class_name || (s.class_level ? `All ${s.class_level} Classes` : 'All Classes');
    const rowsByKey = new Map<string, { category: string; scope: string; a?: number; b?: number }>();
    for (const s of structures) {
      if (s.session_id !== compareA && s.session_id !== compareB) continue;
      const category = s.category_name || 'Uncategorised';
      const scope = scopeLabel(s);
      const key = `${category}|||${scope}`;
      const entry = rowsByKey.get(key) || { category, scope };
      if (s.session_id === compareA) entry.a = (entry.a || 0) + (Number(s.amount) || 0);
      if (s.session_id === compareB) entry.b = (entry.b || 0) + (Number(s.amount) || 0);
      rowsByKey.set(key, entry);
    }
    return [...rowsByKey.values()]
      .map((r) => {
        const delta = (r.b ?? 0) - (r.a ?? 0);
        const pct = r.a ? (delta / r.a) * 100 : null;
        return { ...r, delta, pct };
      })
      .sort((x, y) => x.category.localeCompare(y.category) || x.scope.localeCompare(y.scope));
  }, [structures, compareA, compareB]);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Financial Reports</h1>
            <p className="text-gray-600 mt-1">View fee collection and payment analytics</p>
          </div>
          {sessions.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Academic Session</label>
              <select
                value={currentSessionId}
                onChange={(e) => {
                  setCurrentSessionId(e.target.value);
                  if (e.target.value) fetchFinancialAnalytics(e.target.value);
                }}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                {sessions.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}{s.is_current ? ' (Current)' : ''}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* View Toggle */}
        <div className="flex flex-wrap gap-4">
          <button
            onClick={() => setActiveView('overview')}
            className={`px-4 py-2 rounded-lg border-2 transition-colors ${
              activeView === 'overview'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            Financial Overview
          </button>
          <button
            onClick={() => setActiveView('structures')}
            className={`px-4 py-2 rounded-lg border-2 transition-colors ${
              activeView === 'structures'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            Structure Breakdown
          </button>
          <button
            onClick={() => setActiveView('compare')}
            className={`px-4 py-2 rounded-lg border-2 transition-colors ${
              activeView === 'compare'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            Session Comparison
          </button>
          <button
            onClick={() => setActiveView('student')}
            className={`px-4 py-2 rounded-lg border-2 transition-colors ${
              activeView === 'student'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            Student Fee Summary
          </button>
        </div>

        {/* Financial Overview */}
        {activeView === 'overview' && analytics && (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Expected</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {formatCurrency(analytics.total_expected)}
                    </p>
                  </div>
                  <div className="p-3 bg-blue-100 rounded-full">
                    <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Collected</p>
                    <p className="text-2xl font-bold text-green-600 mt-1">
                      {formatCurrency(analytics.total_collected)}
                    </p>
                  </div>
                  <div className="p-3 bg-green-100 rounded-full">
                    <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="mt-2">
                  <span className="text-sm text-gray-600">
                    Collection Rate: <span className="font-bold text-green-600">{analytics.collection_rate.toFixed(1)}%</span>
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Outstanding</p>
                    <p className="text-2xl font-bold text-red-600 mt-1">
                      {formatCurrency(analytics.total_outstanding)}
                    </p>
                  </div>
                  <div className="p-3 bg-red-100 rounded-full">
                    <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            {/* Payment Status Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Fully Paid</h3>
                <div className="text-3xl font-bold text-green-600">{analytics.students_fully_paid}</div>
                <div className="text-sm text-gray-600 mt-1">
                  {((analytics.students_fully_paid / analytics.total_students) * 100).toFixed(1)}% of students
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Partial Payment</h3>
                <div className="text-3xl font-bold text-yellow-600">{analytics.students_partial_payment}</div>
                <div className="text-sm text-gray-600 mt-1">
                  {((analytics.students_partial_payment / analytics.total_students) * 100).toFixed(1)}% of students
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">No Payment</h3>
                <div className="text-3xl font-bold text-red-600">{analytics.students_no_payment}</div>
                <div className="text-sm text-gray-600 mt-1">
                  {((analytics.students_no_payment / analytics.total_students) * 100).toFixed(1)}% of students
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Overdue</h3>
                <div className="text-3xl font-bold text-red-700">{analytics.students_overdue}</div>
                <div className="text-sm text-gray-600 mt-1">
                  {((analytics.students_overdue / analytics.total_students) * 100).toFixed(1)}% of students
                </div>
              </div>
            </div>

            {/* Collection Progress */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Collection Progress</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Collected: {formatCurrency(analytics.total_collected)}</span>
                  <span className="font-medium text-gray-900">{analytics.collection_rate.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-green-600 h-4 rounded-full transition-all"
                    style={{ width: `${analytics.collection_rate}%` }}
                  />
                </div>
                <div className="flex justify-between text-sm text-gray-600">
                  <span>₦0</span>
                  <span>{formatCurrency(analytics.total_expected)}</span>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Structure Breakdown */}
        {activeView === 'structures' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">Fee Structures</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{structureStats.total}</p>
                <p className="text-sm text-gray-500 mt-1">{structureStats.activeCount} active</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">Average Fee</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(structureStats.average)}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">Highest Fee</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {structureStats.highest ? formatCurrency(Number(structureStats.highest.amount)) : '—'}
                </p>
                {structureStats.highest && (
                  <p className="text-sm text-gray-500 mt-1 truncate">
                    {structureStats.highest.category_name}
                    {' · '}
                    {structureStats.highest.class_name
                      || (structureStats.highest.class_level ? `All ${structureStats.highest.class_level} Classes` : 'All Classes')}
                  </p>
                )}
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">Categories in use</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{structureStats.categoryRows.length}</p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Total fee value by category</h3>
              {structureStats.categoryRows.length === 0 ? (
                <p className="text-sm text-gray-500">No fee structures for this session.</p>
              ) : (
                <div className="space-y-3">
                  {structureStats.categoryRows.map((row) => (
                    <div key={row.name}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-700">{row.name} <span className="text-gray-400">({row.count})</span></span>
                        <span className="font-medium text-gray-900">{formatCurrency(row.total)}</span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${structureStats.categoryMax ? (row.total / structureStats.categoryMax) * 100 : 0}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">By class</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Class</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Structures</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total fee value</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {structureStats.classRows.length === 0 ? (
                      <tr><td colSpan={3} className="px-6 py-8 text-center text-gray-500">No fee structures for this session.</td></tr>
                    ) : (
                      structureStats.classRows.map((row) => (
                        <tr key={row.name}>
                          <td className="px-6 py-3 text-sm text-gray-900">{row.name}</td>
                          <td className="px-6 py-3 text-sm text-gray-500 text-right">{row.count}</td>
                          <td className="px-6 py-3 text-sm text-gray-900 text-right">{formatCurrency(row.total)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* Session Comparison */}
        {activeView === 'compare' && (
          <>
            <div className="bg-white rounded-lg shadow p-6 flex flex-wrap items-end gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">From</label>
                <select
                  value={compareA}
                  onChange={(e) => setCompareA(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="">Select session</option>
                  {sessions.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}{s.is_current ? ' (Current)' : ''}</option>
                  ))}
                </select>
              </div>
              <span className="pb-2 text-gray-400">→</span>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">To</label>
                <select
                  value={compareB}
                  onChange={(e) => setCompareB(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="">Select session</option>
                  {sessions.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}{s.is_current ? ' (Current)' : ''}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Class</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">From</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">To</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Change</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {(!compareA || !compareB || compareA === compareB) ? (
                      <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">Pick two different sessions to compare.</td></tr>
                    ) : comparison.length === 0 ? (
                      <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">No fee structures in either session.</td></tr>
                    ) : (
                      comparison.map((r) => (
                        <tr key={`${r.category}-${r.scope}`}>
                          <td className="px-6 py-3 text-sm font-medium text-gray-900">{r.category}</td>
                          <td className="px-6 py-3 text-sm text-gray-500">{r.scope}</td>
                          <td className="px-6 py-3 text-sm text-gray-900 text-right">{r.a != null ? formatCurrency(r.a) : '—'}</td>
                          <td className="px-6 py-3 text-sm text-gray-900 text-right">{r.b != null ? formatCurrency(r.b) : '—'}</td>
                          <td className={`px-6 py-3 text-sm text-right font-medium ${
                            r.delta > 0 ? 'text-red-600' : r.delta < 0 ? 'text-green-600' : 'text-gray-400'
                          }`}>
                            {r.a == null ? 'New' : r.b == null ? 'Removed'
                              : r.delta === 0 ? 'No change'
                              : `${r.delta > 0 ? '+' : ''}${formatCurrency(r.delta)}${r.pct != null ? ` (${r.delta > 0 ? '+' : ''}${r.pct.toFixed(1)}%)` : ''}`}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* Student Fee Summary */}
        {activeView === 'student' && (
          <>
            <div className="bg-white rounded-lg shadow p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Student</label>
              <select
                value={selectedStudent}
                onChange={(e) => setSelectedStudent(e.target.value)}
                className="w-full max-w-2xl px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">Choose a student...</option>
                {(students || []).map(student => (
                  <option key={student.id} value={student.id}>
                    {student.admission_number} - {student.first_name} {student.last_name}
                  </option>
                ))}
              </select>
            </div>

            {loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="text-gray-500">Loading...</div>
              </div>
            ) : studentSummary ? (
              <>
                {/* Student Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <p className="text-sm text-gray-600">Total Fees</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {formatCurrency(studentSummary.total_fees)}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg shadow p-6">
                    <p className="text-sm text-gray-600">Amount Paid</p>
                    <p className="text-2xl font-bold text-green-600 mt-1">
                      {formatCurrency(studentSummary.total_paid)}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg shadow p-6">
                    <p className="text-sm text-gray-600">Outstanding</p>
                    <p className="text-2xl font-bold text-red-600 mt-1">
                      {formatCurrency(studentSummary.total_outstanding)}
                    </p>
                  </div>
                </div>

                {/* Fee Breakdown */}
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">Fee Breakdown</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fee Category</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Amount</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Paid</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Balance</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {(studentSummary?.fees || []).map((fee, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {fee.category_name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(fee.final_amount)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-medium">
                              {formatCurrency(fee.amount_paid)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 font-medium">
                              {formatCurrency(fee.balance)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                fee.status === 'paid'
                                  ? 'bg-green-100 text-green-800'
                                  : fee.status === 'partial'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {fee.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
                Select a student to view fee summary
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
