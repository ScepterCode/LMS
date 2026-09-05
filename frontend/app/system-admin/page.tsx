'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import SystemAdminLayout from '@/components/SystemAdminLayout';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatCard } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LinkButton } from '@/components/ui/Button';

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
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingEmail, setTestingEmail] = useState(false);
  const [testEmailResult, setTestEmailResult] = useState<{ sent: boolean; detail: string } | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const handleTestEmail = async () => {
    setTestingEmail(true);
    setTestEmailResult(null);
    const response = await api.sendTestEmail();
    setTestingEmail(false);
    if (response.error) {
      setTestEmailResult({ sent: false, detail: response.error });
      return;
    }
    setTestEmailResult(response.data as { sent: boolean; detail: string });
  };

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

  const statusTone = (status: string) => (status === 'trial' ? 'warning' : undefined);

  return (
    <SystemAdminLayout>
      <div className="space-y-6">
        <PageHeader
          title="Platform Overview"
          subtitle="Monitor and manage every school on the platform"
          actions={<LinkButton href="/system-admin/organizations">View All Organizations</LinkButton>}
        />

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
          </div>
        ) : (
          <>
            <div className="grid md:grid-cols-4 gap-6">
              <StatCard label="Total Schools" value={analytics?.organizations.total ?? 0} hint={`${analytics?.organizations.active ?? 0} active`} />
              <StatCard label="Total Users" value={analytics?.users.total ?? 0} hint={`${analytics?.users.admin ?? 0} admins`} />
              <StatCard label="Trial Schools" value={analytics?.organizations.trial ?? 0} hint="On free trial" />
              <StatCard label="Suspended" value={analytics?.organizations.suspended ?? 0} hint="Requires attention" />
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Email Delivery</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Sends a test email to your own account's address through Resend, to confirm outbound email is configured.
                  </p>
                </div>
                <button
                  onClick={handleTestEmail}
                  disabled={testingEmail}
                  className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 whitespace-nowrap text-sm font-medium"
                >
                  {testingEmail ? 'Sending...' : 'Send test email'}
                </button>
              </div>
              {testEmailResult && (
                <div className={`mt-4 text-sm rounded-lg px-4 py-3 ${
                  testEmailResult.sent ? 'bg-success-50 text-success-700' : 'bg-danger-50 text-danger-700'
                }`}>
                  {testEmailResult.detail}
                </div>
              )}
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Recent Organizations</h3>
                <Link href="/system-admin/organizations" className="text-sm text-brand-600 hover:text-brand-800 font-medium">
                  View all &rarr;
                </Link>
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
                    {organizations.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-gray-500">No organizations yet</td>
                      </tr>
                    ) : (
                      organizations.map((org) => (
                        <tr key={org.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <Link href={`/system-admin/organizations/${org.id}`} className="text-sm font-medium text-brand-600 hover:text-brand-800">
                              {org.name}
                            </Link>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{org.email}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <Badge tone={statusTone(org.subscription_status)}>{org.subscription_status}</Badge>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{org.subscription_plan_id}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {new Date(org.created_at).toLocaleDateString()}
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
      </div>
    </SystemAdminLayout>
  );
}
