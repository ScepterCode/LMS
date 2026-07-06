'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface Organization {
  id: string;
  name: string;
  address?: string;
  phone?: string;
  motto?: string;
  logo_url?: string;
}

export default function SchoolSettingsPage() {
  const { user } = useAuth();
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [formData, setFormData] = useState({ name: '', address: '', phone: '', motto: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (user?.school_id) {
      fetchOrganization();
    }
  }, [user?.school_id]);

  const fetchOrganization = async () => {
    setLoading(true);
    try {
      const response = await api.getOrganization(user!.school_id!);
      const org = (response.data as any)?.organization as Organization | undefined;
      if (org) {
        setOrganization(org);
        setFormData({
          name: org.name || '',
          address: org.address || '',
          phone: org.phone || '',
          motto: org.motto || '',
        });
      }
    } catch (err) {
      console.error('Error fetching organization:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!user?.school_id) return;

    setSaving(true);
    try {
      const response = await api.updateOrganization(user.school_id, formData);
      if (response.error) {
        setError(response.error);
        return;
      }
      setSuccess('School details saved successfully!');
      fetchOrganization();
    } catch {
      setError('Failed to save school details');
    } finally {
      setSaving(false);
    }
  };

  const handleLogoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user?.school_id) return;

    setError('');
    setSuccess('');
    setUploadingLogo(true);
    try {
      const response = await api.uploadOrganizationLogo(user.school_id, file);
      if (response.error) {
        setError(response.error);
        return;
      }
      setSuccess('Logo uploaded successfully!');
      fetchOrganization();
    } catch {
      setError('Failed to upload logo');
    } finally {
      setUploadingLogo(false);
      e.target.value = '';
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading school settings...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-3xl">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">School Settings</h1>
          <p className="text-gray-600 mt-1">Manage your school's branding for report cards and documents</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{error}</div>
        )}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">{success}</div>
        )}

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">School Logo</h2>
          <div className="flex items-center gap-6">
            <div className="w-24 h-24 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center overflow-hidden bg-gray-50">
              {organization?.logo_url ? (
                <img src={organization.logo_url} alt="School logo" className="w-full h-full object-contain" />
              ) : (
                <span className="text-xs text-gray-400 text-center px-2">No logo yet</span>
              )}
            </div>
            <div>
              <label className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer disabled:opacity-50">
                {uploadingLogo ? 'Uploading...' : 'Upload Logo'}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={handleLogoChange}
                  disabled={uploadingLogo}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-gray-500 mt-2">PNG, JPEG, or WebP. Max 2MB.</p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">School Details</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">School Name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Motto</label>
            <input
              type="text"
              name="motto"
              value={formData.motto}
              onChange={handleChange}
              placeholder="e.g., Knowledge is Power"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <textarea
              name="address"
              value={formData.address}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="pt-2">
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
}
