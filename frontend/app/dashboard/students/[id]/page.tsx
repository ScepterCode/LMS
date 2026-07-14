'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import ProtectedRoute from '@/components/ProtectedRoute';
import GuardianModal from '@/components/GuardianModal';

interface Student {
  id: string;
  admission_number: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  full_name: string;
  date_of_birth: string;
  gender: string;
  blood_group?: string;
  email?: string;
  phone?: string;
  address: string;
  state_of_origin: string;
  lga: string;
  nationality: string;
  religion?: string;
  medical_conditions?: string;
  allergies?: string;
  current_class_id?: string;
  class_name?: string;
  status: string;
  age?: number;
  admission_date: string;
  created_at: string;
}

interface Guardian {
  id: string;
  guardian_type: string;
  title?: string;
  first_name: string;
  last_name: string;
  full_name: string;
  relationship: string;
  phone: string;
  email?: string;
  occupation?: string;
  address?: string;
  is_emergency_contact: boolean;
  is_primary: boolean;
}

interface LinkedParent {
  parent_id: string;
  full_name: string;
  relationship: string;
  is_primary: boolean;
  phone?: string;
  email?: string;
}

export default function StudentDetailPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const params = useParams();
  const studentId = params?.id as string;
  
  const [student, setStudent] = useState<Student | null>(null);
  const [guardians, setGuardians] = useState<Guardian[]>([]);
  const [linkedParents, setLinkedParents] = useState<LinkedParent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showGuardianModal, setShowGuardianModal] = useState(false);
  const [selectedGuardian, setSelectedGuardian] = useState<Guardian | null>(null);
  const [unlinkingParentId, setUnlinkingParentId] = useState<string | null>(null);

  useEffect(() => {
    if (studentId) {
      loadData();
    }
  }, [studentId]);

  const loadData = async () => {
    setLoading(true);
    setError('');

    try {
      // Load student
      const studentResponse = await api.getStudent(studentId);
      if (studentResponse.error) {
        setError(studentResponse.error);
      } else if (studentResponse.data) {
        setStudent(studentResponse.data as Student);
      }

      // Load guardians
      const guardiansResponse = await api.getStudentGuardians(studentId);
      if (guardiansResponse.data) {
        setGuardians(guardiansResponse.data as Guardian[]);
      }

      // Load linked parent accounts (distinct from the free-text guardians
      // above - these have a real login and dashboard access to this student)
      const parentsResponse = await api.get(`/api/v1/students/${studentId}/parents`);
      if (parentsResponse.data) {
        setLinkedParents(parentsResponse.data as LinkedParent[]);
      }
    } catch (err) {
      setError('Failed to load student data');
    } finally {
      setLoading(false);
    }
  };

  const handleUnlinkParent = async (parentId: string) => {
    if (!confirm('Remove this parent\'s access to this student?')) return;
    setUnlinkingParentId(parentId);
    const res = await api.unlinkParentFromStudent(parentId, studentId);
    if (res.error) {
      alert(res.error);
    } else {
      setLinkedParents((prev) => prev.filter((p) => p.parent_id !== parentId));
    }
    setUnlinkingParentId(null);
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      graduated: 'bg-blue-100 text-blue-800',
      suspended: 'bg-red-100 text-red-800',
      withdrawn: 'bg-gray-100 text-gray-800',
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const handleAddGuardian = () => {
    setSelectedGuardian(null);
    setShowGuardianModal(true);
  };

  const handleEditGuardian = (guardian: Guardian) => {
    setSelectedGuardian(guardian);
    setShowGuardianModal(true);
  };

  const handleModalClose = () => {
    setShowGuardianModal(false);
    setSelectedGuardian(null);
  };

  const handleModalSuccess = () => {
    loadData(); // Reload guardians
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <h1 className="text-xl font-bold text-blue-600">Nigerian LMS</h1>
              <div className="flex items-center gap-6">
                <Link href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">Dashboard</Link>
                <Link href="/dashboard/students" className="text-sm font-medium text-gray-900">Students</Link>
                <Link href="/dashboard/teachers" className="text-sm text-gray-600 hover:text-gray-900">Teachers</Link>
                <Link href="/dashboard/academic" className="text-sm text-gray-600 hover:text-gray-900">Academic</Link>
                <div className="border-l pl-6 flex items-center gap-4">
                  <span className="text-sm text-gray-600">{user?.full_name}</span>
                  <button onClick={handleLogout} className="text-sm text-gray-700 hover:text-gray-900">
                    Logout
                  </button>
                </div>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <Link href="/dashboard/students" className="text-sm text-blue-600 hover:text-blue-800 mb-2 inline-block">
              ← Back to Students
            </Link>
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Student Profile</h2>
                {student && <p className="text-gray-600">{student.admission_number}</p>}
              </div>
              {student && (
                <Link
                  href={`/dashboard/students/${studentId}/edit`}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Edit Student
                </Link>
              )}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-900">{error}</p>
            </div>
          )}

          {/* Loading */}
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : student ? (
            <div className="grid md:grid-cols-3 gap-6">
              {/* Main Info */}
              <div className="md:col-span-2 space-y-6">
                {/* Basic Information */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(student.status)}`}>
                      {student.status}
                    </span>
                  </div>
                  <dl className="grid grid-cols-2 gap-4">
                    <div>
                      <dt className="text-sm text-gray-600">Full Name</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.full_name}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Admission Number</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.admission_number}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Date of Birth</dt>
                      <dd className="text-sm font-medium text-gray-900">
                        {new Date(student.date_of_birth).toLocaleDateString()} ({student.age} years)
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Gender</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.gender}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Blood Group</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.blood_group || 'Not specified'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Current Class</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.class_name || 'Not assigned'}</dd>
                    </div>
                  </dl>
                </div>

                {/* Contact Information */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
                  <dl className="grid grid-cols-2 gap-4">
                    <div>
                      <dt className="text-sm text-gray-600">Email</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.email || 'Not provided'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Phone</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.phone || 'Not provided'}</dd>
                    </div>
                    <div className="col-span-2">
                      <dt className="text-sm text-gray-600">Address</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.address}</dd>
                    </div>
                  </dl>
                </div>

                {/* Additional Information */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Information</h3>
                  <dl className="grid grid-cols-2 gap-4">
                    <div>
                      <dt className="text-sm text-gray-600">State of Origin</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.state_of_origin}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">LGA</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.lga}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Nationality</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.nationality}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Religion</dt>
                      <dd className="text-sm font-medium text-gray-900">{student.religion || 'Not specified'}</dd>
                    </div>
                  </dl>
                </div>

                {/* Medical Information */}
                {(student.medical_conditions || student.allergies) && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Medical Information</h3>
                    <dl className="space-y-3">
                      {student.medical_conditions && (
                        <div>
                          <dt className="text-sm text-gray-600">Medical Conditions</dt>
                          <dd className="text-sm font-medium text-gray-900 mt-1">{student.medical_conditions}</dd>
                        </div>
                      )}
                      {student.allergies && (
                        <div>
                          <dt className="text-sm text-gray-600">Allergies</dt>
                          <dd className="text-sm font-medium text-gray-900 mt-1">{student.allergies}</dd>
                        </div>
                      )}
                    </dl>
                  </div>
                )}
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Linked Parent Accounts */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Linked Parent Accounts</h3>
                    <button
                      onClick={handleAddGuardian}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      + Add
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mb-3">
                    Registered parents with dashboard access to this student's grades and attendance.
                  </p>
                  {linkedParents.length === 0 ? (
                    <p className="text-sm text-gray-500">No parent accounts linked yet</p>
                  ) : (
                    <div className="space-y-3">
                      {linkedParents.map((parent) => (
                        <div key={parent.parent_id} className="border rounded-lg p-3">
                          <div className="flex items-start justify-between mb-1">
                            <div>
                              <p className="text-sm font-medium text-gray-900">{parent.full_name}</p>
                              <p className="text-xs text-gray-500">{parent.relationship}</p>
                            </div>
                            {parent.is_primary && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Primary</span>
                            )}
                          </div>
                          <div className="text-xs text-gray-600 space-y-1">
                            {parent.phone && <p>📞 {parent.phone}</p>}
                            {parent.email && <p>📧 {parent.email}</p>}
                          </div>
                          <button
                            onClick={() => handleUnlinkParent(parent.parent_id)}
                            disabled={unlinkingParentId === parent.parent_id}
                            className="text-xs text-red-600 hover:text-red-800 mt-2 disabled:opacity-50"
                          >
                            {unlinkingParentId === parent.parent_id ? 'Removing...' : 'Unlink'}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Guardians (emergency contacts without a login) */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Other Emergency Contacts</h3>
                  </div>
                  {guardians.length === 0 ? (
                    <p className="text-sm text-gray-500">No emergency contacts added</p>
                  ) : (
                    <div className="space-y-4">
                      {guardians.map((guardian) => (
                        <div key={guardian.id} className="border rounded-lg p-3">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <p className="text-sm font-medium text-gray-900">{guardian.full_name}</p>
                              <p className="text-xs text-gray-500">{guardian.relationship}</p>
                            </div>
                            {guardian.is_primary && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Primary</span>
                            )}
                          </div>
                          <div className="text-xs text-gray-600 space-y-1">
                            <p>📞 {guardian.phone}</p>
                            {guardian.email && <p>📧 {guardian.email}</p>}
                            {guardian.occupation && <p>💼 {guardian.occupation}</p>}
                          </div>
                          {guardian.is_emergency_contact && (
                            <p className="text-xs text-red-600 mt-2">⚠️ Emergency Contact</p>
                          )}
                          <button
                            onClick={() => handleEditGuardian(guardian)}
                            className="text-xs text-blue-600 hover:text-blue-800 mt-2"
                          >
                            Edit
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Quick Stats */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Info</h3>
                  <dl className="space-y-3">
                    <div>
                      <dt className="text-sm text-gray-600">Admission Date</dt>
                      <dd className="text-sm font-medium text-gray-900">
                        {new Date(student.admission_date).toLocaleDateString()}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Created</dt>
                      <dd className="text-sm font-medium text-gray-900">
                        {new Date(student.created_at).toLocaleDateString()}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Linked Parents</dt>
                      <dd className="text-sm font-medium text-gray-900">{linkedParents.length}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Other Contacts</dt>
                      <dd className="text-sm font-medium text-gray-900">{guardians.length}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            </div>
          ) : null}

          {/* Guardian Modal */}
          {showGuardianModal && student && (
            <GuardianModal
              studentId={studentId}
              guardian={selectedGuardian}
              onClose={handleModalClose}
              onSuccess={handleModalSuccess}
            />
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
