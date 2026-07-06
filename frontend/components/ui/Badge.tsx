type BadgeTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'brand';

const toneClasses: Record<BadgeTone, string> = {
  success: 'bg-success-100 text-success-700',
  warning: 'bg-warning-100 text-warning-700',
  danger: 'bg-danger-100 text-danger-700',
  info: 'bg-info-100 text-info-700',
  neutral: 'bg-gray-100 text-gray-700',
  brand: 'bg-brand-100 text-brand-700',
};

// Common status strings mapped to one consistent tone, so "active" is
// always green and "pending" is always amber no matter which page renders it.
const statusToneMap: Record<string, BadgeTone> = {
  active: 'success',
  approved: 'success',
  paid: 'success',
  present: 'success',
  completed: 'success',
  pending: 'warning',
  draft: 'warning',
  partial: 'warning',
  late: 'warning',
  inactive: 'neutral',
  suspended: 'danger',
  rejected: 'danger',
  overdue: 'danger',
  absent: 'danger',
  cancelled: 'danger',
};

interface BadgeProps {
  children: string;
  tone?: BadgeTone;
  className?: string;
}

export function Badge({ children, tone, className = '' }: BadgeProps) {
  const resolvedTone = tone ?? statusToneMap[children.toLowerCase()] ?? 'neutral';
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${toneClasses[resolvedTone]} ${className}`}
    >
      {children}
    </span>
  );
}
