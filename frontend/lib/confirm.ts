// Promise-based replacement for window.confirm(). A single <ConfirmHost/>
// (mounted in the root layout) listens for the event and renders the
// dialog; callers just `await confirm({...})`.

export interface ConfirmOptions {
  title?: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
}

const EVENT = 'app:confirm';

export function confirm(options: ConfirmOptions): Promise<boolean> {
  if (typeof window === 'undefined') return Promise.resolve(false);
  return new Promise<boolean>((resolve) => {
    window.dispatchEvent(new CustomEvent(EVENT, { detail: { options, resolve } }));
  });
}

export function subscribeConfirm(
  handler: (options: ConfirmOptions, resolve: (v: boolean) => void) => void,
): () => void {
  const listener = (e: Event) => {
    const { options, resolve } = (e as CustomEvent).detail;
    handler(options, resolve);
  };
  window.addEventListener(EVENT, listener);
  return () => window.removeEventListener(EVENT, listener);
}
