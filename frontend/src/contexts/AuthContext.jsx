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
      console.log('AuthContext: Attempting login for email:', email);

      // Call our custom backend login endpoint
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();

      if (data.user && data.access_token) {
        console.log('AuthContext: Login successful for:', data.user.name);

        const userData = {
          id: data.user.id,
          email: data.user.email || '',
          name: data.user.name || email,
          role: data.user.role,
          is_active: data.user.is_active,
          created_at: data.user.created_at
        };

        console.log('AuthContext: Storing user data:', userData);

        // Store auth data
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(userData));

        setUser(userData);
        setToken(data.access_token);

        return userData;
      }

      console.error('AuthContext: Login failed - no user or token data');
      throw new Error('Login failed - no user data received');
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
      const { data: { session }, error } = await supabase.auth.getSession();

      if (error) {
        console.error('AuthContext: Session error:', error);
        throw error;
      }

      if (!session) {
        console.log('AuthContext: No session found, user needs to login');
        logout();
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
          logout();
          throw new Error('Token refresh failed');
        }

        if (refreshData.session) {
          console.log('AuthContext: Token refreshed successfully');
          const role = refreshData.user.user_metadata?.role || 'employee';
          const userData = {
            id: refreshData.user.id,
            email: refreshData.user.email,
            name: refreshData.user.user_metadata?.name || '',
            role: role,
            is_active: true,
            created_at: refreshData.user.created_at
          };

          setUser(userData);
          setToken(refreshData.session.access_token);
          localStorage.setItem('token', refreshData.session.access_token);
          localStorage.setItem('user', JSON.stringify(userData));

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
