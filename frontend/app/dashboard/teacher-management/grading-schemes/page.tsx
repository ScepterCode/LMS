'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';

interface GradingSchemeComponent {
  id?: string;
  component_type: string;
  component_name: string;
  weight_percentage: number;
  max_score: number;
  required: boolean;
  display_order: number;
}

interface GradingScheme {
  id: string;
  name: string;
  description?: string;
  session_id: string;
  is_active: boolean;
  is_default: boolean;
  components: GradingSchemeComponent[];
  created_at: string;
}

export default function GradingSchemesPage() {
  const [schemes, setSchemes] = useState<GradingScheme[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingScheme, setEditingScheme] = useState<GradingScheme | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    session_id: '',
    is_default: false,
    components: [] as GradingSchemeComponent[],
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    const [schemesRes, sessionsRes] = await Promise.all([
      api.getGradingSchemes(),
      api.getSessions(),
    ]);

    if (schemesRes.data) setSchemes(schemesRes.data as GradingScheme[]);
    if (sessionsRes.data) setSessions(sessionsRes.data as any[]);
    setLoading(false);
  };

  const handleAddComponent = () => {
    setFormData({
      ...formData,
      components: [
        ...formData.components,
        {
          component_type: 'test',
          component_name: '',
          weight_percentage: 0,
          max_score: 0,
          required: true,
          display_order: formData.components.length + 1,
        },
      ],
    });
  };

  const handleRemoveComponent = (index: number) => {
    const newComponents = formData.components.filter((_, i) => i !== index);
    // Update display orders
    newComponents.forEach((comp, i) => {
      comp.display_order = i + 1;
    });
    setFormData({ ...formData, components: newComponents });
  };

  const handleComponentChange = (index: number, field: string, value: any) => {
    const newComponents = [...formData.components];
    (newComponents[index] as any)[field] = value;
    setFormData({ ...formData, components: newComponents });
  };

  const getTotalWeight = () => {
    return formData.components.reduce((sum, comp) => sum + Number(comp.weight_percentage), 0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const totalWeight = getTotalWeight();
    if (totalWeight !== 100) {
      alert('Component weights must sum to 100%');
      return;
    }

    if (!formData.name || !formData.session_id || formData.components.length === 0) {
      alert('Please fill all required fields and add at least one component');
      return;
    }

    const response = editingScheme
      ? await api.updateGradingScheme(editingScheme.id, formData)
      : await api.createGradingScheme(formData);

    if (response.error) {
      alert(response.error);
    } else {
      await loadData();
      setShowCreateModal(false);
      setEditingScheme(null);
      resetForm();
    }
  };

  const handleEdit = (scheme: GradingScheme) => {
    setEditingScheme(scheme);
    setFormData({
      name: scheme.name,
      description: scheme.description || '',
      session_id: scheme.session_id,
      is_default: scheme.is_default,
      components: scheme.components.map(c => ({ ...c })),
    });
    setShowCreateModal(true);
  };

  const handleDelete = async (schemeId: string) => {
    if (!confirm('Are you sure you want to delete this grading scheme?')) return;

    const response = await api.deleteGradingScheme(schemeId);
    if (response.error) {
      alert(response.error);
    } else {
      await loadData();
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      session_id: '',
      is_default: false,
      components: [],
    });
  };

  const handleCloseModal = () => {
    setShowCreateModal(false);
    setEditingScheme(null);
    resetForm();
  };

  return (
    <DashboardLayout>
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Grading Schemes</h2>
          <p className="text-gray-600 mt-1">Create and manage assessment formats</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Create Grading Scheme
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="grid gap-6">
          {(!schemes || schemes.length === 0) ? (
            <div className="bg-white p-12 rounded-lg shadow-sm text-center">
              <p className="text-gray-500">No grading schemes found. Create your first scheme to get started.</p>
            </div>
          ) : (
            (schemes || []).map((scheme) => (
              <div key={scheme.id} className="bg-white p-6 rounded-lg shadow-sm">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                      {scheme.name}
                      {scheme.is_default && (
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                          Default
                        </span>
                      )}
                    </h3>
                    {scheme.description && (
                      <p className="text-sm text-gray-600 mt-1">{scheme.description}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(scheme)}
                      className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(scheme.id)}
                      className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-gray-700">Components:</h4>
                  {scheme.components.map((comp, idx) => (
                    <div key={idx} className="flex items-center gap-4 text-sm bg-gray-50 p-3 rounded">
                      <span className="font-medium text-gray-900">{comp.component_name}</span>
                      <span className="text-gray-600">({comp.component_type})</span>
                      <span className="text-blue-600 font-semibold">{comp.weight_percentage}%</span>
                      <span className="text-gray-600">Max: {comp.max_score} points</span>
                      {comp.required && (
                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Required</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-900">
                {editingScheme ? 'Edit Grading Scheme' : 'Create Grading Scheme'}
              </h3>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Scheme Name <span className="text-red-600">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="e.g., 20-20-60 Format"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Session <span className="text-red-600">*</span>
                  </label>
                  <select
                    value={formData.session_id}
                    onChange={(e) => setFormData({ ...formData, session_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  >
                    <option value="">Select Session</option>
                    {sessions.map((session) => (
                      <option key={session.id} value={session.id}>
                        {session.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  rows={2}
                  placeholder="Briefly describe this grading format"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_default"
                  checked={formData.is_default}
                  onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                  className="rounded"
                />
                <label htmlFor="is_default" className="text-sm text-gray-700">
                  Set as default for this session
                </label>
              </div>

              {/* Components Section */}
              <div className="border-t pt-6">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900">Assessment Components</h4>
                    <p className="text-sm text-gray-600">Total Weight: {getTotalWeight()}% (must equal 100%)</p>
                  </div>
                  <button
                    type="button"
                    onClick={handleAddComponent}
                    className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    Add Component
                  </button>
                </div>

                <div className="space-y-4">
                  {formData.components.map((comp, index) => (
                    <div key={index} className="bg-gray-50 p-4 rounded-lg">
                      <div className="grid md:grid-cols-4 gap-4">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
                          <select
                            value={comp.component_type}
                            onChange={(e) => handleComponentChange(index, 'component_type', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                          >
                            <option value="test">Test</option>
                            <option value="coursework">Coursework</option>
                            <option value="exam">Exam</option>
                            <option value="assignment">Assignment</option>
                            <option value="project">Project</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Name</label>
                          <input
                            type="text"
                            value={comp.component_name}
                            onChange={(e) => handleComponentChange(index, 'component_name', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            placeholder="e.g., Test 1"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Weight %</label>
                          <input
                            type="number"
                            value={comp.weight_percentage}
                            onChange={(e) => handleComponentChange(index, 'weight_percentage', parseFloat(e.target.value))}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            min="0"
                            max="100"
                            step="0.1"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Max Score</label>
                          <input
                            type="number"
                            value={comp.max_score}
                            onChange={(e) => handleComponentChange(index, 'max_score', parseFloat(e.target.value))}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            min="0"
                            step="0.1"
                            required
                          />
                        </div>
                      </div>

                      <div className="flex items-center justify-between mt-3">
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            id={`required-${index}`}
                            checked={comp.required}
                            onChange={(e) => handleComponentChange(index, 'required', e.target.checked)}
                            className="rounded"
                          />
                          <label htmlFor={`required-${index}`} className="text-xs text-gray-700">
                            Required
                          </label>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveComponent(index)}
                          className="text-xs text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}

                  {formData.components.length === 0 && (
                    <div className="text-center py-8 text-gray-500 text-sm">
                      No components added. Click "Add Component" to get started.
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-6 border-t">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {editingScheme ? 'Update Scheme' : 'Create Scheme'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
