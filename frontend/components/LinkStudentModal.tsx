'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface Student {
  id: string;
  full_name: string;
  admission_number: string;
  class_name?: string;
}

interface LinkStudentModalProps {
  parentId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function LinkStudentModal({ parentId, onClose, onSuccess }: LinkStudentModalProps) {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  const [formData, setFormData] = useState({
    student_id: '',
    relationship: 'Father',
    is_primary: false,
  });

  useEffect(() => {
    loadStudents();
  }, []);

  const loadStudents = async () => {
    try {
      const response = await api.getStudents({ limit: 1000 });
      if (response.data) {
        setStudents(response.data as Student[]);
      }
    } catch (err) {
      console.error('Failed to load students:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const response = await api.linkParentToStudent(parentId, formData);
      
      if (response.error) {
        setError(response.error);
      } else {
        onSuccess();
        onClose();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to link student');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredStudents = students.filter(student =>
    student.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    student.admission_number.includes(searchTerm)
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4">
          <h3 className="text-lg font-semibold">Link Student to Parent</h3>
          <p className="text-sm text-gray-600 mt-1">Select a student to link as this parent's ward</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Search Students */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Student
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name or admission number..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 mb-2"
            />
          </div>

          {/* Student Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Student *
            </label>
            {loading ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              </div>
            ) : (
              <div className="border border-gray-300 rounded-lg max-h-64 overflow-y-auto">
                {filteredStudents.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">
                    {searchTerm ? 'No students found matching your search' : 'No students available'}
                  </div>
                ) : (
                  <div className="divide-y">
                    {filteredStudents.map((student) => (
                      <label
                        key={student.id}
                        className={`flex items-center p-3 hover:bg-gray-50 cursor-pointer ${
                          formData.student_id === student.id ? 'bg-blue-50' : ''
                        }`}
                      >
                        <input
                          type="radio"
                          name="student_id"
                          value={student.id}
                          checked={formData.student_id === student.id}
                          onChange={handleChange}
                          required
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                        />
                        <div className="ml-3 flex-1">
                          <p className="text-sm font-medium text-gray-900">{student.full_name}</p>
                          <p className="text-xs text-gray-500">
                            {student.admission_number} {student.class_name && `• ${student.class_name}`}
                          </p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Relationship */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Relationship *
            </label>
            <select
              name="relationship"
              value={formData.relationship}
              onChange={handleChange}
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

          {/* Primary Guardian Checkbox */}
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
              Set as primary guardian for this student
            </label>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 mb-2">ℹ️ About Linking</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• This parent will be able to view this student's grades and attendance</li>
              <li>• Primary guardians receive important notifications first</li>
              <li>• One parent can be linked to multiple students</li>
              <li>• One student can have multiple parents/guardians</li>
            </ul>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <button
              type="submit"
              disabled={submitting || !formData.student_id}
              className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {submitting ? 'Linking...' : 'Link Student'}
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
      </div>
    </div>
  );
}
