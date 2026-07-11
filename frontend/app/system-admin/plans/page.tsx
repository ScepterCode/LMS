'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import SystemAdminLayout from '@/components/SystemAdminLayout';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

interface SubscriptionPlan {
  id: string;
  name: string;
  description: string | null;
  price_monthly: number;
  price_yearly: number;
  max_students: number;
  features: string[];
  is_active: boolean;
}

interface PlanFormState {
  id: string;
  name: string;
  description: string;
  price_monthly: string;
  price_yearly: string;
  max_students: string;
  features: string;
  is_active: boolean;
}

const emptyForm: PlanFormState = {
  id: '',
  name: '',
  description: '',
  price_monthly: '0',
  price_yearly: '0',
  max_students: '0',
  features: '',
  is_active: true,
};

export default function SubscriptionPlansPage() {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<PlanFormState>(emptyForm);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    setLoading(true);
    const res = await api.getSubscriptionPlans();
    if (res.data) setPlans((res.data as any).plans ?? []);
    setLoading(false);
  };

  const openCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setError('');
    setShowModal(true);
  };

  const openEdit = (plan: SubscriptionPlan) => {
    setEditingId(plan.id);
    setForm({
      id: plan.id,
      name: plan.name,
      description: plan.description ?? '',
      price_monthly: String(plan.price_monthly),
      price_yearly: String(plan.price_yearly),
      max_students: String(plan.max_students),
      features: plan.features.join('\n'),
      is_active: plan.is_active,
    });
    setError('');
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');

    const features = form.features.split('\n').map((f) => f.trim()).filter(Boolean);
    const price_monthly = parseFloat(form.price_monthly) || 0;
    const price_yearly = parseFloat(form.price_yearly) || 0;
    const max_students = parseInt(form.max_students, 10) || 0;

    const res = editingId
      ? await api.updateSubscriptionPlan(editingId, {
          name: form.name,
          description: form.description || undefined,
          price_monthly,
          price_yearly,
          max_students,
          features,
          is_active: form.is_active,
        })
      : await api.createSubscriptionPlan({
          id: form.id,
          name: form.name,
          description: form.description || undefined,
          price_monthly,
          price_yearly,
          max_students,
          features,
        });

    if (res.error) {
      setError(res.error);
      setSaving(false);
      return;
    }

    setSaving(false);
    setShowModal(false);
    await loadPlans();
  };

  return (
    <SystemAdminLayout>
      <div className="space-y-6">
        <PageHeader
          title="Subscription Plans"
          subtitle="Manage the plans schools can subscribe to"
          actions={<Button onClick={openCreate}>New Plan</Button>}
        />

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {plans.map((plan) => (
              <Card key={plan.id}>
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
                  <Badge tone={plan.is_active ? 'success' : 'neutral'}>{plan.is_active ? 'active' : 'inactive'}</Badge>
                </div>
                <p className="text-xs text-gray-400 mb-3 font-mono">{plan.id}</p>
                {plan.description && <p className="text-sm text-gray-600 mb-4">{plan.description}</p>}
                <div className="space-y-1 text-sm mb-4">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Monthly</span>
                    <span className="font-medium text-gray-900">₦{plan.price_monthly.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Yearly</span>
                    <span className="font-medium text-gray-900">₦{plan.price_yearly.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Max Students</span>
                    <span className="font-medium text-gray-900">{plan.max_students.toLocaleString()}</span>
                  </div>
                </div>
                {plan.features.length > 0 && (
                  <ul className="text-xs text-gray-600 space-y-1 mb-4 list-disc list-inside">
                    {plan.features.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                )}
                <Button variant="secondary" size="sm" onClick={() => openEdit(plan)} className="w-full">
                  Edit
                </Button>
              </Card>
            ))}
          </div>
        )}

        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 my-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {editingId ? `Edit ${editingId}` : 'New Subscription Plan'}
              </h3>

              {error && (
                <div className="bg-danger-50 border border-danger-100 text-danger-700 px-4 py-2 rounded-lg text-sm mb-4">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                {!editingId && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Plan ID (lowercase, no spaces)</label>
                    <input
                      type="text"
                      value={form.id}
                      onChange={(e) => setForm({ ...form, id: e.target.value.toLowerCase() })}
                      placeholder="e.g. enterprise"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    />
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <input
                    type="text"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Monthly (₦)</label>
                    <input
                      type="number"
                      value={form.price_monthly}
                      onChange={(e) => setForm({ ...form, price_monthly: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Yearly (₦)</label>
                    <input
                      type="number"
                      value={form.price_yearly}
                      onChange={(e) => setForm({ ...form, price_yearly: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Students</label>
                    <input
                      type="number"
                      value={form.max_students}
                      onChange={(e) => setForm({ ...form, max_students: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Features (one per line)</label>
                  <textarea
                    value={form.features}
                    onChange={(e) => setForm({ ...form, features: e.target.value })}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  />
                </div>
                {editingId && (
                  <label className="flex items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={form.is_active}
                      onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                      className="h-4 w-4 text-brand-600 border-gray-300 rounded"
                    />
                    Active (available for new schools)
                  </label>
                )}
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <Button variant="secondary" onClick={() => setShowModal(false)} disabled={saving}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={saving || !form.name || (!editingId && !form.id)}
                >
                  {saving ? 'Saving...' : editingId ? 'Save Changes' : 'Create Plan'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </SystemAdminLayout>
  );
}
