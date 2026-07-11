'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import SystemAdminLayout from '@/components/SystemAdminLayout';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, StatCard } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

interface OrganizationDetail {
  id: string;
  name: string;
  slug: string;
  email: string;
  phone: string | null;
  address: string | null;
  subscription_plan_id: string;
  subscription_status: string;
  trial_ends_at: string | null;
  is_active: boolean;
  created_at: string;
}

interface Statistics {
  users: {
    admin: number;
    teacher: number;
    bursar: number;
    parent: number;
    total: number;
  };
  campuses: number;
}

const STATUS_OPTIONS = ['trial', 'active', 'suspended', 'cancelled'];

export default function OrganizationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const orgId = params.id as string;

  const [organization, setOrganization] = useState<OrganizationDetail | null>(null);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updating, setUpdating] = useState(false);
  const [pendingStatus, setPendingStatus] = useState<string | null>(null);

  useEffect(() => {
    loadOrganization();
  }, [orgId]);

  const loadOrganization = async () => {
    setLoading(true);
    setError('');
    const res = await api.getSystemAdminOrganization(orgId);
    if (res.error) {
      setError(res.error);
    } else if (res.data) {
      const data = res.data as { organization: OrganizationDetail; statistics: Statistics };
      setOrganization(data.organization);
      setStatistics(data.statistics);
    }
    setLoading(false);
  };

  const handleStatusChange = async (newStatus: string) => {
    if (!organization || newStatus === organization.subscription_status) return;
    setPendingStatus(newStatus);
  };

  const confirmStatusChange = async () => {
    if (!pendingStatus) return;
    setUpdating(true);
    const res = await api.updateOrganizationStatus(orgId, pendingStatus);
    if (res.error) {
      setError(res.error);
    } else {
      await loadOrganization();
    }
    setUpdating(false);
    setPendingStatus(null);
  };

  const statusTone = (status: string) => (status === 'trial' ? 'warning' : undefined);

  if (loading) {
    return (
      <SystemAdminLayout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
        </div>
      </SystemAdminLayout>
    );
  }

  if (error && !organization) {
    return (
      <SystemAdminLayout>
        <div className="text-center py-12">
          <p className="text-danger-600 mb-4">{error}</p>
          <Link href="/system-admin/organizations" className="text-brand-600 hover:text-brand-800">
            &larr; Back to Organizations
          </Link>
        </div>
      </SystemAdminLayout>
    );
  }

  if (!organization) return null;

  return (
    <SystemAdminLayout>
      <div className="space-y-6">
        <div>
          <Link href="/system-admin/organizations" className="text-sm text-brand-600 hover:text-brand-800 font-medium">
            &larr; Back to Organizations
          </Link>
        </div>

        <PageHeader
          title={organization.name}
          subtitle={organization.email}
          actions={<Badge tone={statusTone(organization.subscription_status)}>{organization.subscription_status}</Badge>}
        />

        {error && (
          <div className="bg-danger-50 border border-danger-100 text-danger-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="grid sm:grid-cols-3 gap-4">
          <StatCard label="Total Users" value={statistics?.users.total ?? 0} />
          <StatCard label="Campuses" value={statistics?.campuses ?? 0} />
          <StatCard label="Plan" value={organization.subscription_plan_id} />
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">School Information</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Slug</dt>
                <dd className="text-gray-900 font-medium">{organization.slug}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Email</dt>
                <dd className="text-gray-900 font-medium">{organization.email}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Phone</dt>
                <dd className="text-gray-900 font-medium">{organization.phone || '-'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Address</dt>
                <dd className="text-gray-900 font-medium text-right">{organization.address || '-'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Trial Ends</dt>
                <dd className="text-gray-900 font-medium">
                  {organization.trial_ends_at ? new Date(organization.trial_ends_at).toLocaleDateString() : '-'}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd className="text-gray-900 font-medium">{new Date(organization.created_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">User Breakdown</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Admins</dt>
                <dd className="text-gray-900 font-medium">{statistics?.users.admin ?? 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Teachers</dt>
                <dd className="text-gray-900 font-medium">{statistics?.users.teacher ?? 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Bursars</dt>
                <dd className="text-gray-900 font-medium">{statistics?.users.bursar ?? 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Parents</dt>
                <dd className="text-gray-900 font-medium">{statistics?.users.parent ?? 0}</dd>
              </div>
            </dl>
          </Card>
        </div>

        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Subscription Status</h3>
          <p className="text-sm text-gray-600 mb-4">
            Changing this affects what the school can do on the platform. Suspending blocks their access immediately.
          </p>
          <div className="flex flex-wrap gap-2">
            {STATUS_OPTIONS.map((status) => (
              <Button
                key={status}
                variant={status === organization.subscription_status ? 'primary' : 'secondary'}
                size="sm"
                disabled={status === organization.subscription_status || updating}
                onClick={() => handleStatusChange(status)}
              >
                {status === 'suspended' || status === 'cancelled' ? status : `Set ${status}`}
              </Button>
            ))}
          </div>
        </Card>

        {pendingStatus && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Confirm status change</h3>
              <p className="text-sm text-gray-600 mb-6">
                Change <strong>{organization.name}</strong>&apos;s status from{' '}
                <strong>{organization.subscription_status}</strong> to <strong>{pendingStatus}</strong>?
                {pendingStatus === 'suspended' && ' This will immediately restrict the school\'s access.'}
              </p>
              <div className="flex justify-end gap-3">
                <Button variant="secondary" onClick={() => setPendingStatus(null)} disabled={updating}>
                  Cancel
                </Button>
                <Button
                  variant={pendingStatus === 'suspended' || pendingStatus === 'cancelled' ? 'danger' : 'primary'}
                  onClick={confirmStatusChange}
                  disabled={updating}
                >
                  {updating ? 'Updating...' : 'Confirm'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </SystemAdminLayout>
  );
}
