'use client';

import { useEffect } from 'react';

/**
 * Component to clear stale authentication cookies on mount
 * This fixes issues where cookies were set for 127.0.0.1 but
 * the app is now accessed via localhost
 */
export function CookieCleaner() {
  useEffect(() => {
    // Only run once on mount
    const hasCleared = sessionStorage.getItem('cookies_cleared');
    
    if (!hasCleared) {
      console.log('🧹 Clearing stale cookies...');
      
      // Get all cookies
      const cookies = document.cookie.split(';');
      
      // Clear each cookie for all possible domains/paths
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i];
        const eqPos = cookie.indexOf('=');
        const name = eqPos > -1 ? cookie.substring(0, eqPos).trim() : cookie.trim();
        
        // Clear for current domain
        document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/';
        
        // Clear for localhost
        document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=localhost';
        
        // Clear for 127.0.0.1
        document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=127.0.0.1';
        
        // Clear for .localhost
        document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=.localhost';
      }
      
      // Mark as cleared for this session
      sessionStorage.setItem('cookies_cleared', 'true');
      
      // Also clear localStorage user data to force fresh login
      localStorage.removeItem('user');
      
      console.log('✅ Stale cookies cleared. Please log in.');
      
      // Force a full page refresh to ensure clean state
      window.location.href = '/login';
    }
  }, []);

  return null;
}
