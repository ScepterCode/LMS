'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface Guardian {
  id?: string;
  guardian_type: string;
  title?: string;
  first_name: string;
  last_name: string;
  relationship: string;
  phone: string;
  email?: string;
  occupation?: string;
  address?: string;
  is_emergency_contact: boolean;
  is_primary: boolean;
}

interface RegisteredParent {
  id: string;
  full_name: string;
  email: string;
  phone: string;
}

interface GuardianModalProps {
  studentId: string;
  guardian?: Guardian | null;
  onClose: () => void;
  onSuccess: () => void;
}

export default function GuardianModal({ studentId, guardian, onClose, onSuccess }: GuardianModalProps) {
  const isEdit = !!guardian;
  // Editing an existing free-text contact always uses the plain form;
  // adding new defaults to linking an already-registered parent, since
  // that's what actually grants the parent dashboard access - typing
  // fresh contact details here previously created a disconnected record
  // with no login, even when the parent already had an account.
  const [mode, setMode] = useState<'link' | 'new'>(isEdit ? 'new' : 'link');

  const [parents, setParents] = useState<RegisteredParent[]>([]);
  const [loadingParents, setLoadingParents] = useState(true);
  const [parentSearch, setParentSearch] = useState('');
  const [selectedParentId, setSelectedParentId] = useState('');
  const [linkRelationship, setLinkRelationship] = useState('Father');
  const [linkIsPrimary, setLinkIsPrimary] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState<Guardian>(guardian || {
    guardian_type: 'father',
    title: 'Mr',
    first_name: '',
    last_name: '',
    relationship: 'Father',
    phone: '',
    email: '',
    occupation: '',
    address: '',
    is_emergency_contact: true,
    is_primary: false,
  });

  useEffect(() => {
    if (mode === 'link' && parents.length === 0) {
      loadParents();
    }
  }, [mode]);

  const loadParents = async () => {
    setLoadingParents(true);
    const res = await api.getParents({ limit: 1000 });
    if (res.data) setParents(res.data as RegisteredParent[]);
    setLoadingParents(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;

    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleLinkSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    const response = await api.linkParentToStudent(selectedParentId, {
      student_id: studentId,
      relationship: linkRelationship,
      is_primary: linkIsPrimary,
    });

    if (response.error) {
      setError(response.error);
    } else {
      onSuccess();
      onClose();
    }
    setSubmitting(false);
  };

  const handleNewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const payload = {
        ...formData,
        email: formData.email || undefined,
        occupation: formData.occupation || undefined,
        address: formData.address || undefined,
      };
      const response = isEdit
        ? await api.updateGuardian(studentId, guardian!.id!, payload)
        : await api.addGuardian(studentId, payload);

      if (response.error) {
        setError(response.error);
        return;
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(`Failed to ${isEdit ? 'update' : 'add'} guardian`);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredParents = parents.filter((p) =>
    p.full_name.toLowerCase().includes(parentSearch.toLowerCase()) ||
    p.email.toLowerCase().includes(parentSearch.toLowerCase())
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4">
          <h3 className="text-lg font-semibold">
            {isEdit ? 'Edit Emergency Contact' : 'Add Guardian'}
          </h3>
        </div>

        {!isEdit && (
          <div className="flex border-b">
            <button
              type="button"
              onClick={() => setMode('link')}
              className={`flex-1 py-3 text-sm font-medium ${mode === 'link' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Link Registered Parent
            </button>
            <button
              type="button"
              onClick={() => setMode('new')}
              className={`flex-1 py-3 text-sm font-medium ${mode === 'new' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Add Contact Without Login
            </button>
          </div>
        )}

        {mode === 'link' && !isEdit ? (
          <form onSubmit={handleLinkSubmit} className="p-6 space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <p className="text-sm text-gray-600">
              This links an already-registered parent account, so they get dashboard access to this student's grades, report cards, and attendance.
            </p>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search Parent</label>
              <input
                type="text"
                value={parentSearch}
                onChange={(e) => setParentSearch(e.target.value)}
                placeholder="Search by name or email..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 mb-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Parent *</label>
              {loadingParents ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                </div>
              ) : (
                <div className="border border-gray-300 rounded-lg max-h-64 overflow-y-auto">
                  {filteredParents.length === 0 ? (
                    <div className="p-4 text-center text-gray-500">
                      {parentSearch ? 'No parents found matching your search' : 'No registered parents yet - add one under Parents/Guardians'}
                    </div>
                  ) : (
                    <div className="divide-y">
                      {filteredParents.map((parent) => (
                        <label
                          key={parent.id}
                          className={`flex items-center p-3 hover:bg-gray-50 cursor-pointer ${
                            selectedParentId === parent.id ? 'bg-blue-50' : ''
                          }`}
                        >
                          <input
                            type="radio"
                            name="parent_id"
                            value={parent.id}
                            checked={selectedParentId === parent.id}
                            onChange={(e) => setSelectedParentId(e.target.value)}
                            required
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                          />
                          <div className="ml-3 flex-1">
                            <p className="text-sm font-medium text-gray-900">{parent.full_name}</p>
                            <p className="text-xs text-gray-500">{parent.email}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Relationship *</label>
              <select
                value={linkRelationship}
                onChange={(e) => setLinkRelationship(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="Father">Father</option>
                <option value="Mother">Mother</option>
                <option value="Guardian">Guardian</option>
                <option value="Uncle">Uncle</option>
                <option value="Aunt">Aunt</option>
                <option value="Grandfather">Grandfather</option>
                <option value="Grandmother">Grandmother</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="link_is_primary"
                checked={linkIsPrimary}
                onChange={(e) => setLinkIsPrimary(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="link_is_primary" className="ml-2 block text-sm text-gray-700">
                Set as primary guardian for this student
              </label>
            </div>

            <div className="flex gap-3 pt-4 border-t">
              <button
                type="submit"
                disabled={submitting || !selectedParentId}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {submitting ? 'Linking...' : 'Link Parent'}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={submitting}
                className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleNewSubmit} className="p-6 space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            {!isEdit && (
              <p className="text-sm text-gray-600">
                Use this only for a contact who doesn't have (or doesn't need) a login of their own - they won't get dashboard access. For a parent who already has an account, use "Link Registered Parent" instead.
              </p>
            )}

            {/* Guardian Type & Title */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Guardian Type *
                </label>
                <select
                  name="guardian_type"
                  value={formData.guardian_type}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="father">Father</option>
                  <option value="mother">Mother</option>
                  <option value="guardian">Guardian</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title
                </label>
                <select
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Mr">Mr</option>
                  <option value="Mrs">Mrs</option>
                  <option value="Ms">Ms</option>
                  <option value="Dr">Dr</option>
                  <option value="Prof">Prof</option>
                  <option value="Chief">Chief</option>
                  <option value="Alhaji">Alhaji</option>
                  <option value="Alhaja">Alhaja</option>
                </select>
              </div>
            </div>

            {/* Name */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name *
                </label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name *
                </label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Relationship */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Relationship *
              </label>
              <input
                type="text"
                name="relationship"
                value={formData.relationship}
                onChange={handleChange}
                required
                placeholder="e.g., Father, Mother, Uncle, Aunt"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Contact */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone *
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  required
                  placeholder="+234 800 000 0000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="email@example.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Occupation */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Occupation
              </label>
              <input
                type="text"
                name="occupation"
                value={formData.occupation}
                onChange={handleChange}
                placeholder="e.g., Accountant, Teacher"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Address */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Address
              </label>
              <textarea
                name="address"
                value={formData.address}
                onChange={handleChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Checkboxes */}
            <div className="space-y-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_emergency_contact"
                  name="is_emergency_contact"
                  checked={formData.is_emergency_contact}
                  onChange={handleChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is_emergency_contact" className="ml-2 block text-sm text-gray-700">
                  Emergency Contact
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_primary"
                  name="is_primary"
                  checked={formData.is_primary}
                  onChange={handleChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is_primary" className="ml-2 block text-sm text-gray-700">
                  Primary Guardian
                </label>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t">
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {submitting ? (isEdit ? 'Updating...' : 'Adding...') : (isEdit ? 'Update Guardian' : 'Add Guardian')}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
