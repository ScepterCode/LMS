'use client';

import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card } from '@/components/ui/Card';

interface GuideStep {
  title: string;
  description: string;
  actionLabel: string;
  actionUrl: string;
}

const SETUP_STEPS: GuideStep[] = [
  {
    title: '1. Create an Academic Session',
    description:
      'Set up the current academic year (e.g. 2025/2026) and mark it as current. Terms, classes, and attendance are all scoped to a session.',
    actionLabel: 'Go to Sessions & Terms',
    actionUrl: '/dashboard/academic',
  },
  {
    title: '2. Add Subjects',
    description: 'Create the subjects taught at your school (e.g. Mathematics, English Language).',
    actionLabel: 'Go to Subjects',
    actionUrl: '/dashboard/academic?tab=subjects',
  },
  {
    title: '3. Create Classes',
    description: 'Set up classes (e.g. JSS 1, SS 2) and attach the subjects each one offers.',
    actionLabel: 'Go to Classes',
    actionUrl: '/dashboard/academic?tab=classes',
  },
  {
    title: '4. Add Teachers',
    description:
      'Register teacher accounts, then assign each one to a class and subject under Teacher Assignments. Check "Designate as Form Teacher" for a class\'s homeroom teacher.',
    actionLabel: 'Go to Teachers',
    actionUrl: '/dashboard/teachers',
  },
  {
    title: '5. Enroll Students',
    description: 'Add student records and enroll them into a class for the current session.',
    actionLabel: 'Go to Students',
    actionUrl: '/dashboard/students',
  },
];

const KEY_AREAS: GuideStep[] = [
  {
    title: 'Assessments & Grading',
    description:
      'Define assessment types (e.g. CA, Exam) with score weights and grade bands under Manage Types / Manage Grade Bands before entering scores.',
    actionLabel: 'Go to Assessments',
    actionUrl: '/dashboard/grading/assessments',
  },
  {
    title: 'Report Cards',
    description:
      'Generate report cards once scores are entered. Regenerating an existing report card updates it in place with the latest scores. Publish a report card to make it visible to parents.',
    actionLabel: 'Go to Report Cards',
    actionUrl: '/dashboard/grading/reports',
  },
  {
    title: 'Attendance',
    description: 'Form teachers mark daily attendance for their class and can view attendance summaries and leave requests.',
    actionLabel: 'Go to Attendance',
    actionUrl: '/dashboard/attendance/mark',
  },
  {
    title: 'Fees & Payments',
    description: 'Set up fee categories, assign fees to students, and record payments.',
    actionLabel: 'Go to Fees',
    actionUrl: '/dashboard/fees',
  },
];

const ROLES: { role: string; description: string }[] = [
  { role: 'Admin', description: 'Full access to a school\'s classes, staff, students, finances, and settings.' },
  { role: 'Dean', description: 'Academic and staff/student oversight - no access to finance or school settings.' },
  { role: 'Registrar', description: 'Admissions and enrollment only - adding students and managing class enrollment.' },
  { role: 'Teacher', description: 'Manages assigned subjects and classes. A form teacher additionally marks attendance, adds remarks, and sends report cards for their own class.' },
  { role: 'Bursar', description: 'Manages fees, payments, and financial reports.' },
  { role: 'Parent', description: 'Views their linked children\'s published report cards and attendance.' },
];

export default function HelpPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <PageHeader
          title="Setup Guide & Help"
          subtitle="A quick walkthrough of getting your school set up and finding your way around"
        />

        <div className="space-y-6">
          <Card title="Initial Setup" subtitle="Complete these in order when setting up a new school">
            <div className="space-y-4">
              {SETUP_STEPS.map((step) => (
                <div key={step.title} className="flex items-start justify-between gap-4 pb-4 border-b border-gray-100 last:border-0 last:pb-0">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{step.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                  </div>
                  <Link
                    href={step.actionUrl}
                    className="shrink-0 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors whitespace-nowrap"
                  >
                    {step.actionLabel}
                  </Link>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Key Areas" subtitle="Where to go for day-to-day tasks">
            <div className="space-y-4">
              {KEY_AREAS.map((area) => (
                <div key={area.title} className="flex items-start justify-between gap-4 pb-4 border-b border-gray-100 last:border-0 last:pb-0">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{area.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{area.description}</p>
                  </div>
                  <Link
                    href={area.actionUrl}
                    className="shrink-0 px-3 py-1.5 border border-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-50 transition-colors whitespace-nowrap"
                  >
                    {area.actionLabel}
                  </Link>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Staff Roles" subtitle="What each account type can do">
            <div className="divide-y divide-gray-100">
              {ROLES.map((r) => (
                <div key={r.role} className="py-3 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4">
                  <span className="text-sm font-medium text-gray-900 sm:w-28 shrink-0">{r.role}</span>
                  <span className="text-sm text-gray-600">{r.description}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
