'use client';

import { useEffect } from 'react';

export default function GlobalError({
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
    <html lang="en">
      <body style={{ fontFamily: 'system-ui, sans-serif', margin: 0, background: '#f9fafb' }}>
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
          <div style={{ maxWidth: 400, textAlign: 'center' }}>
            <h1 style={{ fontSize: 20, fontWeight: 600, color: '#111827' }}>Something went wrong</h1>
            <p style={{ fontSize: 14, color: '#4b5563', marginTop: 8 }}>
              The application hit an unexpected error. Please reload the page.
            </p>
            {error?.digest && (
              <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 8, fontFamily: 'monospace' }}>
                Reference: {error.digest}
              </p>
            )}
            <button
              onClick={reset}
              style={{
                marginTop: 24, padding: '8px 16px', background: '#2563eb', color: '#fff',
                border: 0, borderRadius: 8, fontWeight: 500, fontSize: 14, cursor: 'pointer',
              }}
            >
              Reload
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
