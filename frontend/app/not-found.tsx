import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <p className="text-5xl font-bold text-blue-600">404</p>
        <h1 className="text-xl font-semibold text-gray-900 mt-3">Page not found</h1>
        <p className="text-sm text-gray-600 mt-2">
          The page you&apos;re looking for doesn&apos;t exist or has moved.
        </p>
        <Link
          href="/dashboard"
          className="inline-block mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm"
        >
          Go to dashboard
        </Link>
      </div>
    </div>
  );
}
