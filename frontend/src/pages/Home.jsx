import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Home = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleGetStarted = () => {
    if (isAuthenticated()) {
      if (user.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/employee/dashboard');
      }
    } else {
      navigate('/login');
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 shadow-sm">
        <div className="w-full px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h1 className="text-2xl font-bold text-white">Miles</h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {isAuthenticated() ? (
                <>
                  <div className="glass-card px-4 py-2">
                    <span className="text-sm text-white/90">
                      Welcome, <span className="font-medium text-white">{user?.name}</span> ({user?.role})
                    </span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="glass-button border-red-400/30 bg-red-500/20 hover:bg-red-500/30 text-red-300 hover:text-red-200"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <Link
                  to="/login"
                  className="glass-button-primary"
                >
                  Login
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center floating-animation">
          <div className="glass-card p-8 max-w-4xl mx-auto mb-8">
            <h1 className="text-5xl font-bold text-white mb-6">
              Welcome to <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Miles</span>
            </h1>
            <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
              Your AI-powered multi-tenant application platform. Streamline workflows,
              manage teams, and leverage cutting-edge AI capabilities all in one place.
            </p>

            <div className="flex justify-center space-x-6">
              <button
                onClick={handleGetStarted}
                className="glass-button-primary text-lg px-8 py-4"
              >
                {isAuthenticated() ? 'Go to Dashboard' : 'Get Started'}
              </button>
              {!isAuthenticated() && (
                <Link
                  to="/login"
                  className="glass-button text-lg px-8 py-4"
                >
                  Login
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
          <div className="glass-card p-6 floating-animation hover:scale-105 transition-transform duration-300">
            <div className="w-12 h-12 bg-indigo-500/20 rounded-lg flex items-center justify-center mb-4 backdrop-blur-sm border border-indigo-400/30">
              <svg className="w-6 h-6 text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Secure Authentication</h3>
            <p className="text-white/70">Role-based access control with JWT tokens and secure password hashing.</p>
          </div>

          <div className="glass-card p-6 floating-delayed hover:scale-105 transition-transform duration-300">
            <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center mb-4 backdrop-blur-sm border border-green-400/30">
              <svg className="w-6 h-6 text-green-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">AI-Powered Workflows</h3>
            <p className="text-white/70">Leverage LangGraph and advanced AI models for intelligent automation.</p>
          </div>

          <div className="glass-card p-6 floating-animation hover:scale-105 transition-transform duration-300" style={{ animationDelay: '1s' }}>
            <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-4 backdrop-blur-sm border border-purple-400/30">
              <svg className="w-6 h-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Multi-Tenant Architecture</h3>
            <p className="text-white/70">Isolated workspaces with role-based permissions for scalable team management.</p>
          </div>
        </div>

        {/* Demo Credentials */}
        {!isAuthenticated() && (
          <div className="mt-12 glass-card p-6 max-w-2xl mx-auto border-yellow-400/30 bg-yellow-500/10 floating-animation">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-yellow-500/20 rounded-full flex items-center justify-center backdrop-blur-sm border border-yellow-400/30">
                  <svg className="h-5 w-5 text-yellow-300" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-yellow-300">
                  Demo Credentials
                </h3>
                <div className="mt-2 text-sm text-yellow-200 space-y-1">
                  <p><strong>Admin:</strong> admin@miles.com / admin123</p>
                  <p><strong>Employee:</strong> employee@miles.com / employee123</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
