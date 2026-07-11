'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import SystemAdminLayout from '@/components/SystemAdminLayout';
import { PageHeader } from '@/components/ui/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

interface AuditLog {
  id: string;
  actor_user_id: string | null;
  actor_email: string | null;
  actor_role: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  target_organization_id: string | null;
  details: Record<string, any>;
  created_at: string;
}

const PAGE_SIZE = 50;

function actionTone(action: string) {
  if (action.includes('suspended') || action.includes('deactivated') || action.includes('cancelled')) return 'danger';
  if (action.includes('created') || action.includes('started')) return 'success';
  if (action.includes('ended') || action.includes('updated') || action.includes('changed')) return 'info';
  return 'neutral';
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, [skip]);

  const loadLogs = async () => {
    setLoading(true);
    const res = await api.getAuditLogs({ skip, limit: PAGE_SIZE });
    if (res.data) {
      const data = res.data as any;
      setLogs(data.logs ?? []);
      setTotal(data.total ?? 0);
    }
    setLoading(false);
  };

  return (
    <SystemAdminLayout>
      <div className="space-y-6">
        <PageHeader title="Audit Log" subtitle="Every action taken by system admins across the platform" />

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">When</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actor</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Target</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Details</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">Loading...</td>
                  </tr>
                ) : logs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">No audit events yet</td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50 align-top">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.actor_email ?? '-'}
                        {log.actor_role && <div className="text-xs text-gray-400">{log.actor_role}</div>}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge tone={actionTone(log.action)}>{log.action}</Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {log.target_type ? `${log.target_type}${log.target_id ? ` (${log.target_id.slice(0, 8)}...)` : ''}` : '-'}
                      </td>
                      <td className="px-6 py-4 text-xs text-gray-500 max-w-xs">
                        {Object.keys(log.details || {}).length > 0 ? (
                          <pre className="whitespace-pre-wrap break-words">{JSON.stringify(log.details)}</pre>
                        ) : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {total > PAGE_SIZE && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">
              Showing {skip + 1}-{Math.min(skip + PAGE_SIZE, total)} of {total}
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={skip === 0}
                onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={skip + PAGE_SIZE >= total}
                onClick={() => setSkip(skip + PAGE_SIZE)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>
    </SystemAdminLayout>
  );
}
