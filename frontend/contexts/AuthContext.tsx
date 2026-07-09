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
        // Check the real HTTP status rather than guessing from the error
        // message text - a fragile substring match here meant any backend
        // error message that didn't happen to contain one of these exact
        // words (e.g. "Account no longer exists" for a deleted user/org)
        // silently fell through to "keep the stale session", even though
        // the server had already rejected it with a 401.
        const isAuthError = response.status === 401 || response.status === 403;

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
    // The auth cookie is httpOnly (deliberately - it stops XSS from
    // stealing it), so document.cookie can never see it and a
    // hasAuthCookie-style check here is always false. The server is the
    // only reliable source of truth for whether a session is valid.
    // Optimistically restore from localStorage for a faster initial
    // render, but always ask the server too - otherwise anyone whose
    // localStorage got cleared (privacy tools, browser storage eviction,
    // manual clear) while their cookie is still valid gets bounced to
    // /login for no reason.
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error('Failed to parse stored user:', e);
      }
    }

    refreshUser().finally(() => setLoading(false));
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
    clearAllCookies();
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
