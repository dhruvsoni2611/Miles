import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Home from './pages/Home'
import AuthCallback from './pages/AuthCallback'
import Calendar from './pages/Calendar'
import './App.css'

// Protected Route Component
const ProtectedRoute = ({ children, requiredRole }) => {
  const { isAuthenticated, hasRole, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-2 border-blue-200 border-t-blue-600 mx-auto"></div>
          <p className="mt-6 text-gray-600 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  // First check: Must be authenticated
  if (!isAuthenticated()) {
    console.log('ProtectedRoute: User not authenticated, redirecting to login');
    return <Navigate to="/login" replace />;
  }

  // Second check: Must have required role if specified
  if (requiredRole && !hasRole(requiredRole)) {
    console.log(`ProtectedRoute: User does not have required role '${requiredRole}', redirecting to login`);
    // If user doesn't have the required role, redirect to login (don't allow access to any dashboard)
    return <Navigate to="/login" replace />;
  }

  console.log(`ProtectedRoute: Access granted for role '${requiredRole}'`);
  return children;
};

// App Router Component
const AppRouter = () => {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="App">
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Dashboard />} />
        <Route path="/login" element={<Login />} />
        <Route path="/home" element={<Home />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/auth/callback" element={<AuthCallback />} />


        {/* Catch all route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRouter />
      </Router>
    </AuthProvider>
  )
}

export default App
