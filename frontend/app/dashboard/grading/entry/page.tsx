'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import { api } from '@/lib/api';

interface Assessment {
  id: string;
  title: string;
  max_score: number;
  assessment_type_name?: string;
  subject_name?: string;
  class_name?: string;
}

interface Student {
  id: string;
  admission_number: string;
  first_name: string;
  last_name: string;
}

interface GradeEntry {
  student_id: string;
  score: number | null;
  remark?: string;
  is_absent: boolean;
  is_excused: boolean;
}

function GradeEntryContent() {
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get('assessment');
  
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [grades, setGrades] = useState<Record<string, GradeEntry>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState(assessmentId || '');
  const [assessments, setAssessments] = useState<Assessment[]>([]);

  useEffect(() => {
    fetchAssessments();
  }, []);

  useEffect(() => {
    if (selectedAssessment) {
      fetchAssessmentData();
    }
  }, [selectedAssessment]);

  const fetchAssessments = async () => {
    try {
      const response = await api.get('/api/v1/grading/assessments?status=published');
      setAssessments(response.data ? (response.data as Assessment[]) : []);
      if (assessmentId) {
        setSelectedAssessment(assessmentId);
      }
    } catch (error) {
      console.error('Error fetching assessments:', error);
      setAssessments([]);
    }
  };

  const fetchAssessmentData = async () => {
    setLoading(true);
    try {
      // Fetch assessment details
      const assessmentRes = await api.get(`/api/v1/grading/assessments/${selectedAssessment}`);
      if (!assessmentRes.data) {
        throw new Error('Assessment not found');
      }
      setAssessment(assessmentRes.data);
      
      // Fetch students in the class
      const studentsRes = await api.get(`/api/v1/classes/${assessmentRes.data.class_id}/students`);
      const studentsData = studentsRes.data ? (studentsRes.data as Student[]) : [];
      setStudents(studentsData);
      
      // Fetch existing grades
      const gradesRes = await api.get(`/api/v1/grading/assessments/${selectedAssessment}/grades`);
      const gradesData = gradesRes.data || [];
      
      // Initialize grades state
      const gradesMap: Record<string, GradeEntry> = {};
      studentsData.forEach((student: Student) => {
        const existingGrade = gradesData.find((g: any) => g.student_id === student.id);
        gradesMap[student.id] = {
          student_id: student.id,
          score: existingGrade?.score || null,
          remark: existingGrade?.remark || '',
          is_absent: existingGrade?.is_absent || false,
          is_excused: existingGrade?.is_excused || false
        };
      });
      setGrades(gradesMap);
      
    } catch (error) {
      console.error('Error fetching assessment data:', error);
      setAssessment(null);
      setStudents([]);
      setGrades({});
    } finally {
      setLoading(false);
    }
  };

  const handleScoreChange = (studentId: string, score: string) => {
    const numScore = score === '' ? null : parseFloat(score);
    setGrades({
      ...grades,
      [studentId]: {
        ...grades[studentId],
        score: numScore,
        is_absent: false
      }
    });
  };

  const handleAbsentToggle = (studentId: string) => {
    setGrades({
      ...grades,
      [studentId]: {
        ...grades[studentId],
        is_absent: !grades[studentId].is_absent,
        score: grades[studentId].is_absent ? null : grades[studentId].score
      }
    });
  };

  const handleSaveGrades = async () => {
    if (!selectedAssessment) {
      alert('Please select an assessment');
      return;
    }

    // Validate scores
    for (const grade of Object.values(grades)) {
      if (!grade.is_absent && grade.score !== null) {
        if (grade.score < 0 || grade.score > assessment!.max_score) {
          alert(`Score must be between 0 and ${assessment!.max_score}`);
          return;
        }
      }
    }

    try {
      setSaving(true);
      
      const gradesArray = Object.values(grades);
      
      await api.post('/api/v1/grading/grades/bulk', {
        assessment_id: selectedAssessment,
        grades: gradesArray
      });
      
      alert('Grades saved successfully!');
    } catch (error: any) {
      console.error('Error saving grades:', error);
      alert(error.response?.data?.detail || 'Failed to save grades');
    } finally {
      setSaving(false);
    }
  };

  if (!selectedAssessment) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Grade Entry</h1>
            <p className="text-gray-600 mt-1">Select an assessment to enter grades</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Assessment</label>
            <select
              value={selectedAssessment}
              onChange={(e) => setSelectedAssessment(e.target.value)}
              className="w-full max-w-2xl px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Choose an assessment...</option>
              {assessments.map(a => (
                <option key={a.id} value={a.id}>
                  {a.title} - {a.subject_name} ({a.class_name})
                </option>
              ))}
            </select>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Grade Entry</h1>
            <p className="text-gray-600 mt-1">Enter grades for {assessment?.title}</p>
            <div className="mt-2 space-y-1 text-sm text-gray-600">
              <p><strong>Subject:</strong> {assessment?.subject_name}</p>
              <p><strong>Class:</strong> {assessment?.class_name}</p>
              <p><strong>Max Score:</strong> {assessment?.max_score}</p>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setSelectedAssessment('')}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Change Assessment
            </button>
            <button
              onClick={handleSaveGrades}
              disabled={saving}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save All Grades'}
            </button>
          </div>
        </div>

        {/* Grade Entry Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Admission No.</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score (/{assessment?.max_score})</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Absent</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Remark</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {students.map((student, index) => {
                  const grade = grades[student.id];
                  const isAbsent = grade?.is_absent || false;
                  
                  return (
                    <tr key={student.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {student.admission_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {student.first_name} {student.last_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          min="0"
                          max={assessment?.max_score}
                          step="0.01"
                          value={grade?.score ?? ''}
                          onChange={(e) => handleScoreChange(student.id, e.target.value)}
                          disabled={isAbsent}
                          className="w-24 px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
                          placeholder="Score"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="checkbox"
                          checked={isAbsent}
                          onChange={() => handleAbsentToggle(student.id)}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                      </td>
                      <td className="px-6 py-4">
                        <input
                          type="text"
                          value={grade?.remark || ''}
                          onChange={(e) => setGrades({
                            ...grades,
                            [student.id]: {...grades[student.id], remark: e.target.value}
                          })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          placeholder="Optional remark"
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Total Students</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{students.length}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Grades Entered</div>
            <div className="text-2xl font-bold text-green-600 mt-1">
              {Object.values(grades).filter(g => g.score !== null || g.is_absent).length}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Absent</div>
            <div className="text-2xl font-bold text-yellow-600 mt-1">
              {Object.values(grades).filter(g => g.is_absent).length}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Pending</div>
            <div className="text-2xl font-bold text-red-600 mt-1">
              {Object.values(grades).filter(g => g.score === null && !g.is_absent).length}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}


export default function GradeEntryPage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    }>
      <GradeEntryContent />
    </Suspense>
  );
}
