'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';

interface BursarUser {
  id: string;
  full_name: string;
  email: string;
  phone?: string;
  is_active: boolean;
  created_at: string;
}

export default function BursarsPage() {
  const [bursars, setBursars] = useState<BursarUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadBursars();
  }, []);

  const loadBursars = async () => {
    setLoading(true);
    setError('');
    const response = await api.getUsers({ role: 'bursar', limit: 100 });
    if (response.error) {
      setError(response.error);
      setBursars([]);
    } else {
      setBursars(response.data ? (response.data as BursarUser[]) : []);
    }
    setLoading(false);
  };

  const handleDeactivate = async (id: string, name: string) => {
    if (!window.confirm(`Deactivate bursar account "${name}"? They will no longer be able to log in.`)) return;
    const response = await api.deactivateUser(id);
    if (response.error) {
      alert(response.error);
    } else {
      loadBursars();
    }
  };

  return (
    <DashboardLayout>
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Bursars</h2>
          <p className="text-gray-600">Manage staff who handle school finances</p>
        </div>
        <Link
          href="/dashboard/bursars/add"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Add Bursar
        </Link>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : bursars.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <h3 className="text-sm font-medium text-gray-900">No bursars found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Add a bursar account to let them manage fees, payments, and financial reports.
          </p>
          <div className="mt-6">
            <Link
              href="/dashboard/bursars/add"
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              + Add Bursar
            </Link>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {bursars.map((bursar) => (
                <tr key={bursar.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{bursar.full_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{bursar.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{bursar.phone || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${bursar.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {bursar.is_active ? 'active' : 'inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {bursar.is_active && (
                      <button onClick={() => handleDeactivate(bursar.id, bursar.full_name)} className="text-red-600 hover:text-red-900">
                        Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </DashboardLayout>
  );
}
