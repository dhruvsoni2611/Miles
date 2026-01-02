import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import GlassBackground from '../components/GlassBackground';

const AuthCallback = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        console.log('AuthCallback: Handling OAuth callback');

        // Handle the OAuth callback
        const { data, error } = await supabase.auth.getSession();

        if (error) {
          console.error('AuthCallback: OAuth error:', error);
          setError('Authentication failed. Please try again.');
          setLoading(false);
          return;
        }

        if (data.session && data.session.user) {
          console.log('AuthCallback: OAuth successful for:', data.session.user.email);

          // Check if this Google user exists in our task_admins table
          // For now, we'll create a basic user entry or find existing one
          // In production, you'd want to map Google users to your internal users

          // Try to find user by email in task_admins table
          const { data: userData, error: userError } = await supabase
            .from('task_admins')
            .select('*')
            .eq('email', data.session.user.email)
            .single();

          if (userError || !userData) {
            console.log('AuthCallback: Google user not found in task_admins table');
            setError('Your Google account is not authorized. Please contact an administrator.');
            setLoading(false);
            // Sign out the user since they're not in our system
            await supabase.auth.signOut();
            return;
          }

          // User found in task_admins table
          console.log('AuthCallback: User found in task_admins:', userData.username);

          // Create user data object
          const userInfo = {
            id: userData.id,
            email: userData.email,
            name: userData.name || userData.username,
            role: userData.role,
            is_active: userData.is_active,
            created_at: userData.created_at
          };

          // Store auth data
          localStorage.setItem('token', data.session.access_token);
          localStorage.setItem('user', JSON.stringify(userInfo));

          console.log('AuthCallback: Authentication successful, redirecting...');

          // Redirect to dashboard after successful authentication
          navigate('/');
        } else {
          console.log('AuthCallback: No session found');
          setError('Authentication failed. Please try again.');
          navigate('/login');
        }
      } catch (err) {
        console.error('AuthCallback: Unexpected error:', err);
        setError('An unexpected error occurred. Please try again.');
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };

    handleAuthCallback();
  }, [navigate]);

  return (
    <GlassBackground>
      <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 floating-animation">
          <div className="glass-card p-8">
            <div className="text-center">
              <div className="mx-auto h-20 w-20 bg-gradient-to-r from-indigo-500/30 to-purple-500/30 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/20 mb-4">
                {loading ? (
                  <svg className="animate-spin h-10 w-10 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : error ? (
                  <svg className="h-10 w-10 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="h-10 w-10 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </div>

              <h2 className="mt-6 text-center text-3xl font-bold text-white">
                {loading ? 'Authenticating...' : error ? 'Authentication Failed' : 'Success!'}
              </h2>

              <p className="mt-2 text-center text-sm text-white/80">
                {loading
                  ? 'Please wait while we complete your authentication.'
                  : error
                    ? error
                    : 'Redirecting you to your dashboard...'
                }
              </p>

              {error && (
                <div className="mt-6">
                  <button
                    onClick={() => navigate('/login')}
                    className="glass-button-primary w-full"
                  >
                    Return to Login
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </GlassBackground>
  );
};

export default AuthCallback;
