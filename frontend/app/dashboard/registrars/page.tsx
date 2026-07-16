'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';

interface RegistrarUser {
  id: string;
  full_name: string;
  email: string;
  phone?: string;
  is_active: boolean;
  created_at: string;
}

export default function RegistrarsPage() {
  const [registrars, setRegistrars] = useState<RegistrarUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadRegistrars();
  }, []);

  const loadRegistrars = async () => {
    setLoading(true);
    setError('');
    const response = await api.getUsers({ role: 'registrar', limit: 100 });
    if (response.error) {
      setError(response.error);
      setRegistrars([]);
    } else {
      setRegistrars(response.data ? (response.data as RegistrarUser[]) : []);
    }
    setLoading(false);
  };

  const handleDeactivate = async (id: string, name: string) => {
    if (!window.confirm(`Deactivate registrar account "${name}"? They will no longer be able to log in.`)) return;
    const response = await api.deactivateUser(id);
    if (response.error) {
      alert(response.error);
    } else {
      loadRegistrars();
    }
  };

  return (
    <DashboardLayout>
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Registrars</h2>
          <p className="text-gray-600">Manage front desk staff who handle admissions and enrollment</p>
        </div>
        <Link
          href="/dashboard/registrars/add"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Add Registrar
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
      ) : registrars.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <h3 className="text-sm font-medium text-gray-900">No registrars found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Add a registrar account to delegate admissions intake and enrollment records.
          </p>
          <div className="mt-6">
            <Link
              href="/dashboard/registrars/add"
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              + Add Registrar
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
              {registrars.map((registrar) => (
                <tr key={registrar.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{registrar.full_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{registrar.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{registrar.phone || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${registrar.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {registrar.is_active ? 'active' : 'inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {registrar.is_active && (
                      <button onClick={() => handleDeactivate(registrar.id, registrar.full_name)} className="text-red-600 hover:text-red-900">
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
