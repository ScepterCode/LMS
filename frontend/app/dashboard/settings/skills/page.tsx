'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';

interface SkillCategory {
  id: string;
  name: string;
  domain: 'psychomotor' | 'affective';
  display_order: number;
  is_active: boolean;
}

export default function SkillsSettingsPage() {
  const [categories, setCategories] = useState<SkillCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newName, setNewName] = useState('');
  const [newDomain, setNewDomain] = useState<'psychomotor' | 'affective'>('psychomotor');
  const [adding, setAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    setLoading(true);
    try {
      const response = await api.getSkillCategories(true);
      setCategories(response.data ? (response.data as SkillCategory[]) : []);
    } catch (err) {
      console.error('Error fetching skill categories:', err);
      setCategories([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    setError('');
    setAdding(true);
    try {
      const response = await api.createSkillCategory({ name: newName.trim(), domain: newDomain });
      if (response.error) {
        setError(response.error);
        return;
      }
      setNewName('');
      fetchCategories();
    } catch {
      setError('Failed to add skill category');
    } finally {
      setAdding(false);
    }
  };

  const handleToggleActive = async (category: SkillCategory) => {
    setError('');
    const response = await api.updateSkillCategory(category.id, { is_active: !category.is_active });
    if (response.error) {
      setError(response.error);
      return;
    }
    fetchCategories();
  };

  const startEditing = (category: SkillCategory) => {
    setEditingId(category.id);
    setEditingName(category.name);
  };

  const saveEdit = async (categoryId: string) => {
    if (!editingName.trim()) return;
    setError('');
    const response = await api.updateSkillCategory(categoryId, { name: editingName.trim() });
    if (response.error) {
      setError(response.error);
      return;
    }
    setEditingId(null);
    fetchCategories();
  };

  const renderGroup = (domain: 'psychomotor' | 'affective', label: string) => {
    const items = categories.filter((c) => c.domain === domain);
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{label} Domain</h2>
        {items.length === 0 ? (
          <p className="text-sm text-gray-500">No traits yet.</p>
        ) : (
          <ul className="divide-y divide-gray-200">
            {items.map((category) => (
              <li key={category.id} className="py-3 flex items-center justify-between gap-4">
                {editingId === category.id ? (
                  <input
                    type="text"
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    className="flex-1 px-2 py-1 border border-gray-300 rounded"
                    autoFocus
                  />
                ) : (
                  <span className={category.is_active ? 'text-gray-900' : 'text-gray-400 line-through'}>
                    {category.name}
                  </span>
                )}
                <div className="flex items-center gap-3 text-sm">
                  {editingId === category.id ? (
                    <>
                      <button onClick={() => saveEdit(category.id)} className="text-blue-600 hover:text-blue-800">
                        Save
                      </button>
                      <button onClick={() => setEditingId(null)} className="text-gray-500 hover:text-gray-700">
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button onClick={() => startEditing(category)} className="text-blue-600 hover:text-blue-800">
                        Edit
                      </button>
                      <button
                        onClick={() => handleToggleActive(category)}
                        className={category.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'}
                      >
                        {category.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-3xl">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Report Card Skills</h1>
          <p className="text-gray-600 mt-1">
            Configure the psychomotor and affective domain traits (sports, handling of tools,
            punctuality, etc.) that form teachers rate on each student's report card
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{error}</div>
        )}

        <form onSubmit={handleAdd} className="bg-white rounded-lg shadow p-6 flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Trait Name</label>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="e.g., Sports & Games"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Domain</label>
            <select
              value={newDomain}
              onChange={(e) => setNewDomain(e.target.value as 'psychomotor' | 'affective')}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="psychomotor">Psychomotor</option>
              <option value="affective">Affective</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={adding || !newName.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {adding ? 'Adding...' : '+ Add Trait'}
          </button>
        </form>

        {loading ? (
          <div className="text-center text-gray-500 py-12">Loading skill traits...</div>
        ) : (
          <>
            {renderGroup('psychomotor', 'Psychomotor')}
            {renderGroup('affective', 'Affective')}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
