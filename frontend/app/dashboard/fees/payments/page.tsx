'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';

interface Student {
  id: string;
  admission_number: string;
  first_name: string;
  last_name: string;
}

interface StudentFee {
  id: string;
  category_name: string;
  final_amount: number;
  amount_paid: number;
  balance: number;
  status: string;
}

interface Payment {
  id: string;
  receipt_number: string;
  student_name?: string;
  student_admission_number?: string;
  payment_date: string;
  amount: number;
  payment_method: string;
  status: string;
}

export default function PaymentsPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'record' | 'history'>('record');
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudent, setSelectedStudent] = useState('');
  const [studentFees, setStudentFees] = useState<StudentFee[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    student_id: '',
    payment_date: new Date().toISOString().split('T')[0],
    amount: '',
    payment_method: 'cash',
    reference_number: '',
    payer_name: '',
    payer_phone: '',
    notes: ''
  });
  const [selectedFees, setSelectedFees] = useState<Record<string, number>>({});

  useEffect(() => {
    fetchStudents();
    if (activeTab === 'history') {
      fetchPayments();
    }
  }, [activeTab]);

  useEffect(() => {
    if (selectedStudent) {
      fetchStudentFees();
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

  const fetchStudentFees = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/v1/fees/student-fees?student_id=${selectedStudent}`);
      // Filter only unpaid or partially paid fees
      const unpaidFees = (response.data || []).filter((fee: StudentFee) => 
        fee.status === 'pending' || fee.status === 'partial'
      );
      setStudentFees(unpaidFees);
      
      // Initialize selected fees with balances
      const fees: Record<string, number> = {};
      unpaidFees.forEach((fee: StudentFee) => {
        fees[fee.id] = 0;
      });
      setSelectedFees(fees);
    } catch (error) {
      console.error('Error fetching student fees:', error);
      setStudentFees([]); // Ensure studentFees is always an array
      setSelectedFees({});
    } finally {
      setLoading(false);
    }
  };

  const fetchPayments = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/fees/payments');
      setPayments(response.data || []);
    } catch (error) {
      console.error('Error fetching payments:', error);
      setPayments([]); // Ensure payments is always an array
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedStudent) {
      alert('Please select a student');
      return;
    }

    const totalAllocated = Object.values(selectedFees).reduce((sum, amount) => sum + amount, 0);
    const paymentAmount = parseFloat(formData.amount);

    if (totalAllocated > paymentAmount) {
      alert('Total allocated amount cannot exceed payment amount');
      return;
    }

    // Build fee allocations
    const feeAllocations = Object.entries(selectedFees)
      .filter(([_, amount]) => amount > 0)
      .map(([feeId, amount]) => ({
        student_fee_id: feeId,
        allocated_amount: amount
      }));

    if (feeAllocations.length === 0) {
      alert('Please allocate payment to at least one fee');
      return;
    }

    try {
      const paymentData = {
        ...formData,
        student_id: selectedStudent,
        amount: paymentAmount,
        fee_allocations: feeAllocations
      };

      await api.post('/api/v1/fees/payments', paymentData);
      alert('Payment recorded successfully!');
      
      // Reset form
      setFormData({
        student_id: '',
        payment_date: new Date().toISOString().split('T')[0],
        amount: '',
        payment_method: 'cash',
        reference_number: '',
        payer_name: '',
        payer_phone: '',
        notes: ''
      });
      setSelectedStudent('');
      setStudentFees([]);
      setSelectedFees({});
      
      // Refresh payments list
      setActiveTab('history');
    } catch (error: any) {
      console.error('Error recording payment:', error);
      alert(error.response?.data?.detail || 'Failed to record payment');
    }
  };

  const handleFeeAllocation = (feeId: string, amount: number) => {
    const fee = studentFees.find(f => f.id === feeId);
    if (fee && amount > Number(fee.balance)) {
      alert(`Amount cannot exceed balance of ₦${Number(fee.balance).toLocaleString()}`);
      return;
    }

    setSelectedFees({
      ...selectedFees,
      [feeId]: amount
    });
  };

  const totalBalance = studentFees.reduce((sum, fee) => sum + Number(fee.balance), 0);
  const totalAllocated = Object.values(selectedFees).reduce((sum, amount) => sum + amount, 0);
  const paymentAmount = parseFloat(formData.amount) || 0;
  const unallocated = paymentAmount - totalAllocated;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Payment Management</h1>
            <p className="text-gray-600 mt-1">Record and manage fee payments</p>
          </div>
          <button
            onClick={() => router.push('/dashboard/fees/reports')}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
          >
            Financial Reports
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('record')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'record'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Record Payment
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Payment History
            </button>
          </nav>
        </div>

        {/* Record Payment Tab */}
        {activeTab === 'record' && (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Student Selection */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Student Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Select Student *</label>
                  <select
                    required
                    value={selectedStudent}
                    onChange={(e) => {
                      setSelectedStudent(e.target.value);
                      setFormData({...formData, student_id: e.target.value});
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="">Choose a student...</option>
                    {(students || []).map(student => (
                      <option key={student.id} value={student.id}>
                        {student.admission_number} - {student.first_name} {student.last_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Outstanding Fees */}
            {selectedStudent && studentFees.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Outstanding Fees</h3>
                <div className="space-y-3">
                  {studentFees.map((fee) => (
                    <div key={fee.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{fee.category_name}</div>
                        <div className="text-sm text-gray-500">
                          Balance: ₦{Number(fee.balance).toLocaleString()} (of ₦{Number(fee.final_amount).toLocaleString()})
                        </div>
                      </div>
                      <div className="ml-4">
                        <input
                          type="number"
                          min="0"
                          max={Number(fee.balance)}
                          step="0.01"
                          value={selectedFees[fee.id] || 0}
                          onChange={(e) => handleFeeAllocation(fee.id, parseFloat(e.target.value) || 0)}
                          className="w-32 px-3 py-2 border border-gray-300 rounded-lg"
                          placeholder="Amount"
                        />
                      </div>
                    </div>
                  ))}
                  <div className="pt-3 border-t border-gray-200">
                    <div className="text-sm text-gray-600">Total Outstanding: <span className="font-bold text-red-600">₦{totalBalance.toLocaleString()}</span></div>
                  </div>
                </div>
              </div>
            )}

            {/* Payment Details */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Payment Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Payment Date *</label>
                  <input
                    type="date"
                    required
                    value={formData.payment_date}
                    onChange={(e) => setFormData({...formData, payment_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Amount Paid *</label>
                  <input
                    type="number"
                    required
                    min="0"
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) => setFormData({...formData, amount: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="0.00"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method *</label>
                  <select
                    required
                    value={formData.payment_method}
                    onChange={(e) => setFormData({...formData, payment_method: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="cash">Cash</option>
                    <option value="bank_transfer">Bank Transfer</option>
                    <option value="card">Card</option>
                    <option value="cheque">Cheque</option>
                    <option value="online">Online Payment</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Reference Number</label>
                  <input
                    type="text"
                    value={formData.reference_number}
                    onChange={(e) => setFormData({...formData, reference_number: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="Transaction reference"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Payer Name</label>
                  <input
                    type="text"
                    value={formData.payer_name}
                    onChange={(e) => setFormData({...formData, payer_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="Who is paying"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Payer Phone</label>
                  <input
                    type="tel"
                    value={formData.payer_phone}
                    onChange={(e) => setFormData({...formData, payer_phone: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="Phone number"
                  />
                </div>
              </div>
              
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  rows={3}
                  placeholder="Additional notes (optional)"
                />
              </div>
            </div>

            {/* Summary */}
            {paymentAmount > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">Payment Amount</div>
                    <div className="text-lg font-bold text-gray-900">₦{paymentAmount.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Allocated to Fees</div>
                    <div className="text-lg font-bold text-green-600">₦{totalAllocated.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Unallocated</div>
                    <div className={`text-lg font-bold ${unallocated > 0 ? 'text-yellow-600' : 'text-gray-900'}`}>
                      ₦{unallocated.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={!selectedStudent || !formData.amount}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Record Payment
              </button>
            </div>
          </form>
        )}

        {/* Payment History Tab */}
        {activeTab === 'history' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {loading ? (
              <div className="p-12 text-center text-gray-500">Loading payments...</div>
            ) : payments.length === 0 ? (
              <div className="p-12 text-center text-gray-500">No payments recorded yet</div>
            ) : (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Receipt No.</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {payments.map((payment) => (
                    <tr key={payment.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {payment.receipt_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{payment.student_name || 'N/A'}</div>
                        <div className="text-sm text-gray-500">{payment.student_admission_number}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(payment.payment_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                        ₦{Number(payment.amount).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {payment.payment_method.replace('_', ' ')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          payment.status === 'confirmed'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {payment.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => alert(`View receipt: ${payment.receipt_number}`)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View Receipt
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
