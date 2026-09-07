'use client';

import { useEffect } from 'react';
import Link from 'next/link';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <div className="mx-auto w-14 h-14 rounded-full bg-red-100 flex items-center justify-center mb-5">
          <svg className="w-7 h-7 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h1 className="text-xl font-semibold text-gray-900">Something went wrong</h1>
        <p className="text-sm text-gray-600 mt-2">
          This page hit an unexpected error. Trying again often fixes it.
        </p>
        {error?.digest && (
          <p className="text-xs text-gray-400 mt-2 font-mono">Reference: {error.digest}</p>
        )}
        <div className="flex gap-3 justify-center mt-6">
          <button
            onClick={reset}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm"
          >
            Try again
          </button>
          <Link
            href="/dashboard"
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium text-sm"
          >
            Go to dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
