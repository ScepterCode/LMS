'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface Assessment {
  id: string;
  title: string;
  description?: string;
  subject_id?: string;
  class_id?: string;
  assessment_type_name?: string;
  subject_name?: string;
  class_name?: string;
  teacher_name?: string;
  assessment_date?: string;
  max_score: number;
  status: string;
  grades_count?: number;
}

interface AssessmentType {
  id: string;
  name: string;
  code: string;
  max_score: number;
  weight_percentage?: number;
}

interface Subject {
  id: string;
  name: string;
}

interface Class {
  id: string;
  name: string;
}

interface GradeConfig {
  id: string;
  grade_letter: string;
  min_score: number;
  max_score: number;
  grade_point?: number;
  remark?: string;
  is_passing: boolean;
}

export default function AssessmentsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const isTeacher = user?.role === 'teacher';
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [assessmentTypes, setAssessmentTypes] = useState<AssessmentType[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  // The class/subject pairs this teacher actually teaches - used to scope
  // the filter dropdowns and assessment list down from "every assessment
  // in the school" to "mine", since the backend only blocks mutations on
  // assessments outside a teacher's own subjects, not visibility of them.
  const [ownAssignments, setOwnAssignments] = useState<{ classId: string; subjectId: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedClass, setSelectedClass] = useState('');
  const [formData, setFormData] = useState({
    assessment_type_id: '',
    subject_id: '',
    class_id: '',
    title: '',
    description: '',
    assessment_date: '',
    max_score: 100
  });
  const [currentSessionId, setCurrentSessionId] = useState('');
  const [currentTermId, setCurrentTermId] = useState('');
  const [showTypesModal, setShowTypesModal] = useState(false);
  const [typeSubmitting, setTypeSubmitting] = useState(false);
  const [typeError, setTypeError] = useState('');
  const [typeFormData, setTypeFormData] = useState({
    name: '',
    code: '',
    max_score: 100,
    weight_percentage: 0,
  });
  const [gradeConfigs, setGradeConfigs] = useState<GradeConfig[]>([]);
  const [showGradeConfigsModal, setShowGradeConfigsModal] = useState(false);
  const [gradeConfigSubmitting, setGradeConfigSubmitting] = useState(false);
  const [gradeConfigError, setGradeConfigError] = useState('');
  const [gradeConfigFormData, setGradeConfigFormData] = useState({
    grade_letter: '',
    min_score: 0,
    max_score: 100,
    grade_point: 4,
    is_passing: true,
  });
  const isAdminOrBursar = user?.role === 'admin' || user?.role === 'system_admin' || user?.role === 'bursar';
  // Only true school admins can delete assessments - the backend rejects
  // system_admin/bursar the same as any other non-admin caller.
  const canDeleteAssessments = user?.role === 'admin';

  const [editingAssessment, setEditingAssessment] = useState<Assessment | null>(null);
  const [editFormData, setEditFormData] = useState({
    title: '',
    description: '',
    assessment_date: '',
    max_score: 100,
  });
  const [editError, setEditError] = useState('');
  const [editSubmitting, setEditSubmitting] = useState(false);

  useEffect(() => {
    if (isTeacher && user?.teacher_id) {
      fetchOwnAssignments();
    }
  }, [isTeacher, user?.teacher_id]);

  useEffect(() => {
    fetchData();
    fetchCurrentSessionAndTerm();
  }, [selectedSubject, selectedClass]);

  const fetchOwnAssignments = async () => {
    if (!user?.teacher_id) return;
    try {
      const res = await api.getTeacherClasses(user.teacher_id);
      const teacherClasses = (res.data as any[]) || [];
      const assignments: { classId: string; subjectId: string }[] = [];
      teacherClasses.forEach((cls) => {
        (cls.subjects || []).forEach((subject: any) => {
          assignments.push({ classId: cls.id, subjectId: subject.id });
        });
      });
      setOwnAssignments(assignments);
    } catch (error) {
      console.error('Error fetching own class/subject assignments:', error);
      setOwnAssignments([]);
    }
  };

  const fetchCurrentSessionAndTerm = async () => {
    try {
      const sessionsRes = await api.getSessions({ is_current: true });
      const sessions = sessionsRes.data as any[] | undefined;
      const currentSession = sessions?.[0];
      if (currentSession) {
        setCurrentSessionId(currentSession.id);

        const termsRes = await api.getTerms({ is_current: true, session_id: currentSession.id });
        const terms = termsRes.data as any[] | undefined;
        if (terms?.[0]) {
          setCurrentTermId(terms[0].id);
        }
      }
    } catch (error) {
      console.error('Error fetching current session/term:', error);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch assessments with filters
      let url = '/api/v1/grading/assessments';
      const params = new URLSearchParams();
      if (selectedSubject) params.append('subject_id', selectedSubject);
      if (selectedClass) params.append('class_id', selectedClass);
      if (params.toString()) url += `?${params.toString()}`;

      const [assessmentsRes, typesRes, subjectsRes, classesRes, gradeConfigsRes] = await Promise.all([
        api.get(url),
        api.get('/api/v1/grading/assessment-types'),
        api.get('/api/v1/subjects'),
        api.get('/api/v1/classes'),
        api.get('/api/v1/grading/grade-configs')
      ]);

      setAssessments(assessmentsRes.data ? (assessmentsRes.data as Assessment[]) : []);
      setAssessmentTypes(typesRes.data ? (typesRes.data as AssessmentType[]) : []);
      setSubjects(subjectsRes.data ? (subjectsRes.data as Subject[]) : []);
      setClasses(classesRes.data ? (classesRes.data as Class[]) : []);
      setGradeConfigs(gradeConfigsRes.data ? (gradeConfigsRes.data as GradeConfig[]) : []);
    } catch (error) {
      console.error('Error fetching data:', error);
      setAssessments([]);
      setAssessmentTypes([]);
      setSubjects([]);
      setClasses([]);
      setGradeConfigs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!currentSessionId || !currentTermId) {
      alert('No current academic session/term is set. Set one as current under Sessions & Terms first.');
      return;
    }

    try {
      const response = await api.post('/api/v1/grading/assessments', {
        ...formData,
        session_id: currentSessionId,
        term_id: currentTermId
      });

      if (response.error) {
        alert(response.error);
        return;
      }

      alert('Assessment created successfully!');
      setShowModal(false);
      setFormData({
        assessment_type_id: '',
        subject_id: '',
        class_id: '',
        title: '',
        description: '',
        assessment_date: '',
        max_score: 100
      });
      fetchData();
    } catch (error: any) {
      console.error('Error creating assessment:', error);
      alert('Failed to create assessment');
    }
  };

  const handleCreateType = async (e: React.FormEvent) => {
    e.preventDefault();
    setTypeError('');
    setTypeSubmitting(true);

    try {
      const response = await api.post('/api/v1/grading/assessment-types', typeFormData);
      if (response.error) {
        setTypeError(response.error);
        return;
      }
      setTypeFormData({ name: '', code: '', max_score: 100, weight_percentage: 0 });
      const typesRes = await api.get('/api/v1/grading/assessment-types');
      setAssessmentTypes(typesRes.data ? (typesRes.data as AssessmentType[]) : []);
    } catch (error) {
      console.error('Error creating assessment type:', error);
      setTypeError('Failed to create assessment type');
    } finally {
      setTypeSubmitting(false);
    }
  };

  const handleCreateGradeConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setGradeConfigError('');
    setGradeConfigSubmitting(true);

    try {
      const response = await api.post('/api/v1/grading/grade-configs', gradeConfigFormData);
      if (response.error) {
        setGradeConfigError(response.error);
        return;
      }
      setGradeConfigFormData({ grade_letter: '', min_score: 0, max_score: 100, grade_point: 4, is_passing: true });
      const res = await api.get('/api/v1/grading/grade-configs');
      setGradeConfigs(res.data ? (res.data as GradeConfig[]) : []);
    } catch (error) {
      console.error('Error creating grade band:', error);
      setGradeConfigError('Failed to create grade band');
    } finally {
      setGradeConfigSubmitting(false);
    }
  };

  const handleDeleteGradeConfig = async (id: string) => {
    if (!confirm('Delete this grade band?')) return;
    try {
      const response = await api.delete(`/api/v1/grading/grade-configs/${id}`);
      if (response.error) {
        alert(response.error);
        return;
      }
      setGradeConfigs(gradeConfigs.filter((g) => g.id !== id));
    } catch (error) {
      console.error('Error deleting grade band:', error);
      alert('Failed to delete grade band');
    }
  };

  const handlePublish = async (id: string) => {
    if (!confirm('Are you sure you want to publish this assessment? Students will be able to see it.')) {
      return;
    }

    try {
      const response = await api.post(`/api/v1/grading/assessments/${id}/publish`);
      if (response.error) {
        alert(response.error);
        return;
      }
      alert('Assessment published successfully!');
      fetchData();
    } catch (error: any) {
      console.error('Error publishing assessment:', error);
      alert('Failed to publish assessment');
    }
  };

  const openEditModal = (assessment: Assessment) => {
    setEditingAssessment(assessment);
    setEditFormData({
      title: assessment.title,
      description: assessment.description || '',
      assessment_date: assessment.assessment_date || '',
      max_score: assessment.max_score,
    });
    setEditError('');
  };

  const handleUpdateAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAssessment) return;

    setEditError('');
    setEditSubmitting(true);

    try {
      const response = await api.put(`/api/v1/grading/assessments/${editingAssessment.id}`, editFormData);
      if (response.error) {
        setEditError(response.error);
        return;
      }
      setEditingAssessment(null);
      fetchData();
    } catch (error) {
      console.error('Error updating assessment:', error);
      setEditError('Failed to update assessment');
    } finally {
      setEditSubmitting(false);
    }
  };

  const handleDeleteAssessment = async (assessment: Assessment) => {
    if (!confirm(`Delete "${assessment.title}"? This cannot be undone.`)) return;

    try {
      const response = await api.delete(`/api/v1/grading/assessments/${assessment.id}`);
      if (response.error) {
        alert(response.error);
        return;
      }
      setAssessments((prev) => prev.filter((a) => a.id !== assessment.id));
    } catch (error) {
      console.error('Error deleting assessment:', error);
      alert('Failed to delete assessment');
    }
  };

  // For a teacher, narrow every list down to their own class/subject
  // assignments. Admins see everything, unfiltered, as before.
  const ownClassIds = new Set(ownAssignments.map((a) => a.classId));
  const ownSubjectIds = new Set(ownAssignments.map((a) => a.subjectId));
  const ownPairs = new Set(ownAssignments.map((a) => `${a.classId}|${a.subjectId}`));

  const visibleSubjects = isTeacher ? subjects.filter((s) => ownSubjectIds.has(s.id)) : subjects;
  const visibleClasses = isTeacher ? classes.filter((c) => ownClassIds.has(c.id)) : classes;
  const visibleAssessments = isTeacher
    ? assessments.filter((a) => a.class_id && a.subject_id && ownPairs.has(`${a.class_id}|${a.subject_id}`))
    : assessments;

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-800',
      published: 'bg-blue-100 text-blue-800',
      graded: 'bg-green-100 text-green-800',
      approved: 'bg-purple-100 text-purple-800',
      locked: 'bg-red-100 text-red-800'
    };
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading assessments...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Assessments</h1>
            <p className="text-gray-600 mt-1">Manage assessments and examinations</p>
          </div>
          <div className="flex gap-2">
            {isAdminOrBursar && (
              <>
                <button
                  onClick={() => setShowGradeConfigsModal(true)}
                  className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50"
                >
                  Manage Grade Bands
                </button>
                <button
                  onClick={() => setShowTypesModal(true)}
                  className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50"
                >
                  Manage Types
                </button>
              </>
            )}
            <button
              onClick={() => setShowModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Create Assessment
            </button>
          </div>
        </div>

        {assessmentTypes.length === 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
            No assessment types have been set up yet, so assessments can't be created.{' '}
            {isAdminOrBursar ? (
              <button onClick={() => setShowTypesModal(true)} className="font-medium underline">
                Create one now
              </button>
            ) : (
              'Ask your school admin to set one up under Manage Types.'
            )}
          </div>
        )}

        {gradeConfigs.length === 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
            No grade bands are configured, so every score will show as grade "F" on report cards.{' '}
            {isAdminOrBursar ? (
              <button onClick={() => setShowGradeConfigsModal(true)} className="font-medium underline">
                Set up grade bands now
              </button>
            ) : (
              'Ask your school admin to set these up under Manage Grade Bands.'
            )}
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Subject</label>
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Subjects</option>
                {visibleSubjects.map(subject => (
                  <option key={subject.id} value={subject.id}>{subject.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Class</label>
              <select
                value={selectedClass}
                onChange={(e) => setSelectedClass(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Classes</option>
                {visibleClasses.map(cls => (
                  <option key={cls.id} value={cls.id}>{cls.name}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => {
                  setSelectedSubject('');
                  setSelectedClass('');
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Assessments List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Class</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grades</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {visibleAssessments.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                    No assessments found. Create your first assessment to get started.
                  </td>
                </tr>
              ) : (
                visibleAssessments.map((assessment) => (
                  <tr key={assessment.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{assessment.title}</div>
                      <div className="text-sm text-gray-500">Max Score: {assessment.max_score}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {assessment.assessment_type_name || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {assessment.subject_name || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {assessment.class_name || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {assessment.assessment_date || 'Not set'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(assessment.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {assessment.grades_count || 0} grades
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      {assessment.status === 'draft' && (
                        <button
                          onClick={() => handlePublish(assessment.id)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Publish
                        </button>
                      )}
                      <button
                        onClick={() => router.push(`/dashboard/grading/entry?assessment=${assessment.id}`)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Enter Grades
                      </button>
                      {assessment.status !== 'locked' && (
                        <button
                          onClick={() => openEditModal(assessment)}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          Edit
                        </button>
                      )}
                      {canDeleteAssessments && !assessment.grades_count && (
                        <button
                          onClick={() => handleDeleteAssessment(assessment)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Assessment Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Create New Assessment</h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Assessment Type *</label>
                  <select
                    required
                    value={formData.assessment_type_id}
                    onChange={(e) => setFormData({...formData, assessment_type_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="">Select type</option>
                    {assessmentTypes.map(type => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subject *</label>
                  <select
                    required
                    value={formData.subject_id}
                    onChange={(e) => setFormData({...formData, subject_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="">Select subject</option>
                    {visibleSubjects.map(subject => (
                      <option key={subject.id} value={subject.id}>{subject.name}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Class *</label>
                  <select
                    required
                    value={formData.class_id}
                    onChange={(e) => setFormData({...formData, class_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="">Select class</option>
                    {visibleClasses.map(cls => (
                      <option key={cls.id} value={cls.id}>{cls.name}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Assessment Date</label>
                  <input
                    type="date"
                    value={formData.assessment_date}
                    onChange={(e) => setFormData({...formData, assessment_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="e.g., First Term CA Test"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  rows={3}
                  placeholder="Optional description"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Maximum Score *</label>
                <input
                  type="number"
                  required
                  min="1"
                  max="100"
                  value={formData.max_score}
                  onChange={(e) => setFormData({...formData, max_score: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
                >
                  Create Assessment
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-gray-200 text-gray-800 py-2 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Manage Assessment Types Modal */}
      {showTypesModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Assessment Types</h3>
                <p className="text-sm text-gray-600 mt-1">e.g. Continuous Assessment, Exam, Assignment</p>
              </div>
              <button onClick={() => setShowTypesModal(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div className="border border-gray-200 rounded-lg divide-y max-h-48 overflow-y-auto">
                {assessmentTypes.length === 0 ? (
                  <div className="p-4 text-center text-gray-500 text-sm">No assessment types yet</div>
                ) : (
                  assessmentTypes.map((type) => (
                    <div key={type.id} className="flex items-center justify-between px-4 py-2">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{type.name}</p>
                        <p className="text-xs text-gray-500">{type.code}</p>
                      </div>
                      <p className="text-xs text-gray-500">
                        Max {type.max_score} &middot; {type.weight_percentage ?? 0}% weight
                      </p>
                    </div>
                  ))
                )}
              </div>

              <form onSubmit={handleCreateType} className="space-y-4 border-t pt-4">
                <h4 className="text-sm font-semibold text-gray-900">Add a new type</h4>

                {typeError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded text-sm">
                    {typeError}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                    <input
                      type="text"
                      required
                      value={typeFormData.name}
                      onChange={(e) => setTypeFormData({ ...typeFormData, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="e.g., Continuous Assessment"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Code *</label>
                    <input
                      type="text"
                      required
                      value={typeFormData.code}
                      onChange={(e) => setTypeFormData({ ...typeFormData, code: e.target.value.toUpperCase() })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="e.g., CA"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Score *</label>
                    <input
                      type="number"
                      required
                      min="1"
                      max="999"
                      value={typeFormData.max_score}
                      onChange={(e) => setTypeFormData({ ...typeFormData, max_score: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Weight % *</label>
                    <input
                      type="number"
                      required
                      min="0"
                      max="100"
                      value={typeFormData.weight_percentage}
                      onChange={(e) => setTypeFormData({ ...typeFormData, weight_percentage: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  Weight % is how much this type counts toward a subject's final score (e.g. CA 30% + Exam 70%).
                </p>

                <button
                  type="submit"
                  disabled={typeSubmitting}
                  className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {typeSubmitting ? 'Adding...' : 'Add Assessment Type'}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Manage Grade Bands Modal */}
      {showGradeConfigsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Grade Bands</h3>
                <p className="text-sm text-gray-600 mt-1">e.g. A = 70-100, B = 60-69</p>
              </div>
              <button onClick={() => setShowGradeConfigsModal(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div className="border border-gray-200 rounded-lg divide-y max-h-48 overflow-y-auto">
                {gradeConfigs.length === 0 ? (
                  <div className="p-4 text-center text-gray-500 text-sm">No grade bands yet</div>
                ) : (
                  gradeConfigs.map((g) => (
                    <div key={g.id} className="flex items-center justify-between px-4 py-2">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {g.grade_letter} {!g.is_passing && <span className="text-red-600">(fail)</span>}
                        </p>
                        <p className="text-xs text-gray-500">
                          {g.min_score}&ndash;{g.max_score}
                          {g.grade_point != null ? ` · ${g.grade_point} pts` : ''}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteGradeConfig(g.id)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Delete
                      </button>
                    </div>
                  ))
                )}
              </div>

              <form onSubmit={handleCreateGradeConfig} className="space-y-4 border-t pt-4">
                <h4 className="text-sm font-semibold text-gray-900">Add a grade band</h4>

                {gradeConfigError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded text-sm">
                    {gradeConfigError}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Letter *</label>
                    <input
                      type="text"
                      required
                      maxLength={5}
                      value={gradeConfigFormData.grade_letter}
                      onChange={(e) => setGradeConfigFormData({ ...gradeConfigFormData, grade_letter: e.target.value.toUpperCase() })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="e.g., A"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Grade Point</label>
                    <input
                      type="number"
                      min="0"
                      max="5"
                      step="0.1"
                      value={gradeConfigFormData.grade_point}
                      onChange={(e) => setGradeConfigFormData({ ...gradeConfigFormData, grade_point: parseFloat(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Min Score *</label>
                    <input
                      type="number"
                      required
                      min="0"
                      max="100"
                      value={gradeConfigFormData.min_score}
                      onChange={(e) => setGradeConfigFormData({ ...gradeConfigFormData, min_score: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Score *</label>
                    <input
                      type="number"
                      required
                      min="0"
                      max="100"
                      value={gradeConfigFormData.max_score}
                      onChange={(e) => setGradeConfigFormData({ ...gradeConfigFormData, max_score: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_passing"
                    checked={gradeConfigFormData.is_passing}
                    onChange={(e) => setGradeConfigFormData({ ...gradeConfigFormData, is_passing: e.target.checked })}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                  />
                  <label htmlFor="is_passing" className="ml-2 text-sm text-gray-700">
                    This is a passing grade
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={gradeConfigSubmitting}
                  className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {gradeConfigSubmitting ? 'Adding...' : 'Add Grade Band'}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Assessment Modal */}
      {editingAssessment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Edit Assessment</h2>
            <p className="text-sm text-gray-500 mb-4">
              {editingAssessment.subject_name} &middot; {editingAssessment.class_name}
              <span className="block text-xs mt-1">Subject, class, and type can't be changed after creation.</span>
            </p>

            <form onSubmit={handleUpdateAssessment} className="space-y-4">
              {editError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded text-sm">
                  {editError}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                <input
                  type="text"
                  required
                  value={editFormData.title}
                  onChange={(e) => setEditFormData({ ...editFormData, title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={editFormData.description}
                  onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Assessment Date</label>
                  <input
                    type="date"
                    value={editFormData.assessment_date}
                    onChange={(e) => setEditFormData({ ...editFormData, assessment_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Maximum Score *</label>
                  <input
                    type="number"
                    required
                    min="1"
                    max="999"
                    value={editFormData.max_score}
                    onChange={(e) => setEditFormData({ ...editFormData, max_score: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={editSubmitting}
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {editSubmitting ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  type="button"
                  onClick={() => setEditingAssessment(null)}
                  className="flex-1 bg-gray-200 text-gray-800 py-2 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
