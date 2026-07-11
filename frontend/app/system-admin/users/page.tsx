'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import SystemAdminLayout from '@/components/SystemAdminLayout';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatCard } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

interface PlatformUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  school_id: string | null;
  is_active: boolean;
  created_at: string;
}

interface OrgLite {
  id: string;
  name: string;
}

const ROLE_OPTIONS = ['admin', 'teacher', 'bursar', 'parent', 'student', 'system_admin'];

export default function SystemAdminUsersPage() {
  const [users, setUsers] = useState<PlatformUser[]>([]);
  const [orgMap, setOrgMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [error, setError] = useState('');
  const [confirmTarget, setConfirmTarget] = useState<PlatformUser | null>(null);
  const [processing, setProcessing] = useState(false);
  const [impersonating, setImpersonating] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [roleFilter]);

  const loadData = async () => {
    setLoading(true);
    setError('');
    const [usersRes, orgsRes] = await Promise.all([
      api.getSystemAdminUsers({ limit: 500, role: roleFilter || undefined }),
      api.getOrganizations({ limit: 500 }),
    ]);

    if (usersRes.error) {
      setError(usersRes.error);
    } else if (usersRes.data) {
      setUsers((usersRes.data as any).users ?? []);
    }

    if (orgsRes.data) {
      const orgs: OrgLite[] = (orgsRes.data as any).organizations ?? [];
      const map: Record<string, string> = {};
      orgs.forEach((org) => { map[org.id] = org.name; });
      setOrgMap(map);
    }

    setLoading(false);
  };

  const filtered = useMemo(() => {
    return users.filter((u) =>
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      (u.school_id && (orgMap[u.school_id] ?? '').toLowerCase().includes(search.toLowerCase()))
    );
  }, [users, search, orgMap]);

  const handleToggleActive = (user: PlatformUser) => {
    setConfirmTarget(user);
  };

  const confirmToggle = async () => {
    if (!confirmTarget) return;
    setProcessing(true);
    const res = confirmTarget.is_active
      ? await api.deactivateUser(confirmTarget.id)
      : await api.updateUser(confirmTarget.id, { is_active: true });

    if (res.error) {
      setError(res.error);
    } else {
      setUsers((prev) =>
        prev.map((u) => (u.id === confirmTarget.id ? { ...u, is_active: !confirmTarget.is_active } : u))
      );
    }
    setProcessing(false);
    setConfirmTarget(null);
  };

  const roleTone = (role: string) => {
    if (role === 'system_admin') return 'brand';
    if (role === 'admin') return 'info';
    return undefined;
  };

  const handleImpersonate = async (user: PlatformUser) => {
    setImpersonating(user.id);
    setError('');
    const res = await api.startImpersonation(user.id);
    if (res.error) {
      setError(res.error);
      setImpersonating(null);
      return;
    }
    // Full reload: impersonation swaps role/school_id entirely, so every
    // cached page state (this one included) needs to reset from scratch.
    window.location.href = '/dashboard';
  };

  return (
    <SystemAdminLayout>
      <div className="space-y-6">
        <PageHeader title="Users" subtitle="Every user account across every school" />

        {error && (
          <div className="bg-danger-50 border border-danger-100 text-danger-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="grid sm:grid-cols-3 gap-4">
          <StatCard label="Total Users" value={users.length} />
          <StatCard label="Active" value={users.filter((u) => u.is_active).length} />
          <StatCard label="Deactivated" value={users.filter((u) => !u.is_active).length} />
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Name, email, or school..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              >
                <option value="">All Roles</option>
                {ROLE_OPTIONS.map((role) => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">School</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">Loading...</td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">No users found</td>
                  </tr>
                ) : (
                  filtered.map((u) => (
                    <tr key={u.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{u.full_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{u.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge tone={roleTone(u.role)}>{u.role}</Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {u.school_id ? (orgMap[u.school_id] ?? u.school_id) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge tone={u.is_active ? 'success' : 'neutral'}>{u.is_active ? 'active' : 'inactive'}</Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right space-x-2">
                        {u.role !== 'system_admin' && u.is_active && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleImpersonate(u)}
                            disabled={impersonating === u.id}
                          >
                            {impersonating === u.id ? 'Starting...' : 'Impersonate'}
                          </Button>
                        )}
                        {u.role !== 'system_admin' && (
                          <Button
                            variant={u.is_active ? 'danger' : 'secondary'}
                            size="sm"
                            onClick={() => handleToggleActive(u)}
                          >
                            {u.is_active ? 'Deactivate' : 'Reactivate'}
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {confirmTarget && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {confirmTarget.is_active ? 'Deactivate user?' : 'Reactivate user?'}
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                {confirmTarget.is_active
                  ? <>This will prevent <strong>{confirmTarget.full_name}</strong> ({confirmTarget.email}) from logging in.</>
                  : <>This will restore login access for <strong>{confirmTarget.full_name}</strong> ({confirmTarget.email}).</>}
              </p>
              <div className="flex justify-end gap-3">
                <Button variant="secondary" onClick={() => setConfirmTarget(null)} disabled={processing}>
                  Cancel
                </Button>
                <Button
                  variant={confirmTarget.is_active ? 'danger' : 'primary'}
                  onClick={confirmToggle}
                  disabled={processing}
                >
                  {processing ? 'Working...' : 'Confirm'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </SystemAdminLayout>
  );
}
