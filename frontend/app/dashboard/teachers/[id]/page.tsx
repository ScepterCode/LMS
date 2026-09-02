'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';

const TEACHER_STATUSES = [
  { value: 'active', label: 'Active' },
  { value: 'on-leave', label: 'On Leave' },
  { value: 'terminated', label: 'Terminated' },
  { value: 'retired', label: 'Retired' },
];

interface Teacher {
  id: string;
  user_id: string;
  staff_number: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  date_of_birth?: string;
  gender: string;
  email: string;
  phone: string;
  address?: string;
  state_of_origin?: string;
  lga?: string;
  nationality: string;
  photo_url?: string;
  qualification?: string;
  specialization?: string;
  employment_date?: string;
  employment_type: string;
  status: string;
  years_of_service?: number;
  subject_count?: number;
  class_count?: number;
  form_teacher_for?: { id: string; name: string }[];
  created_at: string;
}

interface SubjectAssignment {
  id: string;
  subject_name: string;
  class_name: string;
  session_name: string;
  term_name: string;
  is_form_teacher?: boolean;
}

export default function TeacherDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [teacher, setTeacher] = useState<Teacher | null>(null);
  const [assignments, setAssignments] = useState<SubjectAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [statusValue, setStatusValue] = useState('');
  const [statusSaving, setStatusSaving] = useState(false);

  useEffect(() => {
    fetchTeacherDetails();
    fetchAssignments();
  }, [params.id]);

  const openStatusModal = () => {
    if (teacher) setStatusValue(teacher.status);
    setShowStatusModal(true);
  };

  const handleStatusChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teacher || statusValue === teacher.status) {
      setShowStatusModal(false);
      return;
    }
    const inactive = statusValue === 'terminated' || statusValue === 'retired';
    if (inactive && !confirm(
      `Set ${teacher.first_name} ${teacher.last_name} to "${statusValue}"? This disables their login and clears their current-session class assignments.`
    )) return;

    setStatusSaving(true);
    const response = await api.updateTeacher(teacher.id, { status: statusValue });
    setStatusSaving(false);
    if (response.error) {
      alert(response.error);
      return;
    }
    setShowStatusModal(false);
    fetchTeacherDetails();
    fetchAssignments();
  };

  const fetchTeacherDetails = async () => {
    const response = await api.getTeacher(params.id as string);
    if (response.error) {
      setError(response.error);
    } else {
      setTeacher(response.data as Teacher);
    }
    setLoading(false);
  };

  const fetchAssignments = async () => {
    const response = await api.getTeacherAssignments(params.id as string);
    if (response.error) {
      console.error('Failed to fetch assignments:', response.error);
    } else {
      setAssignments((response.data as SubjectAssignment[]) || []);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center py-24">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading teacher details...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !teacher) {
    return (
      <DashboardLayout>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error || 'Teacher not found'}
        </div>
        <button
          onClick={() => router.push('/dashboard/teachers')}
          className="mt-4 text-blue-600 hover:text-blue-800"
        >
          ← Back to Teachers
        </button>
      </DashboardLayout>
    );
  }

  const getStatusColor = (status: string) => {
    const colors: any = {
      active: 'bg-green-100 text-green-800',
      'on-leave': 'bg-yellow-100 text-yellow-800',
      terminated: 'bg-red-100 text-red-800',
      retired: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getEmploymentTypeColor = (type: string) => {
    const colors: any = {
      'full-time': 'bg-blue-100 text-blue-800',
      'part-time': 'bg-purple-100 text-purple-800',
      contract: 'bg-orange-100 text-orange-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <DashboardLayout>
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.push('/dashboard/teachers')}
          className="text-blue-600 hover:text-blue-800 mb-4 inline-flex items-center"
        >
          ← Back to Teachers
        </button>

        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
              {teacher.first_name} {teacher.middle_name} {teacher.last_name}
            </h1>
            <p className="text-gray-600 mt-1">Staff Number: {teacher.staff_number}</p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={openStatusModal}
              className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50"
            >
              Change Status
            </button>
            <Link
              href={`/dashboard/teachers/${teacher.id}/edit`}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
            >
              Edit Teacher
            </Link>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Personal Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900">Personal Information</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Email</p>
                <p className="font-medium">{teacher.email}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Phone</p>
                <p className="font-medium">{teacher.phone}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Gender</p>
                <p className="font-medium capitalize">{teacher.gender}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Date of Birth</p>
                <p className="font-medium">
                  {teacher.date_of_birth ? new Date(teacher.date_of_birth).toLocaleDateString() : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">State of Origin</p>
                <p className="font-medium">{teacher.state_of_origin || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">LGA</p>
                <p className="font-medium">{teacher.lga || 'N/A'}</p>
              </div>
              <div className="col-span-2">
                <p className="text-sm text-gray-600">Address</p>
                <p className="font-medium">{teacher.address || 'N/A'}</p>
              </div>
            </div>
          </div>

          {/* Professional Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900">Professional Information</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Qualification</p>
                <p className="font-medium">{teacher.qualification || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Specialization</p>
                <p className="font-medium">{teacher.specialization || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Employment Date</p>
                <p className="font-medium">
                  {teacher.employment_date ? new Date(teacher.employment_date).toLocaleDateString() : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Years of Service</p>
                <p className="font-medium">{teacher.years_of_service || 0} years</p>
              </div>
            </div>
          </div>

          {/* Subject Assignments */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900">
              Class &amp; Subject Assignments ({assignments.length})
            </h2>

            {assignments.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No assignments yet</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Class</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Session</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Term</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {assignments.map((assignment) => (
                      <tr key={assignment.id}>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">{assignment.subject_name}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{assignment.class_name}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{assignment.session_name}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{assignment.term_name}</td>
                        <td className="px-4 py-3 text-sm">
                          {assignment.is_form_teacher && (
                            <span className="inline-block px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded-full font-medium">
                              Form Teacher
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Quick Stats</h3>
            <p className="text-xs text-gray-400 -mt-2 mb-3">Subjects/classes reflect the current academic session</p>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Status</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(teacher.status)}`}>
                  {teacher.status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Employment Type</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getEmploymentTypeColor(teacher.employment_type)}`}>
                  {teacher.employment_type}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Subjects Teaching</span>
                <span className="font-semibold">{teacher.subject_count || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Classes Teaching</span>
                <span className="font-semibold">{teacher.class_count || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Years of Service</span>
                <span className="font-semibold">{teacher.years_of_service || 0}</span>
              </div>
            </div>
          </div>

          {/* Form Teacher For */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Form Teacher For</h3>
            {teacher.form_teacher_for && teacher.form_teacher_for.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {teacher.form_teacher_for.map((cls) => (
                  <Link
                    key={cls.id}
                    href={`/dashboard/academic?tab=classes`}
                    className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium hover:bg-green-200"
                  >
                    {cls.name}
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">Not a form teacher this session</p>
            )}
          </div>

          {/* Additional Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Additional Info</h3>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">User ID</p>
                <p className="text-xs font-mono bg-gray-50 p-2 rounded">{teacher.user_id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Teacher ID</p>
                <p className="text-xs font-mono bg-gray-50 p-2 rounded">{teacher.id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Nationality</p>
                <p className="font-medium">{teacher.nationality}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Registered On</p>
                <p className="text-sm">{new Date(teacher.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {showStatusModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-sm w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-gray-900 mb-1">Change Employment Status</h2>
            <p className="text-sm text-gray-500 mb-4">
              {teacher.first_name} {teacher.last_name}
            </p>
            <form onSubmit={handleStatusChange} className="space-y-4">
              <select
                value={statusValue}
                onChange={(e) => setStatusValue(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                {TEACHER_STATUSES.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
              {(statusValue === 'terminated' || statusValue === 'retired') && (
                <p className="text-xs text-amber-700 bg-amber-50 rounded px-3 py-2">
                  Disables login and clears current-session class assignments. Setting back to Active re-enables login.
                </p>
              )}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={statusSaving}
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {statusSaving ? 'Saving…' : 'Save'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowStatusModal(false)}
                  className="flex-1 border border-gray-300 py-2 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
    </DashboardLayout>
  );
}
