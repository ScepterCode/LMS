'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import SystemAdminLayout from '@/components/SystemAdminLayout';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatCard } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { PasswordInput } from '@/components/ui/PasswordInput';

interface Organization {
  id: string;
  name: string;
  email: string;
  subscription_status: string;
  subscription_plan_id: string;
  trial_ends_at: string | null;
  created_at: string;
}

interface SubscriptionPlan {
  id: string;
  name: string;
}

const TRIAL_WARNING_DAYS = 3;

function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null;
  const diffMs = new Date(dateStr).getTime() - Date.now();
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
}

const emptyOnboardForm = {
  school_name: '',
  school_email: '',
  school_phone: '',
  school_address: '',
  admin_name: '',
  admin_email: '',
  admin_password: '',
  admin_phone: '',
  subscription_plan_id: 'trial',
  subscription_status: 'trial',
};

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [expiringOnly, setExpiringOnly] = useState(false);

  const [showOnboardModal, setShowOnboardModal] = useState(false);
  const [onboardForm, setOnboardForm] = useState(emptyOnboardForm);
  const [onboardError, setOnboardError] = useState('');
  const [onboardSuccess, setOnboardSuccess] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadOrganizations();
  }, [statusFilter]);

  useEffect(() => {
    api.getSubscriptionPlans().then((res) => {
      if (res.data) setPlans((res.data as any).plans ?? []);
    });
  }, []);

  const loadOrganizations = async () => {
    setLoading(true);
    const res = await api.getOrganizations({ limit: 500, status: statusFilter || undefined });
    const data = (res.data as any)?.organizations as Organization[] | undefined;
    setOrganizations(data ?? []);
    setLoading(false);
  };

  const statusTone = (status: string) => (status === 'trial' ? 'warning' : undefined);

  const filtered = organizations
    .filter((org) =>
      org.name.toLowerCase().includes(search.toLowerCase()) ||
      org.email.toLowerCase().includes(search.toLowerCase())
    )
    .filter((org) => {
      if (!expiringOnly) return true;
      const days = daysUntil(org.trial_ends_at);
      return days !== null && days <= TRIAL_WARNING_DAYS;
    });

  const expiringCount = organizations.filter((org) => {
    const days = daysUntil(org.trial_ends_at);
    return days !== null && days <= TRIAL_WARNING_DAYS;
  }).length;

  const openOnboardModal = () => {
    setOnboardForm(emptyOnboardForm);
    setOnboardError('');
    setOnboardSuccess('');
    setShowOnboardModal(true);
  };

  const handleOnboard = async () => {
    setSaving(true);
    setOnboardError('');
    const res = await api.createOrganizationBySystemAdmin({
      school_name: onboardForm.school_name,
      school_email: onboardForm.school_email,
      school_phone: onboardForm.school_phone || undefined,
      school_address: onboardForm.school_address || undefined,
      admin_name: onboardForm.admin_name,
      admin_email: onboardForm.admin_email,
      admin_password: onboardForm.admin_password,
      admin_phone: onboardForm.admin_phone || undefined,
      subscription_plan_id: onboardForm.subscription_plan_id,
      subscription_status: onboardForm.subscription_status,
    });

    if (res.error) {
      setOnboardError(res.error);
      setSaving(false);
      return;
    }

    setSaving(false);
    setOnboardSuccess(`School created. Admin can log in with ${onboardForm.admin_email}.`);
    await loadOrganizations();
  };

  return (
    <SystemAdminLayout>
      <div className="space-y-6">
        <PageHeader
          title="Organizations"
          subtitle="Every school on the platform"
          actions={<Button onClick={openOnboardModal}>Add School</Button>}
        />

        <div className="grid sm:grid-cols-3 gap-4">
          <StatCard label="Total Schools" value={organizations.length} />
          <StatCard
            label="Trial Expiring Soon"
            value={expiringCount}
            hint={`Within ${TRIAL_WARNING_DAYS} days`}
          />
          <StatCard
            label="Suspended"
            value={organizations.filter((o) => o.subscription_status === 'suspended').length}
          />
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="grid sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Name or email..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              >
                <option value="">All Statuses</option>
                <option value="trial">Trial</option>
                <option value="active">Active</option>
                <option value="suspended">Suspended</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={expiringOnly}
                  onChange={(e) => setExpiringOnly(e.target.checked)}
                  className="h-4 w-4 text-brand-600 border-gray-300 rounded"
                />
                Trial expiring soon only
              </label>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">School Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plan</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trial Ends</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">Loading...</td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">No organizations found</td>
                  </tr>
                ) : (
                  filtered.map((org) => {
                    const days = daysUntil(org.trial_ends_at);
                    return (
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
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {org.trial_ends_at ? (
                            <span className={days !== null && days <= TRIAL_WARNING_DAYS ? 'text-danger-600 font-medium' : 'text-gray-600'}>
                              {new Date(org.trial_ends_at).toLocaleDateString()}
                              {days !== null && days <= TRIAL_WARNING_DAYS && ` (${days <= 0 ? 'expired' : `${days}d left`})`}
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {showOnboardModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 my-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Add School</h3>

              {onboardError && (
                <div className="bg-danger-50 border border-danger-100 text-danger-700 px-4 py-2 rounded-lg text-sm mb-4">
                  {onboardError}
                </div>
              )}
              {onboardSuccess && (
                <div className="bg-success-50 border border-success-100 text-success-700 px-4 py-2 rounded-lg text-sm mb-4">
                  {onboardSuccess}
                </div>
              )}

              {!onboardSuccess && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">School Name</label>
                      <input
                        type="text"
                        value={onboardForm.school_name}
                        onChange={(e) => setOnboardForm({ ...onboardForm, school_name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">School Email</label>
                      <input
                        type="email"
                        value={onboardForm.school_email}
                        onChange={(e) => setOnboardForm({ ...onboardForm, school_email: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">School Phone</label>
                      <input
                        type="text"
                        value={onboardForm.school_phone}
                        onChange={(e) => setOnboardForm({ ...onboardForm, school_phone: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">School Address</label>
                      <input
                        type="text"
                        value={onboardForm.school_address}
                        onChange={(e) => setOnboardForm({ ...onboardForm, school_address: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                    </div>
                  </div>

                  <hr className="border-gray-200" />

                  <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Admin Full Name</label>
                      <input
                        type="text"
                        value={onboardForm.admin_name}
                        onChange={(e) => setOnboardForm({ ...onboardForm, admin_name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Admin Email</label>
                      <input
                        type="email"
                        value={onboardForm.admin_email}
                        onChange={(e) => setOnboardForm({ ...onboardForm, admin_email: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Admin Password</label>
                      <PasswordInput
                        value={onboardForm.admin_password}
                        onChange={(e) => setOnboardForm({ ...onboardForm, admin_password: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                    </div>
                  </div>

                  <hr className="border-gray-200" />

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
                      <select
                        value={onboardForm.subscription_plan_id}
                        onChange={(e) => setOnboardForm({ ...onboardForm, subscription_plan_id: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      >
                        {plans.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                      <select
                        value={onboardForm.subscription_status}
                        onChange={(e) => setOnboardForm({ ...onboardForm, subscription_status: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      >
                        <option value="trial">Trial</option>
                        <option value="active">Active</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-3 mt-6">
                <Button variant="secondary" onClick={() => setShowOnboardModal(false)} disabled={saving}>
                  {onboardSuccess ? 'Close' : 'Cancel'}
                </Button>
                {!onboardSuccess && (
                  <Button
                    onClick={handleOnboard}
                    disabled={saving || !onboardForm.school_name || !onboardForm.school_email || !onboardForm.admin_name || !onboardForm.admin_email || !onboardForm.admin_password}
                  >
                    {saving ? 'Creating...' : 'Create School'}
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </SystemAdminLayout>
  );
}
