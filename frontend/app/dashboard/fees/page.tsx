'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

interface FeeCategory {
  id: string;
  name: string;
  code: string;
  description?: string;
  is_mandatory: boolean;
  is_active: boolean;
}

interface FeeStructure {
  id: string;
  category_name: string;
  class_name?: string;
  class_level?: string;
  amount: number;
  payment_frequency: string;
  due_date?: string;
  is_active: boolean;
}

interface Session {
  id: string;
  name: string;
  is_current?: boolean;
}

interface Class {
  id: string;
  name: string;
}

export default function FeeManagementPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'categories' | 'structures'>('categories');
  const [categories, setCategories] = useState<FeeCategory[]>([]);
  const [structures, setStructures] = useState<FeeStructure[]>([]);
  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<FeeCategory | null>(null);
  const [editCategoryForm, setEditCategoryForm] = useState({
    name: '',
    description: '',
    is_mandatory: true,
    is_active: true,
  });
  const [showStructureModal, setShowStructureModal] = useState(false);

  const [categoryForm, setCategoryForm] = useState({
    name: '',
    code: '',
    description: '',
    is_mandatory: true
  });

  const [structureForm, setStructureForm] = useState({
    fee_category_id: '',
    session_id: '',
    class_id: '',
    class_level: '',
    amount: '',
    payment_frequency: 'termly',
    due_date: '',
  });

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  useEffect(() => {
    // Dropdown data for the Create Fee Structure form - fetched once,
    // independent of which tab is active.
    const loadDropdownData = async () => {
      const [categoriesRes, sessionsRes, classesRes] = await Promise.all([
        api.get('/api/v1/fees/categories'),
        api.get('/api/v1/sessions'),
        api.get('/api/v1/classes'),
      ]);
      if (categoriesRes.data) setCategories(categoriesRes.data as FeeCategory[]);
      if (sessionsRes.data) {
        const sessionData = sessionsRes.data as Session[];
        setSessions(sessionData);
        const current = sessionData.find((s) => s.is_current);
        if (current) {
          setStructureForm((prev) => ({ ...prev, session_id: current.id }));
        }
      }
      if (classesRes.data) setClasses(classesRes.data as Class[]);
    };
    loadDropdownData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'categories') {
        const response = await api.get('/api/v1/fees/categories');
        setCategories(response.data ? (response.data as FeeCategory[]) : []);
      } else {
        const response = await api.get('/api/v1/fees/structures');
        setStructures(response.data ? (response.data as FeeStructure[]) : []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      if (activeTab === 'categories') {
        setCategories([]);
      } else {
        setStructures([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/api/v1/fees/categories', categoryForm);
      alert('Fee category created successfully!');
      setShowCategoryModal(false);
      setCategoryForm({ name: '', code: '', description: '', is_mandatory: true });
      fetchData();
    } catch (error: any) {
      console.error('Error creating category:', error);
      alert(error.response?.data?.detail || 'Failed to create category');
    }
  };

  const openEditCategory = (category: FeeCategory) => {
    setEditingCategory(category);
    setEditCategoryForm({
      name: category.name,
      description: category.description || '',
      is_mandatory: category.is_mandatory,
      is_active: category.is_active,
    });
  };

  const handleUpdateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCategory) return;
    try {
      const response = await api.put(`/api/v1/fees/categories/${editingCategory.id}`, editCategoryForm);
      if (response.error) {
        alert(response.error);
        return;
      }
      setEditingCategory(null);
      fetchData();
    } catch (error: any) {
      console.error('Error updating category:', error);
      alert(error.response?.data?.detail || 'Failed to update category');
    }
  };

  const handleDeleteCategory = async (category: FeeCategory) => {
    if (!confirm(`Delete fee category "${category.name}"? This can't be undone.`)) return;
    try {
      const response = await api.delete(`/api/v1/fees/categories/${category.id}`);
      if (response.error) {
        alert(response.error);
        return;
      }
      fetchData();
    } catch (error: any) {
      console.error('Error deleting category:', error);
      alert(error.response?.data?.detail || 'Failed to delete category');
    }
  };

  const handleDeleteStructure = async (structure: FeeStructure) => {
    if (!confirm(`Delete this fee structure (${structure.category_name})? This can't be undone.`)) return;
    try {
      const response = await api.delete(`/api/v1/fees/structures/${structure.id}`);
      if (response.error) {
        alert(response.error);
        return;
      }
      fetchData();
    } catch (error: any) {
      console.error('Error deleting fee structure:', error);
      alert(error.response?.data?.detail || 'Failed to delete fee structure');
    }
  };

  const handleCreateStructure = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.post('/api/v1/fees/structures', {
        fee_category_id: structureForm.fee_category_id,
        session_id: structureForm.session_id,
        class_id: structureForm.class_id || null,
        class_level: structureForm.class_level || null,
        amount: parseFloat(structureForm.amount),
        payment_frequency: structureForm.payment_frequency,
        due_date: structureForm.due_date || null,
      });
      if (response.error) {
        alert(response.error);
        return;
      }
      alert('Fee structure created successfully!');
      setShowStructureModal(false);
      setStructureForm({
        fee_category_id: '',
        session_id: structureForm.session_id,
        class_id: '',
        class_level: '',
        amount: '',
        payment_frequency: 'termly',
        due_date: '',
      });
      fetchData();
    } catch (error: any) {
      console.error('Error creating fee structure:', error);
      alert(error.response?.data?.detail || 'Failed to create fee structure');
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <PageHeader
          title="Fee Management"
          subtitle="Manage fee categories and structures"
          actions={<Button onClick={() => router.push('/dashboard/fees/payments')}>Record Payment</Button>}
        />

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('categories')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'categories'
                  ? 'border-brand-500 text-brand-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Fee Categories
            </button>
            <button
              onClick={() => setActiveTab('structures')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'structures'
                  ? 'border-brand-500 text-brand-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Fee Structures
            </button>
          </nav>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
          </div>
        ) : activeTab === 'categories' ? (
          <div className="space-y-4">
            <div className="flex justify-end">
              <Button onClick={() => setShowCategoryModal(true)}>Add Category</Button>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mandatory</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {categories.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                        No fee categories found. Create your first category to get started.
                      </td>
                    </tr>
                  ) : (
                    categories.map((category) => (
                      <tr key={category.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {category.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {category.code}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {category.is_mandatory ? (
                            <span className="text-success-600">Yes</span>
                          ) : (
                            <span className="text-gray-400">No</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge tone={category.is_active ? 'success' : 'neutral'}>
                            {category.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
                          <button
                            onClick={() => openEditCategory(category)}
                            className="text-brand-600 hover:text-brand-800"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteCategory(category)}
                            className="text-danger-600 hover:text-danger-800"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-end">
              <Button onClick={() => setShowStructureModal(true)}>Add Fee Structure</Button>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Class</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Frequency</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Due Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {structures.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                        No fee structures found. Create fee structures to assign to students.
                      </td>
                    </tr>
                  ) : (
                    structures.map((structure) => (
                      <tr key={structure.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {structure.category_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {structure.class_name || (structure.class_level ? `All ${structure.class_level} Classes` : 'All Classes')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          ₦{Number(structure.amount).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {structure.payment_frequency}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {structure.due_date || 'Not set'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge tone={structure.is_active ? 'success' : 'neutral'}>
                            {structure.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => handleDeleteStructure(structure)}
                            className="text-danger-600 hover:text-danger-800"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Category Modal */}
      {showCategoryModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4 text-gray-900">Create Fee Category</h2>

            <form onSubmit={handleCreateCategory} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  type="text"
                  required
                  value={categoryForm.name}
                  onChange={(e) => setCategoryForm({...categoryForm, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  placeholder="e.g., Tuition Fee"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Code *</label>
                <input
                  type="text"
                  required
                  value={categoryForm.code}
                  onChange={(e) => setCategoryForm({...categoryForm, code: e.target.value.toUpperCase()})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  placeholder="e.g., TUITION"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={categoryForm.description}
                  onChange={(e) => setCategoryForm({...categoryForm, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  rows={3}
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={categoryForm.is_mandatory}
                  onChange={(e) => setCategoryForm({...categoryForm, is_mandatory: e.target.checked})}
                  className="w-4 h-4 text-brand-600 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700">Mandatory fee</label>
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="flex-1">Create Category</Button>
                <Button type="button" variant="secondary" className="flex-1" onClick={() => setShowCategoryModal(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Fee Category Modal */}
      {editingCategory && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-1 text-gray-900">Edit Fee Category</h2>
            <p className="text-sm text-gray-500 mb-4">Code: {editingCategory.code} (can't be changed)</p>

            <form onSubmit={handleUpdateCategory} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  type="text"
                  required
                  value={editCategoryForm.name}
                  onChange={(e) => setEditCategoryForm({ ...editCategoryForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={editCategoryForm.description}
                  onChange={(e) => setEditCategoryForm({ ...editCategoryForm, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  rows={3}
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={editCategoryForm.is_mandatory}
                  onChange={(e) => setEditCategoryForm({ ...editCategoryForm, is_mandatory: e.target.checked })}
                  className="w-4 h-4 text-brand-600 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700">Mandatory fee</label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={editCategoryForm.is_active}
                  onChange={(e) => setEditCategoryForm({ ...editCategoryForm, is_active: e.target.checked })}
                  className="w-4 h-4 text-brand-600 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700">Active (uncheck to hide from new fee structures)</label>
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="flex-1">Save Changes</Button>
                <Button type="button" variant="secondary" className="flex-1" onClick={() => setEditingCategory(null)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Fee Structure Modal */}
      {showStructureModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4 text-gray-900">Create Fee Structure</h2>

            <form onSubmit={handleCreateStructure} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fee Category *</label>
                <select
                  required
                  value={structureForm.fee_category_id}
                  onChange={(e) => setStructureForm({ ...structureForm, fee_category_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">Select category</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Academic Session *</label>
                <select
                  required
                  value={structureForm.session_id}
                  onChange={(e) => setStructureForm({ ...structureForm, session_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">Select session</option>
                  {sessions.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}{s.is_current ? ' (Current)' : ''}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Class</label>
                <select
                  value={structureForm.class_id}
                  onChange={(e) => setStructureForm({ ...structureForm, class_id: e.target.value, class_level: e.target.value ? '' : structureForm.class_level })}
                  disabled={!!structureForm.class_level}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 disabled:bg-gray-100 disabled:text-gray-400"
                >
                  <option value="">All Classes</option>
                  {classes.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Or Class Level <span className="text-gray-400 font-normal">(applies to every class at this level instead of one)</span>
                </label>
                <select
                  value={structureForm.class_level}
                  onChange={(e) => setStructureForm({ ...structureForm, class_level: e.target.value, class_id: e.target.value ? '' : structureForm.class_id })}
                  disabled={!!structureForm.class_id}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 disabled:bg-gray-100 disabled:text-gray-400"
                >
                  <option value="">None</option>
                  <option value="Primary">Primary</option>
                  <option value="Junior">Junior</option>
                  <option value="Senior">Senior</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount (₦) *</label>
                <input
                  type="number"
                  required
                  min="0"
                  step="0.01"
                  value={structureForm.amount}
                  onChange={(e) => setStructureForm({ ...structureForm, amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  placeholder="e.g., 50000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Frequency *</label>
                <select
                  required
                  value={structureForm.payment_frequency}
                  onChange={(e) => setStructureForm({ ...structureForm, payment_frequency: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="termly">Termly</option>
                  <option value="annually">Annually</option>
                  <option value="monthly">Monthly</option>
                  <option value="one-time">One-time</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                <input
                  type="date"
                  value={structureForm.due_date}
                  onChange={(e) => setStructureForm({ ...structureForm, due_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="flex-1">Create Fee Structure</Button>
                <Button type="button" variant="secondary" className="flex-1" onClick={() => setShowStructureModal(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
