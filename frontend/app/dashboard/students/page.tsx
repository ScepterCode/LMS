'use client';

import { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { PageHeader } from '@/components/ui/PageHeader';
import { LinkButton, Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

interface Student {
  id: string;
  admission_number: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  full_name: string;
  date_of_birth: string;
  gender: string;
  email?: string;
  phone?: string;
  current_class_id?: string;
  class_name?: string;
  status: string;
  age?: number;
  created_at: string;
}

interface Class {
  id: string;
  name: string;
  level: string;
}

function StudentsPageContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const [students, setStudents] = useState<Student[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  // Pre-filter when arriving from a "View Students" link (e.g. My Classes)
  // that names a specific class via ?class_id=.
  const [filterClass, setFilterClass] = useState(() => searchParams.get('class_id') || '');
  const [filterStatus, setFilterStatus] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [isFormTeacher, setIsFormTeacher] = useState(false);
  const [formClassInfo, setFormClassInfo] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, [filterClass, filterStatus, searchTerm]);

  useEffect(() => {
    checkFormTeacherStatus();
  }, [user]);

  const checkFormTeacherStatus = async () => {
    if (user?.role === 'teacher' && user?.teacher_id) {
      try {
        const response = await api.getTeacherClasses(user.teacher_id);
        const classes = (response.data as any[]) || [];
        const formClass = classes.find((c: any) => c.is_form_teacher);
        if (formClass) {
          setIsFormTeacher(true);
          setFormClassInfo(formClass);
        }
      } catch (error) {
        console.error('Error checking form teacher status:', error);
        setIsFormTeacher(false);
        setFormClassInfo(null);
      }
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      // Load students
      const studentsResponse = await api.getStudents({
        search: searchTerm || undefined,
        class_id: filterClass || undefined,
        status: filterStatus || undefined,
        limit: 100,
      });
      
      setStudents(studentsResponse.data ? (studentsResponse.data as Student[]) : []);

      // Load classes for filter
      const classesResponse = await api.getClasses();
      setClasses(classesResponse.data ? (classesResponse.data as Class[]) : []);
    } catch (error) {
      console.error('Error loading data:', error);
      setStudents([]);
      setClasses([]);
    } finally {
      setLoading(false);
    }
  };

  const statusTone = (status: string) => {
    const map: Record<string, 'success' | 'info' | 'danger' | 'neutral'> = {
      active: 'success',
      graduated: 'info',
      suspended: 'danger',
      withdrawn: 'neutral',
    };
    return map[status] || 'neutral';
  };

  return (
    <DashboardLayout>
      <PageHeader
        title="Students"
        subtitle="Manage student records and information"
        actions={<LinkButton href="/dashboard/students/add">+ Add Student</LinkButton>}
      />

      {/* Form Teacher Quick Access */}
      {isFormTeacher && formClassInfo && (
        <div className="mb-6 bg-brand-50 border border-brand-100 rounded-lg p-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 bg-brand-600 text-white text-xs font-semibold rounded">
                  FORM TEACHER
                </span>
                <h3 className="text-lg font-semibold text-gray-900">{formClassInfo.name}</h3>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                You are the form teacher of this class. Quick actions available.
              </p>
            </div>
            <div className="flex gap-2">
              <LinkButton href={`/dashboard/students/add?class=${formClassInfo.id}`} size="sm">
                + Add Student to My Class
              </LinkButton>
              <Button variant="secondary" size="sm" onClick={() => setFilterClass(formClassInfo.id)}>
                View My Class Students
              </Button>
            </div>
          </div>
        </div>
      )}

          {/* Filters */}
          <Card className="mb-6">
            <div className="grid md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Search
                </label>
                <input
                  type="text"
                  placeholder="Name or admission number..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Class
                </label>
                <select
                  value={filterClass}
                  onChange={(e) => setFilterClass(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">All Classes</option>
                  {classes.map((cls) => (
                    <option key={cls.id} value={cls.id}>
                      {cls.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">All Status</option>
                  <option value="active">Active</option>
                  <option value="graduated">Graduated</option>
                  <option value="suspended">Suspended</option>
                  <option value="withdrawn">Withdrawn</option>
                </select>
              </div>
              <div className="flex items-end">
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={() => {
                    setSearchTerm('');
                    setFilterClass('');
                    setFilterStatus('');
                  }}
                >
                  Clear Filters
                </Button>
              </div>
            </div>
          </Card>

          {/* Loading */}
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
            </div>
          ) : students.length === 0 ? (
            <Card className="p-12 text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No students found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by adding your first student.
              </p>
              <div className="mt-6">
                <LinkButton href="/dashboard/students/add">+ Add Student</LinkButton>
              </div>
            </Card>
          ) : (
            <>
              {/* Student Count */}
              <div className="mb-4 text-sm text-gray-500">
                Showing {students.length} student{students.length !== 1 ? 's' : ''}
              </div>

              {/* Students Table */}
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Admission No.
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Gender
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Age
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Class
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {students.map((student) => (
                      <tr key={student.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {student.admission_number}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{student.full_name}</div>
                          {student.email && (
                            <div className="text-sm text-gray-500">{student.email}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {student.gender}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {student.age || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {student.class_name || 'Not assigned'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge tone={statusTone(student.status)}>{student.status}</Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link
                            href={`/dashboard/students/${student.id}`}
                            className="text-brand-600 hover:text-brand-800 mr-4"
                          >
                            View
                          </Link>
                          <Link
                            href={`/dashboard/students/${student.id}/edit`}
                            className="text-gray-600 hover:text-gray-900"
                          >
                            Edit
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                </div>
              </div>
            </>
          )}
    </DashboardLayout>
  );
}

export default function StudentsPage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    }>
      <StudentsPageContent />
    </Suspense>
  );
}
