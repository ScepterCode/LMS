'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  required: boolean;
  action: string;
  actionUrl: string;
}

export default function OnboardingChecklist() {
  const [steps, setSteps] = useState<OnboardingStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [show, setShow] = useState(true);
  const [allComplete, setAllComplete] = useState(false);

  useEffect(() => {
    checkOnboardingStatus();
  }, []);

  const checkOnboardingStatus = async () => {
    try {
      setLoading(true);

      // Check each requirement
      const [sessions, classes, subjects, students, teachers] = await Promise.all([
        api.getSessions(),
        api.getClasses(),
        api.getSubjects(),
        api.getStudents(),
        api.getTeachers(),
      ]);

      const currentSession = (sessions.data as any[])?.find((s: any) => s.is_current);
      const hasClasses = (classes.data as any[])?.length > 0;
      const hasSubjects = (subjects.data as any[])?.length > 0;
      const hasStudents = (students.data as any[])?.length > 0;
      const hasTeachers = (teachers.data as any[])?.length > 0;

      const onboardingSteps: OnboardingStep[] = [
        {
          id: 'session',
          title: 'Create Academic Session',
          description: 'Set up the current academic year (e.g., 2024/2025)',
          completed: !!currentSession,
          required: true,
          action: 'Create Session',
          actionUrl: '/dashboard/academic',
        },
        {
          id: 'subjects',
          title: 'Add Subjects',
          description: 'Create subjects (e.g., Math, English, Science)',
          completed: hasSubjects,
          required: true,
          action: 'Add Subjects',
          actionUrl: '/dashboard/academic',
        },
        {
          id: 'classes',
          title: 'Create Classes',
          description: 'Set up classes (e.g., JSS 1, SS 2)',
          completed: hasClasses,
          required: true,
          action: 'Create Classes',
          actionUrl: '/dashboard/academic',
        },
        {
          id: 'teachers',
          title: 'Add Teachers',
          description: 'Register teacher accounts and profiles',
          completed: hasTeachers,
          required: false,
          action: 'Add Teachers',
          actionUrl: '/dashboard/teachers',
        },
        {
          id: 'students',
          title: 'Enroll Students',
          description: 'Add student records with classes',
          completed: hasStudents,
          required: false,
          action: 'Add Students',
          actionUrl: '/dashboard/students',
        },
      ];

      setSteps(onboardingSteps);
      const requiredComplete = onboardingSteps
        .filter(s => s.required)
        .every(s => s.completed);
      setAllComplete(requiredComplete);

      // Auto-hide if all required steps are complete
      if (requiredComplete) {
        const hidden = localStorage.getItem('onboarding_hidden');
        if (hidden === 'true') {
          setShow(false);
        }
      }
    } catch (error) {
      console.error('Error checking onboarding status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = () => {
    localStorage.setItem('onboarding_hidden', 'true');
    setShow(false);
  };

  const completedCount = steps.filter(s => s.completed).length;
  const totalCount = steps.length;
  const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  if (!show || loading) return null;

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-6 shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0 mt-1">
            {allComplete ? (
              <span className="text-2xl leading-none text-green-600">✓</span>
            ) : (
              <span className="text-2xl leading-none text-blue-600">!</span>
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {allComplete ? '✅ Setup Complete!' : '🚀 Getting Started'}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {allComplete
                ? 'Your LMS is ready to use. You can dismiss this checklist.'
                : 'Complete these steps to start using the LMS effectively.'}
            </p>
          </div>
        </div>
        <button
          onClick={handleDismiss}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          title="Dismiss"
          aria-label="Dismiss"
        >
          <span className="text-lg leading-none">×</span>
        </button>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
          <span>Progress</span>
          <span className="font-medium">
            {completedCount} of {totalCount} completed
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-600 to-indigo-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={`flex items-center justify-between p-3 rounded-lg transition-all ${
              step.completed
                ? 'bg-green-50 border border-green-200'
                : 'bg-white border border-gray-200 hover:border-blue-300'
            }`}
          >
            <div className="flex items-center space-x-3 flex-1">
              <div className="flex-shrink-0">
                {step.completed ? (
                  <span className="text-lg leading-none text-green-600">✓</span>
                ) : (
                  <div className="relative flex items-center justify-center h-5 w-5">
                    <span className="text-lg leading-none text-gray-400">○</span>
                    <span className="absolute inset-0 flex items-center justify-center text-xs text-gray-600 font-medium">
                      {index + 1}
                    </span>
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <h4
                    className={`text-sm font-medium ${
                      step.completed ? 'text-green-900' : 'text-gray-900'
                    }`}
                  >
                    {step.title}
                  </h4>
                  {step.required && !step.completed && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                      Required
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-600 mt-0.5">{step.description}</p>
              </div>
            </div>
            {!step.completed && (
              <a
                href={step.actionUrl}
                className="flex items-center space-x-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors ml-3 flex-shrink-0"
              >
                <span>{step.action}</span>
                <span className="text-sm leading-none">›</span>
              </a>
            )}
          </div>
        ))}
      </div>

      {/* Help Link */}
      <div className="mt-4 pt-4 border-t border-blue-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">
            Need help with setup?
          </span>
          <a
            href="/dashboard/help"
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            View Setup Guide →
          </a>
        </div>
      </div>
    </div>
  );
}
