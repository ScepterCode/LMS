'use client';

import { useEffect, useState } from 'react';
import { subscribeConfirm, type ConfirmOptions } from '@/lib/confirm';

type Pending = { options: ConfirmOptions; resolve: (v: boolean) => void };

export default function ConfirmHost() {
  const [pending, setPending] = useState<Pending | null>(null);

  useEffect(() => subscribeConfirm((options, resolve) => setPending({ options, resolve })), []);

  useEffect(() => {
    if (!pending) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  const close = (result: boolean) => {
    pending?.resolve(result);
    setPending(null);
  };

  if (!pending) return null;
  const { title, message, confirmLabel = 'Confirm', cancelLabel = 'Cancel', danger } = pending.options;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4"
      onClick={() => close(false)}
    >
      <div
        className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6"
        role="alertdialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        {title && <h2 className="text-lg font-semibold text-gray-900 mb-1">{title}</h2>}
        <p className="text-sm text-gray-600">{message}</p>
        <div className="flex gap-3 justify-end mt-6">
          <button
            type="button"
            onClick={() => close(false)}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            autoFocus
            onClick={() => close(true)}
            className={`px-4 py-2 text-sm rounded-lg text-white font-medium ${
              danger ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
