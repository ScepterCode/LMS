'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import ProtectedRoute from '@/components/ProtectedRoute';

interface Analytics {
  organizations: {
    total: number;
    trial: number;
    active: number;
    suspended: number;
    cancelled: number;
  };
  users: {
    total: number;
    admin: number;
    teacher: number;
    bursar: number;
    parent: number;
  };
  summary: {
    total_organizations: number;
    total_users: number;
    active_organizations: number;
    trial_organizations: number;
  };
}

interface Organization {
  id: string;
  name: string;
  email: string;
  subscription_status: string;
  subscription_plan_id: string;
  trial_ends_at: string;
  created_at: string;
}

export default function SystemAdminDashboard() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    const [analyticsRes, orgsRes] = await Promise.all([
      api.getPlatformAnalytics(),
      api.getOrganizations({ limit: 10 }),
    ]);

    if (analyticsRes.data) setAnalytics(analyticsRes.data as Analytics);
    if (orgsRes.data) setOrganizations((orgsRes.data as any).organizations);
    setLoading(false);
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <ProtectedRoute requiredRole="system_admin">
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <h1 className="text-xl font-bold text-blue-600">Nigerian LMS - System Admin</h1>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">{user?.full_name}</span>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Platform Overview</h2>
            <p className="text-gray-600">Monitor and manage all schools on the platform</p>
          </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              <div className="grid md:grid-cols-4 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <div className="text-sm text-gray-600 mb-1">Total Schools</div>
                  <div className="text-3xl font-bold text-gray-900">{analytics?.organizations.total || 0}</div>
                  <div className="text-xs text-gray-500 mt-2">
                    {analytics?.organizations.active || 0} active
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <div className="text-sm text-gray-600 mb-1">Total Users</div>
                  <div className="text-3xl font-bold text-gray-900">{analytics?.users.total || 0}</div>
                  <div className="text-xs text-gray-500 mt-2">
                    {analytics?.users.admin || 0} admins
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <div className="text-sm text-gray-600 mb-1">Trial Schools</div>
                  <div className="text-3xl font-bold text-orange-600">{analytics?.organizations.trial || 0}</div>
                  <div className="text-xs text-gray-500 mt-2">
                    On free trial
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <div className="text-sm text-gray-600 mb-1">Suspended</div>
                  <div className="text-3xl font-bold text-red-600">{analytics?.organizations.suspended || 0}</div>
                  <div className="text-xs text-gray-500 mt-2">
                    Requires attention
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm">
                <div className="px-6 py-4 border-b">
                  <h3 className="text-lg font-semibold text-gray-900">Recent Organizations</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">School Name</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plan</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {organizations.map((org) => (
                        <tr key={org.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{org.name}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-600">{org.email}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              org.subscription_status === 'active' ? 'bg-green-100 text-green-800' :
                              org.subscription_status === 'trial' ? 'bg-yellow-100 text-yellow-800' :
                              org.subscription_status === 'suspended' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {org.subscription_status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {org.subscription_plan_id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {new Date(org.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
