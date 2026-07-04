'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import LinkStudentModal from '@/components/LinkStudentModal';

interface Parent {
  id: string;
  user_id: string;
  title?: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  email: string;
  occupation?: string;
  address?: string;
  created_at: string;
}

interface Child {
  id: string;
  student_id: string;
  student_name: string;
  admission_number: string;
  class_name?: string;
  relationship: string;
  is_primary: boolean;
}

export default function ParentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [parent, setParent] = useState<Parent | null>(null);
  const [children, setChildren] = useState<Child[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showLinkModal, setShowLinkModal] = useState(false);

  useEffect(() => {
    if (params.id) {
      fetchParentDetails();
      fetchChildren();
    }
  }, [params.id]);

  const fetchParentDetails = async () => {
    try {
      const response = await api.get(`/parents/${params.id}`);
      setParent(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch parent details');
    } finally {
      setLoading(false);
    }
  };

  const fetchChildren = async () => {
    try {
      const response = await api.get(`/parents/${params.id}/children`);
      setChildren(response.data);
    } catch (err) {
      console.error('Failed to fetch children:', err);
    }
  };

  const handleLinkStudent = () => {
    setShowLinkModal(true);
  };

  const handleModalClose = () => {
    setShowLinkModal(false);
  };

  const handleModalSuccess = () => {
    fetchChildren(); // Reload children list
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading parent details...</p>
        </div>
      </div>
    );
  }

  if (error || !parent) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error || 'Parent not found'}
        </div>
        <button
          onClick={() => router.push('/dashboard/parents')}
          className="mt-4 text-blue-600 hover:text-blue-800"
        >
          ← Back to Parents
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.push('/dashboard/parents')}
          className="text-blue-600 hover:text-blue-800 mb-4 inline-flex items-center"
        >
          ← Back to Parents
        </button>
        
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {parent.title && `${parent.title} `}{parent.full_name}
            </h1>
            <p className="text-gray-600 mt-1">Parent/Guardian Profile</p>
          </div>
          
          <Link
            href={`/dashboard/parents/${parent.id}/edit`}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Edit Parent
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Contact Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900">Contact Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Email</p>
                <p className="font-medium">{parent.email}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Phone</p>
                <p className="font-medium">{parent.phone}</p>
              </div>
              {parent.address && (
                <div className="col-span-2">
                  <p className="text-sm text-gray-600">Address</p>
                  <p className="font-medium">{parent.address}</p>
                </div>
              )}
            </div>
          </div>

          {/* Professional Information */}
          {parent.occupation && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-900">Professional Information</h2>
              <div>
                <p className="text-sm text-gray-600">Occupation</p>
                <p className="font-medium">{parent.occupation}</p>
              </div>
            </div>
          )}

          {/* Children/Wards */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Wards ({children.length})
              </h2>
              <button
                onClick={handleLinkStudent}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                + Link Student
              </button>
            </div>
            
            {children.length === 0 ? (
              <div className="text-center py-8">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                <p className="text-gray-500 mt-2">No wards linked yet</p>
                <button
                  onClick={handleLinkStudent}
                  className="mt-4 text-blue-600 hover:text-blue-800 text-sm"
                >
                  Click "+ Link Student" to add a ward
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {children.map((child) => (
                  <div
                    key={child.id}
                    className="border rounded-lg p-4 hover:bg-gray-50"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-gray-900">{child.student_name}</h3>
                          {child.is_primary && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                              Primary
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mt-1">
                          Admission: {child.admission_number}
                        </p>
                        <p className="text-sm text-gray-600">
                          Class: {child.class_name || 'Not assigned'}
                        </p>
                        <p className="text-sm text-gray-600">
                          Relationship: {child.relationship}
                        </p>
                      </div>
                      <Link
                        href={`/dashboard/students/${child.student_id}`}
                        className="text-blue-600 hover:text-blue-800 text-sm"
                      >
                        View Student →
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Quick Stats</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Wards</span>
                <span className="font-semibold">{children.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Primary Guardian</span>
                <span className="font-semibold">
                  {children.filter(c => c.is_primary).length}
                </span>
              </div>
            </div>
          </div>

          {/* Account Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Account Info</h3>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Parent ID</p>
                <p className="text-xs font-mono bg-gray-50 p-2 rounded">{parent.id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">User ID</p>
                <p className="text-xs font-mono bg-gray-50 p-2 rounded">{parent.user_id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Registered On</p>
                <p className="text-sm">{new Date(parent.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          </div>

          {/* Portal Access */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 mb-2">🔐 Portal Access</h4>
            <p className="text-sm text-blue-800 mb-2">
              This parent can login to:
            </p>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• View ward's grades and scores</li>
              <li>• Check attendance records</li>
              <li>• Communicate with teachers</li>
              <li>• View assignments and progress</li>
            </ul>
            <p className="text-xs text-blue-600 mt-3">
              Login Email: {parent.email}
            </p>
          </div>
        </div>
      </div>

      {/* Link Student Modal */}
      {showLinkModal && parent && (
        <LinkStudentModal
          parentId={parent.id}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}
    </div>
  );
}
