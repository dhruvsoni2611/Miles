import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Sidebar } from '../components';

const Projects = () => {
  const { isAuthenticated, loading: authLoading, user, ensureValidSession } = useAuth();

  // Projects state
  const [projects, setProjects] = useState([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [projectsError, setProjectsError] = useState(null);

  useEffect(() => {
    // Only check auth after AuthContext has finished loading
    if (!authLoading) {
      checkAuth();
    }
  }, [authLoading]);

  // Fetch projects created by the current user
  const fetchUserProjects = async () => {
    try {
      setProjectsLoading(true);
      setProjectsError(null);

      // Ensure we have a valid token
      let token;
      try {
        token = await ensureValidSession();
      } catch (authError) {
        console.error('Authentication error:', authError);
        setProjectsError('Please login to view projects');
        setProjects([]);
        setProjectsLoading(false);
        return;
      }

      const response = await fetch('http://localhost:8000/api/projects/created', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch projects: ${response.status}`);
      }

      const data = await response.json();
      const userProjects = data.projects || [];

      setProjects(userProjects);
    } catch (error) {
      console.error('Error fetching user projects:', error);
      setProjectsError(error.message);
      setProjects([]);
    } finally {
      setProjectsLoading(false);
    }
  };

  const checkAuth = async () => {
    try {
      // Check if user is authenticated via AuthContext
      if (!isAuthenticated()) {
        console.log('Projects: No authenticated user, redirecting to login');
        // Note: Navigation would be handled by protected routes
        return;
      }

      console.log('Projects: Authentication successful for user:', user.email, 'role:', user.role);

      // Fetch user's projects
      fetchUserProjects();

    } catch (error) {
      console.error('Projects: Auth check error:', error);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-2 border-blue-200 border-t-blue-600 mx-auto"></div>
          <p className="mt-6 text-gray-600 font-medium">Loading projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Title Bar */}
        <div className="bg-white border-b border-gray-200 shadow-sm">
          <div className="w-full px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
            </div>
          </div>
        </div>

        {/* Projects Content */}
        <div className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900">Your Created Projects</h2>
            </div>

            {/* Loading State */}
            {projectsLoading && (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-200 border-t-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600 text-lg">Loading your projects...</p>
              </div>
            )}

            {/* Error State */}
            {projectsError && (
              <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6 mb-6">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-3 flex-1">
                    <h3 className="text-sm font-medium text-red-800">
                      Failed to load projects
                    </h3>
                    <div className="mt-1 text-sm text-red-600">
                      <p>{projectsError}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Projects Display */}
            {!projectsLoading && !projectsError && (
              <>
                {projects.length === 0 ? (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                    <div className="text-4xl mb-4">📁</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No projects created yet</h3>
                    <p className="text-gray-600 mb-4">Projects you create will appear here.</p>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 max-w-md mx-auto">
                      <div className="text-yellow-800">
                        <strong>Coming Soon:</strong> Project creation functionality will be available here.
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {projects.map((project) => (
                      <div
                        key={project.id}
                        className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
                      >
                        <h4 className="text-gray-900 font-semibold text-xl mb-3">{project.name}</h4>
                        {project.description && (
                          <p className="text-gray-600 text-sm mb-4 line-clamp-2">{project.description}</p>
                        )}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">Status:</span>
                            <span className={`font-medium ${
                              project.status === 'active' ? 'text-green-600' :
                              project.status === 'paused' ? 'text-yellow-600' :
                              'text-gray-600'
                            }`}>
                              {project.status === 'active' ? '🟢 Active' :
                               project.status === 'paused' ? '🟡 Paused' :
                               '📦 Archived'}
                            </span>
                          </div>
                          {project.deadline && (
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Deadline:</span>
                              <span className="font-medium">
                                {new Date(project.deadline).toLocaleDateString()}
                              </span>
                            </div>
                          )}
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">Created:</span>
                            <span className="font-medium">
                              {new Date(project.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Quick Stats for Projects */}
                {projects.length > 0 && (
                  <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
                      <div className="text-2xl font-bold text-gray-900">{projects.length}</div>
                      <div className="text-sm text-gray-600">Total Projects</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {projects.filter(p => p.status === 'active').length}
                      </div>
                      <div className="text-sm text-gray-600">Active</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
                      <div className="text-2xl font-bold text-yellow-600">
                        {projects.filter(p => p.status === 'paused').length}
                      </div>
                      <div className="text-sm text-gray-600">Paused</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
                      <div className="text-2xl font-bold text-gray-600">
                        {projects.filter(p => p.status === 'archived').length}
                      </div>
                      <div className="text-sm text-gray-600">Archived</div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Projects;
