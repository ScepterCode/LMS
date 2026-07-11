'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';

// Renders nothing unless a system admin is currently impersonating this
// session (user.is_impersonating), so this is a no-op for every normal
// session - the only touch this feature makes to the shared DashboardLayout.
export default function ImpersonationBanner() {
  const { user } = useAuth();
  const [exiting, setExiting] = useState(false);

  if (!user?.is_impersonating) return null;

  const handleExit = async () => {
    setExiting(true);
    await api.exitImpersonation();
    // Full reload rather than client-side navigation: impersonation swaps
    // role/school_id entirely, so every cached page state needs to reset.
    window.location.href = '/system-admin';
  };

  return (
    <div className="bg-amber-500 text-amber-950 px-4 py-2 flex items-center justify-between gap-4 text-sm font-medium sticky top-0 z-20">
      <span>
        Viewing as <strong>{user.full_name}</strong> ({user.email})
        {user.impersonated_by && <> &mdash; impersonated by {user.impersonated_by.name}</>}
      </span>
      <button
        onClick={handleExit}
        disabled={exiting}
        className="bg-amber-950 text-amber-50 px-3 py-1 rounded-lg hover:bg-amber-900 disabled:opacity-60 transition-colors"
      >
        {exiting ? 'Exiting...' : 'Exit Impersonation'}
      </button>
    </div>
  );
}
