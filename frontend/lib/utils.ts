/**
 * Utility functions for the Nigerian LMS frontend
 */

/**
 * Safely map over arrays that might be undefined or null
 * Prevents "Cannot read properties of undefined (reading 'map')" errors
 */
export function safeArray<T>(arr: T[] | undefined | null): T[] {
  return arr || [];
}

/**
 * Format date to localized string
 */
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-NG', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

/**
 * Format currency in Naira
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-NG', {
    style: 'currency',
    currency: 'NGN'
  }).format(amount);
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
}

/**
 * Get initials from full name
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .substring(0, 2);
}

/**
 * Calculate percentage
 */
export function calculatePercentage(value: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((value / total) * 100);
}

/**
 * Check if user has specific role
 */
export function hasRole(user: any, ...roles: string[]): boolean {
  if (!user || !user.role) return false;
  return roles.includes(user.role);
}

/**
 * Check if user is admin (school admin or system admin)
 */
export function isAdmin(user: any): boolean {
  return hasRole(user, 'admin', 'system_admin');
}

/**
 * Check if user is teacher
 */
export function isTeacher(user: any): boolean {
  return hasRole(user, 'teacher');
}

/**
 * Check if user is parent
 */
export function isParent(user: any): boolean {
  return hasRole(user, 'parent');
}
