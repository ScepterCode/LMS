'use client';

import { useState, useEffect, useMemo } from 'react';
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
  fee_category_id?: string;
  session_id?: string;
  class_id?: string;
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

interface StructureDetail {
  structure: FeeStructure & { currency?: string };
  stats: {
    student_count: number;
    total_expected: number;
    total_collected: number;
    total_outstanding: number;
    collection_rate: number;
    by_status: Record<string, number>;
  };
  students: {
    student_fee_id: string;
    student_id: string;
    student_name?: string | null;
    admission_number?: string | null;
    final_amount: number;
    amount_paid: number;
    balance: number;
    status: string;
  }[];
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
  const [editingStructure, setEditingStructure] = useState<FeeStructure | null>(null);
  const [editStructureForm, setEditStructureForm] = useState({
    amount: '',
    due_date: '',
    is_active: true,
  });
  const [viewingStructureDetail, setViewingStructureDetail] = useState<StructureDetail | null>(null);
  const [structureDetailLoading, setStructureDetailLoading] = useState(false);
  const [structureFilters, setStructureFilters] = useState({
    session_id: '',
    class_id: '',
    fee_category_id: '',
    status: 'all' as 'all' | 'active' | 'inactive',
    search: '',
    sort: 'default' as 'default' | 'amount_desc' | 'amount_asc' | 'category',
  });

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

  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkSubmitting, setBulkSubmitting] = useState(false);
  const [bulkForm, setBulkForm] = useState({
    fee_category_id: '',
    session_id: '',
    payment_frequency: 'termly',
    due_date: '',
    applyToAll: '',
  });
  const [bulkRows, setBulkRows] = useState<Record<string, { selected: boolean; amount: string }>>({});

  const [showCopyModal, setShowCopyModal] = useState(false);
  const [copySubmitting, setCopySubmitting] = useState(false);
  const [copyForm, setCopyForm] = useState({
    source_session_id: '',
    target_session_id: '',
    adjustment_type: 'none' as 'none' | 'percentage' | 'fixed',
    adjustment_value: '',
  });

  const [showQuickSetupModal, setShowQuickSetupModal] = useState(false);
  const [quickSetupSubmitting, setQuickSetupSubmitting] = useState(false);
  const [quickSetupForm, setQuickSetupForm] = useState({
    categoryMode: 'new' as 'new' | 'existing',
    existingCategoryId: '',
    name: '',
    code: '',
    description: '',
    is_mandatory: true,
    session_id: '',
    class_id: '',
    class_level: '',
    amount: '',
    payment_frequency: 'termly',
    due_date: '',
    assignNow: true,
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
          setQuickSetupForm((prev) => ({ ...prev, session_id: current.id }));
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

  const handleViewStructureDetail = async (structure: FeeStructure) => {
    setStructureDetailLoading(true);
    try {
      const response = await api.get(`/api/v1/fees/structures/${structure.id}/detail`);
      if (response.error) {
        alert(response.error);
        return;
      }
      setViewingStructureDetail(response.data as StructureDetail);
    } catch (error) {
      console.error('Error fetching fee structure detail:', error);
      alert('Failed to load fee structure details');
    } finally {
      setStructureDetailLoading(false);
    }
  };

  const openEditStructure = (structure: FeeStructure) => {
    setEditingStructure(structure);
    setEditStructureForm({
      amount: String(structure.amount ?? ''),
      due_date: structure.due_date || '',
      is_active: structure.is_active,
    });
  };

  const handleUpdateStructure = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingStructure) return;
    try {
      const response = await api.put(`/api/v1/fees/structures/${editingStructure.id}`, {
        amount: parseFloat(editStructureForm.amount),
        due_date: editStructureForm.due_date || null,
        is_active: editStructureForm.is_active,
      });
      if (response.error) {
        alert(response.error);
        return;
      }
      setEditingStructure(null);
      fetchData();
    } catch (error: any) {
      console.error('Error updating fee structure:', error);
      alert(error.response?.data?.detail || 'Failed to update fee structure');
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

  const openBulkModal = () => {
    const current = sessions.find((s) => s.is_current);
    setBulkForm({
      fee_category_id: '',
      session_id: current?.id || '',
      payment_frequency: 'termly',
      due_date: '',
      applyToAll: '',
    });
    setBulkRows(Object.fromEntries(classes.map((c) => [c.id, { selected: false, amount: '' }])));
    setShowBulkModal(true);
  };

  const handleBulkCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const items = classes
      .filter((c) => bulkRows[c.id]?.selected)
      .map((c) => ({ class_id: c.id, amount: parseFloat(bulkRows[c.id].amount) }));
    if (items.length === 0) {
      alert('Select at least one class.');
      return;
    }
    if (items.some((i) => !Number.isFinite(i.amount) || i.amount < 0)) {
      alert('Enter a valid amount for every selected class.');
      return;
    }
    setBulkSubmitting(true);
    try {
      const response = await api.post('/api/v1/fees/structures/bulk-create', {
        fee_category_id: bulkForm.fee_category_id,
        session_id: bulkForm.session_id,
        payment_frequency: bulkForm.payment_frequency,
        due_date: bulkForm.due_date || null,
        items,
      });
      if (response.error) {
        alert(response.error);
        return;
      }
      alert(`Created ${(response.data as any).created} fee structure(s).`);
      setShowBulkModal(false);
      fetchData();
    } catch (error: any) {
      console.error('Error bulk-creating fee structures:', error);
      alert(error.response?.data?.detail || 'Failed to create fee structures');
    } finally {
      setBulkSubmitting(false);
    }
  };

  const handleCopySession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (copyForm.source_session_id === copyForm.target_session_id) {
      alert('Source and target sessions must be different.');
      return;
    }
    setCopySubmitting(true);
    try {
      const response = await api.post('/api/v1/fees/structures/copy-session', {
        source_session_id: copyForm.source_session_id,
        target_session_id: copyForm.target_session_id,
        adjustment_type: copyForm.adjustment_type,
        adjustment_value: copyForm.adjustment_type === 'none' ? 0 : parseFloat(copyForm.adjustment_value || '0'),
      });
      if (response.error) {
        alert(response.error);
        return;
      }
      const data = response.data as any;
      alert(`Copied ${data.created} structure(s)${data.skipped ? `, skipped ${data.skipped} already in the target session` : ''}.`);
      setShowCopyModal(false);
      fetchData();
    } catch (error: any) {
      console.error('Error copying fee structures:', error);
      alert(error.response?.data?.detail || 'Failed to copy fee structures');
    } finally {
      setCopySubmitting(false);
    }
  };

  const resetQuickSetupForm = () => {
    setQuickSetupForm({
      categoryMode: 'new',
      existingCategoryId: '',
      name: '',
      code: '',
      description: '',
      is_mandatory: true,
      session_id: quickSetupForm.session_id,
      class_id: '',
      class_level: '',
      amount: '',
      payment_frequency: 'termly',
      due_date: '',
      assignNow: true,
    });
  };

  const handleQuickSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setQuickSetupSubmitting(true);
    try {
      let categoryId = quickSetupForm.existingCategoryId;

      if (quickSetupForm.categoryMode === 'new') {
        const categoryResponse = await api.post('/api/v1/fees/categories', {
          name: quickSetupForm.name,
          code: quickSetupForm.code,
          description: quickSetupForm.description || undefined,
          is_mandatory: quickSetupForm.is_mandatory,
        });
        if (categoryResponse.error) {
          alert(categoryResponse.error);
          return;
        }
        categoryId = (categoryResponse.data as FeeCategory).id;
      }

      const structureResponse = await api.post('/api/v1/fees/structures', {
        fee_category_id: categoryId,
        session_id: quickSetupForm.session_id,
        class_id: quickSetupForm.class_id || null,
        class_level: quickSetupForm.class_level || null,
        amount: parseFloat(quickSetupForm.amount),
        payment_frequency: quickSetupForm.payment_frequency,
        due_date: quickSetupForm.due_date || null,
      });
      if (structureResponse.error) {
        alert(structureResponse.error);
        return;
      }
      const structureId = (structureResponse.data as { id: string }).id;

      let assignedMessage = '';
      if (quickSetupForm.assignNow && (quickSetupForm.class_id || quickSetupForm.class_level)) {
        const params = new URLSearchParams({ session_id: quickSetupForm.session_id });
        if (quickSetupForm.class_id) params.set('class_id', quickSetupForm.class_id);
        if (quickSetupForm.class_level) params.set('class_level', quickSetupForm.class_level);
        const assignResponse = await api.post(
          `/api/v1/fees/student-fees/bulk-assign?${params.toString()}`,
          [structureId]
        );
        if (assignResponse.error) {
          alert(`Fee structure created, but bulk assignment failed: ${assignResponse.error}`);
        } else {
          const assigned = assignResponse.data as { fees_assigned?: number };
          assignedMessage = ` and assigned to ${assigned.fees_assigned ?? 0} student(s)`;
        }
      }

      alert(`Fee category and structure created successfully${assignedMessage}!`);
      setShowQuickSetupModal(false);
      resetQuickSetupForm();
      fetchData();
    } catch (error: any) {
      console.error('Error in quick fee setup:', error);
      alert(error.response?.data?.detail || 'Failed to complete quick fee setup');
    } finally {
      setQuickSetupSubmitting(false);
    }
  };

  const structureFormDuplicate = useMemo(() => {
    if (!structureForm.fee_category_id || !structureForm.session_id) return false;
    return structures.some((s) =>
      s.fee_category_id === structureForm.fee_category_id &&
      s.session_id === structureForm.session_id &&
      (structureForm.class_id
        ? s.class_id === structureForm.class_id
        : structureForm.class_level
          ? (!s.class_id && s.class_level === structureForm.class_level)
          : (!s.class_id && !s.class_level)),
    );
  }, [structures, structureForm.fee_category_id, structureForm.session_id, structureForm.class_id, structureForm.class_level]);

  const activeStructureFilterCount =
    (structureFilters.session_id ? 1 : 0) +
    (structureFilters.class_id ? 1 : 0) +
    (structureFilters.fee_category_id ? 1 : 0) +
    (structureFilters.status !== 'all' ? 1 : 0) +
    (structureFilters.search.trim() ? 1 : 0);

  const clearStructureFilters = () =>
    setStructureFilters({
      session_id: '',
      class_id: '',
      fee_category_id: '',
      status: 'all',
      search: '',
      sort: 'default',
    });

  const exportStructuresCsv = () => {
    const sessionName = (id?: string) => sessions.find((s) => s.id === id)?.name ?? '';
    const csvCell = (v: string | number) => {
      const str = String(v ?? '');
      return /[",\n]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str;
    };
    const header = ['Category', 'Class', 'Session', 'Amount', 'Frequency', 'Due Date', 'Status'];
    const rows = filteredStructures.map((s) => [
      s.category_name ?? '',
      s.class_name || (s.class_level ? `All ${s.class_level} Classes` : 'All Classes'),
      sessionName(s.session_id),
      Number(s.amount),
      s.payment_frequency,
      s.due_date || '',
      s.is_active ? 'Active' : 'Inactive',
    ]);
    const csv = [header, ...rows].map((r) => r.map(csvCell).join(',')).join('\r\n');
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `fee-structures-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const filteredStructures = useMemo(() => {
    const term = structureFilters.search.trim().toLowerCase();
    const result = structures.filter((s) => {
      if (structureFilters.session_id && s.session_id !== structureFilters.session_id) return false;
      if (structureFilters.class_id && s.class_id !== structureFilters.class_id) return false;
      if (structureFilters.fee_category_id && s.fee_category_id !== structureFilters.fee_category_id) return false;
      if (structureFilters.status === 'active' && !s.is_active) return false;
      if (structureFilters.status === 'inactive' && s.is_active) return false;
      if (term) {
        const haystack = `${s.category_name ?? ''} ${s.class_name ?? ''} ${s.class_level ?? ''}`.toLowerCase();
        if (!haystack.includes(term)) return false;
      }
      return true;
    });
    switch (structureFilters.sort) {
      case 'amount_desc':
        return [...result].sort((a, b) => Number(b.amount) - Number(a.amount));
      case 'amount_asc':
        return [...result].sort((a, b) => Number(a.amount) - Number(b.amount));
      case 'category':
        return [...result].sort((a, b) => (a.category_name ?? '').localeCompare(b.category_name ?? ''));
      default:
        return result;
    }
  }, [structures, structureFilters]);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <PageHeader
          title="Fee Management"
          subtitle="Manage fee categories and structures"
          actions={
            <div className="flex gap-3">
              <Button variant="secondary" onClick={() => setShowQuickSetupModal(true)}>Quick Fee Setup</Button>
              <Button onClick={() => router.push('/dashboard/fees/payments')}>Record Payment</Button>
            </div>
          }
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
            <div className="flex flex-wrap justify-end gap-3">
              <Button
                variant="secondary"
                onClick={exportStructuresCsv}
                disabled={filteredStructures.length === 0}
              >
                Export CSV
              </Button>
              <Button variant="secondary" onClick={() => setShowCopyModal(true)}>Copy from Session</Button>
              <Button variant="secondary" onClick={openBulkModal}>Bulk Add</Button>
              <Button onClick={() => setShowStructureModal(true)}>Add Fee Structure</Button>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <input
                  type="text"
                  value={structureFilters.search}
                  onChange={(e) => setStructureFilters({ ...structureFilters, search: e.target.value })}
                  placeholder="Search category or class"
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                />
                <select
                  value={structureFilters.session_id}
                  onChange={(e) => setStructureFilters({ ...structureFilters, session_id: e.target.value })}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">All sessions</option>
                  {sessions.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}{s.is_current ? ' (Current)' : ''}</option>
                  ))}
                </select>
                <select
                  value={structureFilters.class_id}
                  onChange={(e) => setStructureFilters({ ...structureFilters, class_id: e.target.value })}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">All classes</option>
                  {classes.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
                <select
                  value={structureFilters.fee_category_id}
                  onChange={(e) => setStructureFilters({ ...structureFilters, fee_category_id: e.target.value })}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">All categories</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
                <select
                  value={structureFilters.status}
                  onChange={(e) => setStructureFilters({ ...structureFilters, status: e.target.value as 'all' | 'active' | 'inactive' })}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="all">All statuses</option>
                  <option value="active">Active only</option>
                  <option value="inactive">Inactive only</option>
                </select>
                <select
                  value={structureFilters.sort}
                  onChange={(e) => setStructureFilters({ ...structureFilters, sort: e.target.value as typeof structureFilters.sort })}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="default">Default order</option>
                  <option value="amount_desc">Amount (high to low)</option>
                  <option value="amount_asc">Amount (low to high)</option>
                  <option value="category">Category (A–Z)</option>
                </select>
              </div>
              <div className="flex items-center justify-between mt-3 text-sm text-gray-500">
                <span>
                  Showing {filteredStructures.length} of {structures.length}
                  {activeStructureFilterCount > 0 && ` · ${activeStructureFilterCount} filter${activeStructureFilterCount > 1 ? 's' : ''} active`}
                </span>
                {activeStructureFilterCount > 0 && (
                  <button onClick={clearStructureFilters} className="text-brand-600 hover:text-brand-800">
                    Clear filters
                  </button>
                )}
              </div>
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
                  ) : filteredStructures.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                        No fee structures match the current filters.
                      </td>
                    </tr>
                  ) : (
                    filteredStructures.map((structure) => (
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
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
                          <button
                            onClick={() => handleViewStructureDetail(structure)}
                            disabled={structureDetailLoading}
                            className="text-gray-600 hover:text-gray-900 disabled:opacity-50"
                          >
                            Details
                          </button>
                          <button
                            onClick={() => openEditStructure(structure)}
                            className="text-brand-600 hover:text-brand-800"
                          >
                            Edit
                          </button>
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

              {structureFormDuplicate && (
                <p className="text-sm text-danger-600 bg-danger-50 rounded-lg px-3 py-2">
                  A structure for this category, session and class already exists. Edit that one instead.
                </p>
              )}

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="flex-1" disabled={structureFormDuplicate}>Create Fee Structure</Button>
                <Button type="button" variant="secondary" className="flex-1" onClick={() => setShowStructureModal(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Add Fee Structures Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-1 text-gray-900">Bulk Add Fee Structures</h2>
            <p className="text-sm text-gray-500 mb-4">
              One structure per selected class, all sharing the category, session and frequency below.
            </p>

            <form onSubmit={handleBulkCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fee Category *</label>
                <select
                  required
                  value={bulkForm.fee_category_id}
                  onChange={(e) => setBulkForm({ ...bulkForm, fee_category_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">Select category</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Session *</label>
                  <select
                    required
                    value={bulkForm.session_id}
                    onChange={(e) => setBulkForm({ ...bulkForm, session_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  >
                    <option value="">Select session</option>
                    {sessions.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}{s.is_current ? ' (Current)' : ''}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Frequency *</label>
                  <select
                    required
                    value={bulkForm.payment_frequency}
                    onChange={(e) => setBulkForm({ ...bulkForm, payment_frequency: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  >
                    <option value="termly">Termly</option>
                    <option value="annually">Annually</option>
                    <option value="monthly">Monthly</option>
                    <option value="one-time">One-time</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                <input
                  type="date"
                  value={bulkForm.due_date}
                  onChange={(e) => setBulkForm({ ...bulkForm, due_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                />
              </div>

              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Apply amount to all selected</label>
                  <input
                    type="number"
                    min="0"
                    value={bulkForm.applyToAll}
                    onChange={(e) => setBulkForm({ ...bulkForm, applyToAll: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    placeholder="e.g., 50000"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => setBulkRows((prev) => {
                    const next = { ...prev };
                    for (const c of classes) {
                      if (next[c.id]?.selected) next[c.id] = { ...next[c.id], amount: bulkForm.applyToAll };
                    }
                    return next;
                  })}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Fill
                </button>
              </div>

              <div className="border border-gray-200 rounded-lg divide-y divide-gray-100 max-h-56 overflow-y-auto">
                {classes.length === 0 ? (
                  <p className="p-3 text-sm text-gray-500">No classes found.</p>
                ) : (
                  classes.map((c) => (
                    <div key={c.id} className="flex items-center gap-3 p-2">
                      <input
                        type="checkbox"
                        checked={bulkRows[c.id]?.selected || false}
                        onChange={(e) => setBulkRows((prev) => ({
                          ...prev,
                          [c.id]: { selected: e.target.checked, amount: prev[c.id]?.amount || '' },
                        }))}
                        className="w-4 h-4 text-brand-600 border-gray-300 rounded"
                      />
                      <span className="flex-1 text-sm text-gray-700">{c.name}</span>
                      <input
                        type="number"
                        min="0"
                        value={bulkRows[c.id]?.amount || ''}
                        onChange={(e) => setBulkRows((prev) => ({
                          ...prev,
                          [c.id]: { selected: prev[c.id]?.selected || false, amount: e.target.value },
                        }))}
                        disabled={!bulkRows[c.id]?.selected}
                        className="w-32 px-2 py-1 border border-gray-300 rounded text-sm disabled:bg-gray-100"
                        placeholder="Amount"
                      />
                    </div>
                  ))
                )}
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="submit" className="flex-1" disabled={bulkSubmitting}>
                  {bulkSubmitting ? 'Creating…' : 'Create Structures'}
                </Button>
                <Button type="button" variant="secondary" className="flex-1" onClick={() => setShowBulkModal(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Copy From Session Modal */}
      {showCopyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-1 text-gray-900">Copy Fees from Another Session</h2>
            <p className="text-sm text-gray-500 mb-4">
              Copies every active structure from the source session. Any category/class already
              present in the target session is skipped.
            </p>

            <form onSubmit={handleCopySession} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Copy from *</label>
                <select
                  required
                  value={copyForm.source_session_id}
                  onChange={(e) => setCopyForm({ ...copyForm, source_session_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">Select source session</option>
                  {sessions.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}{s.is_current ? ' (Current)' : ''}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Copy to *</label>
                <select
                  required
                  value={copyForm.target_session_id}
                  onChange={(e) => setCopyForm({ ...copyForm, target_session_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">Select target session</option>
                  {sessions.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}{s.is_current ? ' (Current)' : ''}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Adjustment</label>
                  <select
                    value={copyForm.adjustment_type}
                    onChange={(e) => setCopyForm({ ...copyForm, adjustment_type: e.target.value as 'none' | 'percentage' | 'fixed' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  >
                    <option value="none">No change</option>
                    <option value="percentage">Increase by %</option>
                    <option value="fixed">Increase by ₦</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Value</label>
                  <input
                    type="number"
                    value={copyForm.adjustment_value}
                    onChange={(e) => setCopyForm({ ...copyForm, adjustment_value: e.target.value })}
                    disabled={copyForm.adjustment_type === 'none'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 disabled:bg-gray-100"
                    placeholder={copyForm.adjustment_type === 'percentage' ? '10' : '5000'}
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="submit" className="flex-1" disabled={copySubmitting}>
                  {copySubmitting ? 'Copying…' : 'Copy Fees'}
                </Button>
                <Button type="button" variant="secondary" className="flex-1" onClick={() => setShowCopyModal(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Fee Structure Detail Modal */}
      {viewingStructureDetail && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  {viewingStructureDetail.structure.category_name || 'Fee Structure'}
                </h2>
                <p className="text-sm text-gray-500">
                  {viewingStructureDetail.structure.class_name
                    || (viewingStructureDetail.structure.class_level
                      ? `All ${viewingStructureDetail.structure.class_level} Classes`
                      : 'All Classes')}
                  {' · '}
                  ₦{Number(viewingStructureDetail.structure.amount).toLocaleString()}
                  {' · '}
                  {viewingStructureDetail.structure.payment_frequency}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setViewingStructureDetail(null)}
                className="text-gray-400 hover:text-gray-600 text-xl leading-none"
              >
                ×
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500">Students</p>
                <p className="text-lg font-semibold text-gray-900">{viewingStructureDetail.stats.student_count}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500">Expected</p>
                <p className="text-lg font-semibold text-gray-900">₦{viewingStructureDetail.stats.total_expected.toLocaleString()}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500">Collected</p>
                <p className="text-lg font-semibold text-success-600">₦{viewingStructureDetail.stats.total_collected.toLocaleString()}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500">Outstanding</p>
                <p className="text-lg font-semibold text-danger-600">₦{viewingStructureDetail.stats.total_outstanding.toLocaleString()}</p>
              </div>
            </div>

            <div className="mb-4 text-sm text-gray-600">
              Collection rate: <span className="font-semibold text-gray-900">{viewingStructureDetail.stats.collection_rate.toFixed(1)}%</span>
              {Object.keys(viewingStructureDetail.stats.by_status).length > 0 && (
                <span className="ml-3">
                  {Object.entries(viewingStructureDetail.stats.by_status).map(([st, n]) => (
                    <span key={st} className="mr-2 capitalize">{st}: {n}</span>
                  ))}
                </span>
              )}
            </div>

            {viewingStructureDetail.students.length === 0 ? (
              <p className="text-sm text-gray-500 py-6 text-center border-t border-gray-200">
                No students have been assigned this fee yet.
              </p>
            ) : (
              <div className="overflow-x-auto border-t border-gray-200">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Paid</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Balance</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {viewingStructureDetail.students.map((s) => (
                      <tr key={s.student_fee_id}>
                        <td className="px-3 py-2 text-gray-900">
                          {s.student_name || 'Unknown'}
                          {s.admission_number ? <span className="text-gray-400"> ({s.admission_number})</span> : null}
                        </td>
                        <td className="px-3 py-2 text-right text-gray-900">₦{s.final_amount.toLocaleString()}</td>
                        <td className="px-3 py-2 text-right text-gray-900">₦{s.amount_paid.toLocaleString()}</td>
                        <td className="px-3 py-2 text-right text-gray-900">₦{s.balance.toLocaleString()}</td>
                        <td className="px-3 py-2 capitalize text-gray-500">{s.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="flex justify-end pt-4">
              <Button type="button" variant="secondary" onClick={() => setViewingStructureDetail(null)}>Close</Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Fee Structure Modal */}
      {editingStructure && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-1 text-gray-900">Edit Fee Structure</h2>
            <p className="text-sm text-gray-500 mb-4">
              {editingStructure.category_name}
              {' – '}
              {editingStructure.class_name
                || (editingStructure.class_level ? `All ${editingStructure.class_level} Classes` : 'All Classes')}
            </p>

            <form onSubmit={handleUpdateStructure} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount (₦) *</label>
                <input
                  type="number"
                  required
                  min="0"
                  step="0.01"
                  value={editStructureForm.amount}
                  onChange={(e) => setEditStructureForm({ ...editStructureForm, amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                <input
                  type="date"
                  value={editStructureForm.due_date}
                  onChange={(e) => setEditStructureForm({ ...editStructureForm, due_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={editStructureForm.is_active}
                  onChange={(e) => setEditStructureForm({ ...editStructureForm, is_active: e.target.checked })}
                  className="w-4 h-4 text-brand-600 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700">Active</label>
              </div>

              <p className="text-xs text-gray-400">
                To change the category, session, class or payment frequency, delete this structure and create a new one.
              </p>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="flex-1">Save Changes</Button>
                <Button type="button" variant="secondary" className="flex-1" onClick={() => setEditingStructure(null)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Quick Fee Setup Wizard */}
      {showQuickSetupModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-1 text-gray-900">Quick Fee Setup</h2>
            <p className="text-sm text-gray-500 mb-4">
              Create a fee category and structure together, and optionally assign it to students right away.
            </p>

            <form onSubmit={handleQuickSetup} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fee Category *</label>
                <div className="flex gap-4 mb-2 text-sm">
                  <label className="flex items-center gap-1.5">
                    <input
                      type="radio"
                      checked={quickSetupForm.categoryMode === 'new'}
                      onChange={() => setQuickSetupForm({ ...quickSetupForm, categoryMode: 'new' })}
                    />
                    New category
                  </label>
                  <label className="flex items-center gap-1.5">
                    <input
                      type="radio"
                      checked={quickSetupForm.categoryMode === 'existing'}
                      onChange={() => setQuickSetupForm({ ...quickSetupForm, categoryMode: 'existing' })}
                    />
                    Use existing
                  </label>
                </div>

                {quickSetupForm.categoryMode === 'existing' ? (
                  <select
                    required
                    value={quickSetupForm.existingCategoryId}
                    onChange={(e) => setQuickSetupForm({ ...quickSetupForm, existingCategoryId: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  >
                    <option value="">Select category</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                ) : (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <input
                        type="text"
                        required
                        placeholder="Name (e.g., Tuition)"
                        value={quickSetupForm.name}
                        onChange={(e) => setQuickSetupForm({ ...quickSetupForm, name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                      <input
                        type="text"
                        required
                        placeholder="Code (e.g., TUITION)"
                        value={quickSetupForm.code}
                        onChange={(e) => setQuickSetupForm({ ...quickSetupForm, code: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                    </div>
                    <input
                      type="text"
                      placeholder="Description (optional)"
                      value={quickSetupForm.description}
                      onChange={(e) => setQuickSetupForm({ ...quickSetupForm, description: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    />
                    <label className="flex items-center gap-2 text-sm text-gray-700">
                      <input
                        type="checkbox"
                        checked={quickSetupForm.is_mandatory}
                        onChange={(e) => setQuickSetupForm({ ...quickSetupForm, is_mandatory: e.target.checked })}
                      />
                      Mandatory fee
                    </label>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Academic Session *</label>
                <select
                  required
                  value={quickSetupForm.session_id}
                  onChange={(e) => setQuickSetupForm({ ...quickSetupForm, session_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">Select session</option>
                  {sessions.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}{s.is_current ? ' (Current)' : ''}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Class</label>
                  <select
                    value={quickSetupForm.class_id}
                    onChange={(e) => setQuickSetupForm({ ...quickSetupForm, class_id: e.target.value, class_level: e.target.value ? '' : quickSetupForm.class_level })}
                    disabled={!!quickSetupForm.class_level}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 disabled:bg-gray-100 disabled:text-gray-400"
                  >
                    <option value="">All Classes</option>
                    {classes.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Or Class Level</label>
                  <select
                    value={quickSetupForm.class_level}
                    onChange={(e) => setQuickSetupForm({ ...quickSetupForm, class_level: e.target.value, class_id: e.target.value ? '' : quickSetupForm.class_id })}
                    disabled={!!quickSetupForm.class_id}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 disabled:bg-gray-100 disabled:text-gray-400"
                  >
                    <option value="">None</option>
                    <option value="Primary">Primary</option>
                    <option value="Junior">Junior</option>
                    <option value="Senior">Senior</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Amount (₦) *</label>
                  <input
                    type="number"
                    required
                    min="0"
                    step="0.01"
                    value={quickSetupForm.amount}
                    onChange={(e) => setQuickSetupForm({ ...quickSetupForm, amount: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    placeholder="e.g., 50000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Frequency *</label>
                  <select
                    required
                    value={quickSetupForm.payment_frequency}
                    onChange={(e) => setQuickSetupForm({ ...quickSetupForm, payment_frequency: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  >
                    <option value="termly">Termly</option>
                    <option value="annually">Annually</option>
                    <option value="monthly">Monthly</option>
                    <option value="one-time">One-time</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                <input
                  type="date"
                  value={quickSetupForm.due_date}
                  onChange={(e) => setQuickSetupForm({ ...quickSetupForm, due_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                />
              </div>

              <label className="flex items-start gap-2 text-sm text-gray-700 bg-gray-50 rounded-lg p-3">
                <input
                  type="checkbox"
                  className="mt-0.5"
                  checked={quickSetupForm.assignNow}
                  onChange={(e) => setQuickSetupForm({ ...quickSetupForm, assignNow: e.target.checked })}
                  disabled={!quickSetupForm.class_id && !quickSetupForm.class_level}
                />
                <span>
                  Assign this fee to students now
                  <span className="block text-xs text-gray-500">
                    {quickSetupForm.class_id || quickSetupForm.class_level
                      ? 'Applies immediately to every student in the class or level chosen above.'
                      : 'Pick a specific class or class level above to enable immediate assignment.'}
                  </span>
                </span>
              </label>

              <div className="flex gap-3 pt-2">
                <Button type="submit" className="flex-1" disabled={quickSetupSubmitting}>
                  {quickSetupSubmitting ? 'Setting up...' : 'Create & Continue'}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  className="flex-1"
                  onClick={() => { setShowQuickSetupModal(false); resetQuickSetupForm(); }}
                >
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
