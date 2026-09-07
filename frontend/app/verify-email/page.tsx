'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';

function VerifyEmail() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token') || '';
  const [state, setState] = useState<'checking' | 'ok' | 'error'>('checking');
  const [message, setMessage] = useState('');
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    if (!token) {
      setState('error');
      setMessage('This link is missing its verification token.');
      return;
    }

    api.verifyEmail(token).then((res) => {
      if (res.error) {
        setState('error');
        setMessage(res.error);
      } else {
        setState('ok');
        setMessage((res.data as { message: string })?.message || 'Your email address is verified.');
      }
    });
  }, [token]);

  return (
    <div className="text-center space-y-4">
      {state === 'checking' && (
        <>
          <div className="mx-auto animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
          <p className="text-sm text-gray-600">Verifying your email…</p>
        </>
      )}

      {state === 'ok' && (
        <>
          <div className="mx-auto w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-gray-900 font-medium">Email verified</p>
          <p className="text-sm text-gray-600">{message}</p>
          <Link href="/login" className="inline-block text-blue-600 hover:text-blue-700 font-medium text-sm">
            Continue to sign in
          </Link>
        </>
      )}

      {state === 'error' && (
        <>
          <p className="text-gray-900 font-medium">Couldn&apos;t verify this link</p>
          <p className="text-sm text-gray-600">{message}</p>
          <p className="text-sm text-gray-500">
            You can still sign in — verifying your email is optional.
          </p>
          <Link href="/login" className="inline-block text-blue-600 hover:text-blue-700 font-medium text-sm">
            Go to sign in
          </Link>
        </>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <Link href="/">
            <h1 className="text-3xl font-bold text-blue-600 mb-2">Learnlyf</h1>
          </Link>
        </div>
        <div className="bg-white rounded-xl shadow-lg p-8">
          <Suspense fallback={<div className="text-center text-gray-500 text-sm">Loading…</div>}>
            <VerifyEmail />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
