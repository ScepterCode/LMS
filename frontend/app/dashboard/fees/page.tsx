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
  is_mandatory: boolean;
}

interface FeeStructure {
  id: string;
  category_name: string;
  class_name?: string;
  amount: number;
  payment_frequency: string;
  due_date?: string;
  is_active: boolean;
}

export default function FeeManagementPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'categories' | 'structures'>('categories');
  const [categories, setCategories] = useState<FeeCategory[]>([]);
  const [structures, setStructures] = useState<FeeStructure[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [showStructureModal, setShowStructureModal] = useState(false);
  
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    code: '',
    description: '',
    is_mandatory: true
  });

  useEffect(() => {
    fetchData();
  }, [activeTab]);

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
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {categories.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-6 py-12 text-center text-gray-500">
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
                          <Badge tone="success">Active</Badge>
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
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {structures.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
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
                          {structure.class_name || 'All Classes'}
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
    </DashboardLayout>
  );
}
