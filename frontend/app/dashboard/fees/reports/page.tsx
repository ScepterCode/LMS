'use client';

import { useState, useEffect } from 'react';
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

export default function FinancialReportsPage() {
  const [analytics, setAnalytics] = useState<FinancialAnalytics | null>(null);
  const [studentSummary, setStudentSummary] = useState<StudentFeesSummary | null>(null);
  const [selectedStudent, setSelectedStudent] = useState('');
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState<'overview' | 'student'>('overview');

  useEffect(() => {
    fetchStudents();
    fetchFinancialAnalytics();
  }, []);

  useEffect(() => {
    if (selectedStudent) {
      fetchStudentSummary();
    }
  }, [selectedStudent]);

  const fetchStudents = async () => {
    try {
      const response = await api.get('/api/v1/students');
      setStudents(response.data || []);
    } catch (error) {
      console.error('Error fetching students:', error);
      setStudents([]); // Ensure students is always an array
    }
  };

  const fetchFinancialAnalytics = async () => {
    try {
      setLoading(true);
      // You'll need to pass actual session_id
      const response = await api.get('/api/v1/fees/analytics/financial?session_id=');
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
      // You'll need to pass actual session_id
      const response = await api.get(`/api/v1/fees/analytics/student/${selectedStudent}?session_id=`);
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

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Financial Reports</h1>
          <p className="text-gray-600 mt-1">View fee collection and payment analytics</p>
        </div>

        {/* View Toggle */}
        <div className="flex gap-4">
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
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
