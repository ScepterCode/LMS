'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import OnboardingChecklist from '@/components/OnboardingChecklist';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Card, StatCard } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

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

const ADMIN_ROLES = ['admin', 'system_admin', 'dean'];
const STUDENT_MANAGEMENT_ROLES = [...ADMIN_ROLES, 'teacher'];

export default function SchoolDashboard() {
  const { user } = useAuth();
  const isAdmin = ADMIN_ROLES.includes(user?.role ?? '');
  const canManageStudents = STUDENT_MANAGEMENT_ROLES.includes(user?.role ?? '');
  const isParent = user?.role === 'parent';
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
    <ProtectedRoute>
    <DashboardLayout>
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-1">
          Welcome, {user?.full_name}
        </h2>
        <p className="text-gray-500">
          {orgData?.organization.name || 'Loading...'}
        </p>
      </div>

      {/* Onboarding Checklist */}
      {isAdmin ? (
        <OnboardingChecklist />
      ) : null}

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
            </div>
          ) : (
            <>
              {orgData?.organization.subscription_status === 'trial' && (
                <div className="bg-warning-50 border border-warning-100 rounded-lg p-4 mb-6">
                  <div className="flex items-center gap-3">
                    <svg className="w-5 h-5 text-warning-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <p className="text-sm font-medium text-warning-700">
                        Trial Period: {getTrialDaysRemaining()} days remaining
                      </p>
                      <p className="text-xs text-warning-600">
                        Upgrade to continue using all features after your trial ends
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid sm:grid-cols-2 md:grid-cols-5 gap-4 mb-8">
                <StatCard label="Students" value={orgData?.statistics.students || 0} hint="Enrolled students" />
                <StatCard label="Teachers" value={orgData?.statistics.users.teacher || 0} hint="Teaching staff" />
                <StatCard label="Parents" value={orgData?.statistics.users.parent || 0} hint="Parent accounts" />
                <StatCard label="Campuses" value={orgData?.statistics.campuses || 0} hint="Locations" />
                <StatCard
                  label="Subscription"
                  value={orgData?.subscription_plan?.name || 'Trial'}
                  hint={orgData?.organization.subscription_status}
                />
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {canManageStudents && (
                  <Card title="Student Management">
                    <div className="space-y-3">
                      <Link
                        href="/dashboard/students"
                        className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-brand-200 transition-colors"
                      >
                        <div className="font-medium text-gray-900">Manage Students</div>
                        <div className="text-sm text-gray-500">Add, edit, view student records</div>
                      </Link>
                      {isAdmin && (
                        <Link
                          href="/dashboard/enrollments"
                          className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-brand-200 transition-colors"
                        >
                          <div className="font-medium text-gray-900">Class Enrollments</div>
                          <div className="text-sm text-gray-500">Enroll students in classes</div>
                        </Link>
                      )}
                    </div>
                  </Card>
                )}

                {isParent && (
                  <Card title="My Children">
                    <div className="space-y-3">
                      <Link
                        href="/dashboard/my-children"
                        className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-brand-200 transition-colors"
                      >
                        <div className="font-medium text-gray-900">View My Children</div>
                        <div className="text-sm text-gray-500">Grades, report cards, and attendance</div>
                      </Link>
                    </div>
                  </Card>
                )}

                {isAdmin && (
                  <Card title="Staff Management">
                    <div className="space-y-3">
                      <Link
                        href="/dashboard/teachers"
                        className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-brand-200 transition-colors"
                      >
                        <div className="font-medium text-gray-900">Manage Teachers</div>
                        <div className="text-sm text-gray-500">Add and manage teaching staff</div>
                      </Link>
                      <Link
                        href="/dashboard/assignments"
                        className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-brand-200 transition-colors"
                      >
                        <div className="font-medium text-gray-900">Subject Assignments</div>
                        <div className="text-sm text-gray-500">Assign teachers to subjects</div>
                      </Link>
                    </div>
                  </Card>
                )}

                {isAdmin && (
                  <Card title="Academic Setup">
                    <div className="space-y-3">
                      <Link
                        href="/dashboard/academic"
                        className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-brand-200 transition-colors"
                      >
                        <div className="font-medium text-gray-900">Academic Structure</div>
                        <div className="text-sm text-gray-500">Sessions, terms, classes, subjects</div>
                      </Link>
                    </div>
                  </Card>
                )}

                <Card title="Organization Info">
                  <dl className="space-y-3">
                    <div>
                      <dt className="text-sm text-gray-500">School Name</dt>
                      <dd className="text-sm font-medium text-gray-900">{orgData?.organization.name}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">Email</dt>
                      <dd className="text-sm font-medium text-gray-900">{orgData?.organization.email}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">Plan</dt>
                      <dd className="text-sm font-medium text-gray-900">
                        {orgData?.subscription_plan?.name || 'Trial'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">Status</dt>
                      <dd>
                        {orgData?.organization.subscription_status && (
                          <Badge tone={orgData.organization.subscription_status === 'active' ? 'success' : orgData.organization.subscription_status === 'trial' ? 'warning' : 'neutral'}>
                            {orgData.organization.subscription_status}
                          </Badge>
                        )}
                      </dd>
                    </div>
                  </dl>
                </Card>
              </div>
            </>
          )}
    </DashboardLayout>
    </ProtectedRoute>
  );
}
