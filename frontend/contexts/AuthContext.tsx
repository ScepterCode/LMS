'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, User } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = async () => {
    try {
      const response = await api.getCurrentUser();
      if (response.data) {
        setUser(response.data);
        // Update localStorage backup
        localStorage.setItem('user', JSON.stringify(response.data));
      } else if (response.error) {
        // Check if this is an authentication error (401, 403, or token-related)
        const isAuthError = 
          response.error.toLowerCase().includes('unauthorized') || 
          response.error.toLowerCase().includes('forbidden') ||
          response.error.toLowerCase().includes('not authenticated') ||
          response.error.toLowerCase().includes('authentication required') ||
          response.error.toLowerCase().includes('token required') ||
          response.error.toLowerCase().includes('invalid token') ||
          response.error.toLowerCase().includes('expired token');
        
        if (isAuthError) {
          // Clear user session - they need to log in again
          console.log('🔒 Auth error detected, clearing session:', response.error);
          setUser(null);
          localStorage.removeItem('user');
          // Clear all cookies to force fresh login
          clearAllCookies();
        } else {
          // Network/timeout/server error - keep user logged in
          console.warn('⚠️ Non-auth error during refresh, keeping user logged in:', response.error);
        }
      }
    } catch (error) {
      console.error('⚠️ Network error during user refresh:', error);
      // Don't clear user on network exceptions
    }
  };

  const clearAllCookies = () => {
    // Clear all cookies for localhost and 127.0.0.1
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i];
      const eqPos = cookie.indexOf('=');
      const name = eqPos > -1 ? cookie.substring(0, eqPos).trim() : cookie.trim();
      // Clear for all possible domains and paths
      document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/';
      document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=localhost';
      document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=127.0.0.1';
    }
    console.log('🧹 Cleared all cookies');
  };

  useEffect(() => {
    // Only try to refresh if we have a cookie or stored user
    const hasAuthCookie = document.cookie.includes('access_token');
    const storedUser = localStorage.getItem('user');
    
    if (hasAuthCookie || storedUser) {
      // Try to restore from localStorage first for faster initial render
      if (storedUser && !user) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (e) {
          console.error('Failed to parse stored user:', e);
        }
      }
      
      // Then refresh from server
      refreshUser().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await api.login({ email, password });
      if (response.error) {
        return { success: false, error: response.error };
      }
      if (response.data?.user) {
        setUser(response.data.user);
        // Store user in localStorage as backup
        localStorage.setItem('user', JSON.stringify(response.data.user));
        return { success: true };
      }
      return { success: false, error: 'Login failed' };
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
    localStorage.removeItem('user');
    // Clear all cookies
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i];
      const eqPos = cookie.indexOf('=');
      const name = eqPos > -1 ? cookie.substring(0, eqPos).trim() : cookie.trim();
      document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/';
      document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=localhost';
      document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=127.0.0.1';
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
