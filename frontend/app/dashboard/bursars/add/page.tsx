'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { PasswordInput } from '@/components/ui/PasswordInput';

export default function AddBursarPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    password: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    const response = await api.createUser({
      email: formData.email,
      password: formData.password,
      full_name: formData.full_name,
      role: 'bursar',
      phone: formData.phone || undefined,
    });

    if (response.error) {
      setError(response.error);
      setSubmitting(false);
    } else {
      router.push('/dashboard/bursars');
    }
  };

  return (
    <DashboardLayout>
      <div className="mb-6">
        <Link href="/dashboard/bursars" className="text-blue-600 hover:text-blue-800 text-sm mb-4 inline-block">
          ← Back to Bursars
        </Link>
        <h2 className="text-2xl font-bold text-gray-900">Add New Bursar</h2>
        <p className="text-gray-600 mt-1">
          Create an account with access to fees, payments, and financial reports
        </p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6 max-w-2xl">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Full Name *
          </label>
          <input
            type="text"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email *
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="bursar@example.com"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">This will be the login email</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone
            </label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="+234 800 000 0000"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="border-t pt-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Password *
          </label>
          <PasswordInput
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            minLength={8}
            placeholder="Minimum 8 characters"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            showRequirements
          />
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Bursar access</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Manage fee categories, structures, and student fee assignments</li>
            <li>• Record payments and view financial reports</li>
            <li>• Does not have access to student records, grading, or attendance</li>
          </ul>
        </div>

        <div className="flex gap-4 pt-4">
          <button
            type="submit"
            disabled={submitting}
            className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {submitting ? 'Creating Account...' : 'Create Bursar Account'}
          </button>
          <Link
            href="/dashboard/bursars"
            className="px-8 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 text-center"
          >
            Cancel
          </Link>
        </div>
      </form>
    </DashboardLayout>
  );
}
