import React, { createContext, useState, useContext, useEffect } from 'react';
import { supabase } from '../lib/supabase';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing Supabase session
    const checkUser = async () => {
      try {
        console.log('AuthContext: Checking Supabase session...');
        const { data: { session }, error } = await supabase.auth.getSession();

        if (error) {
          console.error('AuthContext: Session error:', error);
        }

        if (session && session.user) {
          console.log('AuthContext: Valid session found for user:', session.user.email);
          const role = session.user.user_metadata?.role || 'employee';

          const userData = {
            id: session.user.id,
            email: session.user.email,
            name: session.user.user_metadata?.name || '',
            role: role,
            is_active: true,
            created_at: session.user.created_at
          };

          console.log('AuthContext: Setting user data:', userData);
          setUser(userData);
          setToken(session.access_token);

          // Store in localStorage for persistence
          localStorage.setItem('token', session.access_token);
          localStorage.setItem('user', JSON.stringify(userData));
        } else {
          console.log('AuthContext: No valid session, clearing data');
          // Clear any stale data
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
          setToken(null);
        }
      } catch (error) {
        console.error('AuthContext: Session check error:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        setToken(null);
      } finally {
        setLoading(false);
      }
    };

    checkUser();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('AuthContext: Auth state change - event:', event, 'session:', !!session);
        if (session && session.user) {
          console.log('AuthContext: User signed in:', session.user.email);
          const role = session.user.user_metadata?.role || 'employee';

          const userData = {
            id: session.user.id,
            email: session.user.email,
            name: session.user.user_metadata?.name || '',
            role: role,
            is_active: true,
            created_at: session.user.created_at
          };

          setUser(userData);
          setToken(session.access_token);
          localStorage.setItem('token', session.access_token);
          localStorage.setItem('user', JSON.stringify(userData));
        } else {
          console.log('AuthContext: User signed out or no session');
          setUser(null);
          setToken(null);
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        }
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const login = async (email, password) => {
    try {
      console.log('AuthContext: Attempting Supabase login for email:', email);

      // Use Supabase Auth directly for proper session management
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        console.error('AuthContext: Supabase login error:', error);
        throw new Error(error.message || 'Login failed');
      }

      if (data.user && data.session) {
        console.log('AuthContext: Supabase login successful for:', data.user.email);

        // The session will be handled automatically by Supabase
        // The onAuthStateChange listener will update our state
        return data.user;
      }

      console.error('AuthContext: Login failed - no user or session data');
      throw new Error('Login failed - no session data received');
    } catch (error) {
      console.error('AuthContext: Login error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Sign out from Supabase
      const { error } = await supabase.auth.signOut();
      if (error) {
        console.error('Supabase logout error:', error);
      }
    } catch (error) {
      console.error('Logout error:', error);
    }

    // Clear local storage and state
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setToken(null);
  };

  const isAuthenticated = () => {
    return user !== null && token !== null;
  };

  const hasRole = (role) => {
    return user?.role === role;
  };

  const ensureValidSession = async () => {
    try {
      console.log('AuthContext: Ensuring valid session...');

      // First, check if we have a cached session
      const { data: { session }, error } = await supabase.auth.getSession();

      if (error) {
        console.error('AuthContext: Session error:', error);
        throw error;
      }

      if (!session) {
        console.log('AuthContext: No session found, user needs to login');
        throw new Error('No active session');
      }

      // Check if token is expired or about to expire (within 5 minutes)
      const now = Math.floor(Date.now() / 1000);
      const expiresAt = session.expires_at;
      const timeUntilExpiry = expiresAt - now;

      console.log('AuthContext: Token expires in', timeUntilExpiry, 'seconds');

      if (timeUntilExpiry < 300) { // Less than 5 minutes
        console.log('AuthContext: Token expiring soon, attempting refresh...');
        const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession();

        if (refreshError) {
          console.error('AuthContext: Token refresh failed:', refreshError);
          throw new Error('Token refresh failed');
        }

        if (refreshData.session) {
          console.log('AuthContext: Token refreshed successfully');
          // The onAuthStateChange listener will handle the session update
          return refreshData.session.access_token;
        }
      }

      return session.access_token;
    } catch (error) {
      console.error('AuthContext: ensureValidSession error:', error);
      throw error;
    }
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated,
    hasRole,
    ensureValidSession,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
