'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import OnboardingChecklist from '@/components/OnboardingChecklist';

interface OrganizationData {
  organization: {
    id: string;
    name: string;
    email: string;
    subscription_status: string;
    subscription_plan_id: string;
    trial_ends_at: string;
  };
  subscription_plan?: {
    name: string;
    price_monthly: number;
  };
  statistics: {
    users: {
      admin: number;
      teacher: number;
      bursar: number;
      parent: number;
      total: number;
    };
    campuses: number;
    students?: number;
  };
}

export default function SchoolDashboard() {
  const { user } = useAuth();
  const [orgData, setOrgData] = useState<OrganizationData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.school_id) {
      loadOrganizationData();
    }
  }, [user]);

  const loadOrganizationData = async () => {
    if (!user?.school_id) return;
    
    setLoading(true);
    const response = await api.getOrganization(user.school_id);
    if (response.data) {
      const orgData = response.data as OrganizationData;
      
      // Load student count
      const studentsResponse = await api.getStudents({ limit: 1 });
      if (studentsResponse.data && Array.isArray(studentsResponse.data)) {
        orgData.statistics.students = studentsResponse.data.length;
      } else {
        orgData.statistics.students = 0;
      }
      
      setOrgData(orgData);
    }
    setLoading(false);
  };

  const getTrialDaysRemaining = () => {
    if (!orgData?.organization.trial_ends_at) return 0;
    const trialEnd = new Date(orgData.organization.trial_ends_at);
    const now = new Date();
    const diff = trialEnd.getTime() - now.getTime();
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  };

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Welcome, {user?.full_name}
        </h2>
        <p className="text-gray-600">
          {orgData?.organization.name || 'Loading...'}
        </p>
      </div>

      {/* Onboarding Checklist */}
      {user?.role === 'admin' || user?.role === 'system_admin' ? (
        <OnboardingChecklist />
      ) : null}

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {orgData?.organization.subscription_status === 'trial' && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                  <div className="flex items-center gap-3">
                    <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <p className="text-sm font-medium text-yellow-900">
                        Trial Period: {getTrialDaysRemaining()} days remaining
                      </p>
                      <p className="text-xs text-yellow-700">
                        Upgrade to continue using all features after your trial ends
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid md:grid-cols-5 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <div className="text-sm text-gray-600 mb-1">Students</div>
                  <div className="text-3xl font-bold text-gray-900">
                    {orgData?.statistics.students || 0}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    Enrolled students
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <div className="text-sm text-gray-600 mb-1">Teachers</div>
                  <div className="text-3xl font-bold text-gray-900">
                    {orgData?.statistics.users.teacher || 0}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    Teaching staff
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <div className="text-sm text-gray-600 mb-1">Parents</div>
                  <div className="text-3xl font-bold text-gray-900">
                    {orgData?.statistics.users.parent || 0}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    Parent accounts
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <div className="text-sm text-gray-600 mb-1">Campuses</div>
                  <div className="text-3xl font-bold text-gray-900">
                    {orgData?.statistics.campuses || 0}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    Locations
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <div className="text-sm text-gray-600 mb-1">Subscription</div>
                  <div className="text-lg font-bold text-blue-600">
                    {orgData?.organization.subscription_status}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {orgData?.subscription_plan?.name || 'Trial'}
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Student Management</h3>
                  <div className="space-y-3">
                    <Link
                      href="/dashboard/students"
                      className="block p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="font-medium text-gray-900">Manage Students</div>
                      <div className="text-sm text-gray-600">Add, edit, view student records</div>
                    </Link>
                    <Link
                      href="/dashboard/enrollments"
                      className="block p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="font-medium text-gray-900">Class Enrollments</div>
                      <div className="text-sm text-gray-600">Enroll students in classes</div>
                    </Link>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Staff Management</h3>
                  <div className="space-y-3">
                    <Link
                      href="/dashboard/teachers"
                      className="block p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="font-medium text-gray-900">Manage Teachers</div>
                      <div className="text-sm text-gray-600">Add and manage teaching staff</div>
                    </Link>
                    <Link
                      href="/dashboard/assignments"
                      className="block p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="font-medium text-gray-900">Subject Assignments</div>
                      <div className="text-sm text-gray-600">Assign teachers to subjects</div>
                    </Link>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Academic Setup</h3>
                  <div className="space-y-3">
                    <Link
                      href="/dashboard/academic"
                      className="block p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="font-medium text-gray-900">Academic Structure</div>
                      <div className="text-sm text-gray-600">Sessions, terms, classes, subjects</div>
                    </Link>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Organization Info</h3>
                  <dl className="space-y-3">
                    <div>
                      <dt className="text-sm text-gray-600">School Name</dt>
                      <dd className="text-sm font-medium text-gray-900">{orgData?.organization.name}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Email</dt>
                      <dd className="text-sm font-medium text-gray-900">{orgData?.organization.email}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Plan</dt>
                      <dd className="text-sm font-medium text-gray-900">
                        {orgData?.subscription_plan?.name || 'Trial'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-600">Status</dt>
                      <dd>
                        <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                          orgData?.organization.subscription_status === 'active' ? 'bg-green-100 text-green-800' :
                          orgData?.organization.subscription_status === 'trial' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {orgData?.organization.subscription_status}
                        </span>
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>
            </>
          )}
    </DashboardLayout>
  );
}
