import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import GlassBackground from '../components/GlassBackground';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { logout } = useAuth();

  // Static hardcoded tasks data
  const tasks = [
    {
      id: '1',
      title: 'Design new landing page',
      description: 'Create a modern landing page for the new product launch',
      status: 'assigned',
      priority: 'high',
      progress: 0,
      assigned_to_name: 'John Doe',
      employee_code: 'EMP001',
      deadline: '2024-01-20T00:00:00Z',
      is_overdue: false
    },
    {
      id: '2',
      title: 'Implement user authentication',
      description: 'Add login/signup functionality with secure authentication',
      status: 'in_progress',
      priority: 'urgent',
      progress: 75,
      assigned_to_name: 'Jane Smith',
      employee_code: 'EMP002',
      deadline: '2024-01-18T00:00:00Z',
      is_overdue: false
    },
    {
      id: '3',
      title: 'Database optimization',
      description: 'Optimize slow queries and add proper indexing',
      status: 'in_review',
      priority: 'medium',
      progress: 90,
      assigned_to_name: 'Mike Johnson',
      employee_code: 'EMP003',
      deadline: '2024-01-15T00:00:00Z',
      is_overdue: false
    },
    {
      id: '4',
      title: 'Setup CI/CD pipeline',
      description: 'Configure automated deployment and testing pipeline',
      status: 'completed',
      priority: 'high',
      progress: 100,
      assigned_to_name: 'Sarah Wilson',
      employee_code: 'EMP004',
      deadline: '2024-01-10T00:00:00Z',
      is_overdue: false
    },
    {
      id: '5',
      title: 'Mobile app testing',
      description: 'Complete comprehensive testing of mobile application',
      status: 'overdue',
      priority: 'urgent',
      progress: 30,
      assigned_to_name: 'Alex Brown',
      employee_code: 'EMP005',
      deadline: '2024-01-12T00:00:00Z',
      is_overdue: true
    },
    {
      id: '6',
      title: 'API documentation',
      description: 'Write comprehensive API documentation for developers',
      status: 'assigned',
      priority: 'low',
      progress: 0,
      assigned_to_name: 'Emma Davis',
      employee_code: 'EMP006',
      deadline: '2024-01-25T00:00:00Z',
      is_overdue: false
    },
    {
      id: '7',
      title: 'Security audit',
      description: 'Perform security assessment and vulnerability testing',
      status: 'in_progress',
      priority: 'urgent',
      progress: 45,
      assigned_to_name: 'Chris Taylor',
      employee_code: 'EMP007',
      deadline: '2024-01-16T00:00:00Z',
      is_overdue: true
    }
  ];

  // Modal states
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);

  // New task form
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    priority: 'medium',
    start_date: '',
    deadline: '',
    tags: '',
    notes: ''
  });

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // For demo purposes, skip authentication and use mock admin user
      // This allows the dashboard to load immediately without Supabase setup
      console.log('Dashboard: Running in demo mode');

      setUser({
        id: 'demo-admin-id',
        email: 'admin@workvillage.ai',
        name: 'Demo Administrator',
        role: 'admin'
      });

      /*
      // Production authentication code (uncomment when Supabase is configured):

      const { data: { session }, error: sessionError } = await supabase.auth.getSession();

      if (sessionError || !session) {
        console.log('Dashboard: No valid Supabase session, redirecting to login');
        navigate('/login');
        return;
      }

      // Check if user exists in task_admins table and get their role
      const { data: profile, error: profileError } = await supabase
        .from('task_admins')
        .select('*')
        .eq('id', session.user.id)
        .single();

      if (profileError || !profile) {
        console.log('Dashboard: User not found in task_admins table');
        alert('Your account is not authorized to access the dashboard. Please contact an administrator.');
        navigate('/login');
        return;
      }

      if (profile.role !== 'admin') {
        console.log('Dashboard: User is not admin');
        alert('Only administrators can access the dashboard.');
        navigate('/login');
        return;
      }

      setUser(profile);
      */

    } catch (error) {
      console.error('Dashboard: Auth check error:', error);
      // In demo mode, don't redirect on error
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      // Demo mode: Just redirect without actual logout
      console.log('Demo: Logging out');
      navigate('/login');

      /*
      // Production logout (uncomment when Supabase is configured):
      await logout();
      navigate('/login');
      */
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/login');
    }
  };

  const handleAddTask = () => {
    // Check if user is admin
    if (user?.role !== 'admin') {
      alert('Only administrators can add tasks.');
      return;
    }
    setShowTaskModal(true);
  };

  const handleTaskSubmit = async (e) => {
    e.preventDefault();

    try {
      const taskData = {
        ...newTask,
        tags: newTask.tags ? newTask.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : []
      };

      console.log('Creating task with data:', taskData);

      // Make actual API call to backend
      const response = await fetch('http://localhost:8000/api/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // For demo, skip auth header since backend may not require it
        },
        body: JSON.stringify(taskData), // profile_id will be set by backend
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to create task (${response.status})`);
      }

      const createdTask = await response.json();
      console.log('Task created successfully:', createdTask);

      // Reset form and close modal
      setNewTask({
        title: '',
        description: '',
        priority: 'medium',
        start_date: '',
        deadline: '',
        tags: '',
        notes: ''
      });
      setShowTaskModal(false);

      // Show success message
      alert('Task created successfully! Check console for task data.');

    } catch (error) {
      console.error('Error creating task:', error);
      alert(`Failed to create task: ${error.message}`);
    }
  };



  // Group tasks by status
  const tasksByStatus = {
    assigned: tasks.filter(task => task.status === 'pending' && task.assigned_to_name),
    in_progress: tasks.filter(task => task.status === 'in_progress'),
    in_review: tasks.filter(task => task.status === 'in_review'),
    completed: tasks.filter(task => task.status === 'completed'),
    overdue: tasks.filter(task => task.is_overdue)
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'assigned': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'in_progress': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      case 'in_review': return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'completed': return 'bg-green-500/20 text-green-300 border-green-500/30';
      case 'overdue': return 'bg-red-500/20 text-red-300 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'assigned': return '📋';
      case 'in_progress': return '⚡';
      case 'in_review': return '👁️';
      case 'completed': return '✅';
      case 'overdue': return '🚨';
      default: return '📝';
    }
  };

  if (loading) {
    return (
      <GlassBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="glass-card p-8 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-2 border-white/30 border-t-white mx-auto"></div>
            <p className="mt-6 text-white/80 font-medium">Loading dashboard...</p>
          </div>
        </div>
      </GlassBackground>
    );
  }

  return (
    <GlassBackground>
      <div className="min-h-screen">
        {/* Title Bar */}
        <div className="bg-gradient-to-r from-indigo-600/80 to-purple-600/80 backdrop-blur-md border-b border-white/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div className="flex items-center space-x-4">
                <div className="h-10 w-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <h1 className="text-2xl font-bold text-white">WorkVillage</h1>
              </div>

              <div className="flex items-center space-x-4">
                <div className="text-white/80">
                  Welcome, {user?.name || user?.email?.split('@')[0]}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-3">
                  <button
                    onClick={handleAddTask}
                    className="px-4 py-2 bg-blue-500/80 hover:bg-blue-600/80 rounded-lg text-white transition-colors flex items-center space-x-2"
                  >
                    <span>➕</span>
                    <span>Add Task</span>
                  </button>

                  <button
                    onClick={() => alert('Add Employee functionality will be implemented')}
                    className="px-4 py-2 bg-green-500/80 hover:bg-green-600/80 rounded-lg text-white transition-colors flex items-center space-x-2"
                  >
                    <span>👥</span>
                    <span>Add Employee</span>
                  </button>

                  <button
                    onClick={handleLogout}
                    className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-white transition-colors"
                  >
                    Logout
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

          {/* Task Compartments Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">Task Management</h2>
            <div className="flex space-x-3">
              <button
                onClick={handleAddTask}
                className="px-6 py-3 bg-blue-500/80 hover:bg-blue-600/80 rounded-lg text-white transition-colors flex items-center space-x-2 font-medium"
              >
                <span>➕</span>
                <span>Add Task</span>
              </button>

              <button
                onClick={() => alert('Add Employee functionality will be implemented')}
                className="px-6 py-3 bg-green-500/80 hover:bg-green-600/80 rounded-lg text-white transition-colors flex items-center space-x-2 font-medium"
              >
                <span>👥</span>
                <span>Add Employee</span>
              </button>
            </div>
          </div>

          {/* Task Compartments */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {/* Assigned Tasks */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center">
                  <span className="mr-2">{getStatusIcon('assigned')}</span>
                  Assigned Tasks
                </h3>
                <span className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm">
                  {tasksByStatus.assigned.length}
                </span>
              </div>

              <div className="space-y-3">
                {tasksByStatus.assigned.map((task) => (
                  <div key={task.id} className="glass-card p-3 border border-white/10 hover:border-white/20 transition-colors group">
                    <h4 className="text-white font-medium text-sm mb-1">{task.title}</h4>
                    <div className="flex items-center justify-between text-xs text-white/60 mb-2">
                      <span>👤 {task.assigned_to_name}</span>
                      {task.priority === 'urgent' && (
                        <span className="px-1 py-0.5 bg-red-500/20 text-red-300 rounded text-xs">Urgent</span>
                      )}
                    </div>

                    {/* Task Actions */}
                    <div className="flex items-center justify-end space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      {(task.status === 'assigned' || task.status === 'in_progress') && (
                        <button
                          onClick={() => alert(`Mark complete: ${task.title}`)}
                          className="px-2 py-1 bg-green-500/20 hover:bg-green-500/40 text-green-300 rounded text-xs transition-colors"
                        >
                          Complete
                        </button>
                      )}
                      <button
                        onClick={() => alert(`Edit task: ${task.title}`)}
                        className="px-2 py-1 bg-blue-500/20 hover:bg-blue-500/40 text-blue-300 rounded text-xs transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => alert(`Delete task: ${task.title}`)}
                        className="px-2 py-1 bg-red-500/20 hover:bg-red-500/40 text-red-300 rounded text-xs transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}

                {tasksByStatus.assigned.length === 0 && (
                  <div className="text-center py-8 text-white/40">
                    <div className="text-2xl mb-2">{getStatusIcon('assigned')}</div>
                    <p className="text-sm">No assigned tasks</p>
                  </div>
                )}
              </div>
            </div>

            {/* In Progress */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center">
                  <span className="mr-2">{getStatusIcon('in_progress')}</span>
                  In Progress
                </h3>
                <span className="px-2 py-1 bg-yellow-500/20 text-yellow-300 rounded-full text-sm">
                  {tasksByStatus.in_progress.length}
                </span>
              </div>

              <div className="space-y-3">
                {tasksByStatus.in_progress.map((task) => (
                  <div key={task.id} className="glass-card p-3 border border-white/10 hover:border-white/20 transition-colors group">
                    <h4 className="text-white font-medium text-sm mb-1">{task.title}</h4>
                    <div className="flex items-center justify-between text-xs text-white/60">
                      <span>👤 {task.assigned_to_name}</span>
                      <div className="flex items-center space-x-1">
                        <div className="w-16 bg-white/20 rounded-full h-1">
                          <div
                            className="bg-yellow-400 h-1 rounded-full"
                            style={{ width: `${task.progress || 0}%` }}
                          ></div>
                        </div>
                        <span>{task.progress || 0}%</span>
                      </div>
                    </div>
                  </div>
                ))}

                {tasksByStatus.in_progress.length === 0 && (
                  <div className="text-center py-8 text-white/40">
                    <div className="text-2xl mb-2">{getStatusIcon('in_progress')}</div>
                    <p className="text-sm">No tasks in progress</p>
                  </div>
                )}
              </div>
            </div>

            {/* In Review */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center">
                  <span className="mr-2">{getStatusIcon('in_review')}</span>
                  In Review
                </h3>
                <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm">
                  {tasksByStatus.in_review.length}
                </span>
              </div>

              <div className="space-y-3">
                {tasksByStatus.in_review.map((task) => (
                  <div key={task.id} className="glass-card p-3 border border-white/10 hover:border-white/20 transition-colors group">
                    <h4 className="text-white font-medium text-sm mb-1">{task.title}</h4>
                    <div className="flex items-center justify-between text-xs text-white/60">
                      <span>👤 {task.assigned_to_name}</span>
                      <span>⏳ Awaiting review</span>
                    </div>
                  </div>
                ))}

                {tasksByStatus.in_review.length === 0 && (
                  <div className="text-center py-8 text-white/40">
                    <div className="text-2xl mb-2">{getStatusIcon('in_review')}</div>
                    <p className="text-sm">No tasks in review</p>
                  </div>
                )}
              </div>
            </div>

            {/* Completed */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center">
                  <span className="mr-2">{getStatusIcon('completed')}</span>
                  Completed
                </h3>
                <span className="px-2 py-1 bg-green-500/20 text-green-300 rounded-full text-sm">
                  {tasksByStatus.completed.length}
                </span>
              </div>

              <div className="space-y-3">
                {tasksByStatus.completed.map((task) => (
                  <div key={task.id} className="glass-card p-3 border border-white/10 hover:border-white/20 transition-colors group">
                    <h4 className="text-white font-medium text-sm mb-1 line-through opacity-75">{task.title}</h4>
                    <div className="flex items-center justify-between text-xs text-white/60">
                      <span>👤 {task.assigned_to_name}</span>
                      <span>✅ Done</span>
                    </div>
                  </div>
                ))}

                {tasksByStatus.completed.length === 0 && (
                  <div className="text-center py-8 text-white/40">
                    <div className="text-2xl mb-2">{getStatusIcon('completed')}</div>
                    <p className="text-sm">No completed tasks</p>
                  </div>
                )}
              </div>
            </div>

            {/* Overdue */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center">
                  <span className="mr-2">{getStatusIcon('overdue')}</span>
                  Overdue
                </h3>
                <span className="px-2 py-1 bg-red-500/20 text-red-300 rounded-full text-sm">
                  {tasksByStatus.overdue.length}
                </span>
              </div>

              <div className="space-y-3">
                {tasksByStatus.overdue.map((task) => (
                  <div key={task.id} className="glass-card p-3 border border-red-500/30 hover:border-red-500/50 transition-colors">
                    <h4 className="text-white font-medium text-sm mb-1">{task.title}</h4>
                    <div className="flex items-center justify-between text-xs text-white/60">
                      <span>👤 {task.assigned_to_name}</span>
                      <span className="text-red-400">🚨 Overdue</span>
                    </div>
                    {task.deadline && (
                      <div className="text-xs text-red-300 mt-1">
                        Due: {new Date(task.deadline).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                ))}

                {tasksByStatus.overdue.length === 0 && (
                  <div className="text-center py-8 text-white/40">
                    <div className="text-2xl mb-2">{getStatusIcon('overdue')}</div>
                    <p className="text-sm">No overdue tasks</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="glass-card p-4 text-center">
              <div className="text-2xl font-bold text-white">{tasks.length}</div>
              <div className="text-sm text-white/70">Total Tasks</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-2xl font-bold text-blue-300">{tasksByStatus.assigned.length}</div>
              <div className="text-sm text-white/70">Assigned</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-2xl font-bold text-yellow-300">{tasksByStatus.in_progress.length}</div>
              <div className="text-sm text-white/70">In Progress</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-2xl font-bold text-green-300">{tasksByStatus.completed.length}</div>
              <div className="text-sm text-white/70">Completed</div>
            </div>
          </div>

          {/* Task Modal */}
          {showTaskModal && (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="glass-card w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                <div className="p-6">
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold text-white">Add New Task</h2>
                    <button
                      onClick={() => setShowTaskModal(false)}
                      className="text-white/70 hover:text-white text-2xl"
                    >
                      ✕
                    </button>
                  </div>

                  <form onSubmit={handleTaskSubmit} className="space-y-6">
                    {/* Title */}
                    <div>
                      <label className="block text-sm font-medium text-white/90 mb-2">
                        Title *
                      </label>
                      <input
                        type="text"
                        required
                        value={newTask.title}
                        onChange={(e) => setNewTask(prev => ({ ...prev, title: e.target.value }))}
                        className="glass-input w-full"
                        placeholder="Enter task title"
                      />
                    </div>

                    {/* Description */}
                    <div>
                      <label className="block text-sm font-medium text-white/90 mb-2">
                        Description
                      </label>
                      <textarea
                        value={newTask.description}
                        onChange={(e) => setNewTask(prev => ({ ...prev, description: e.target.value }))}
                        className="glass-input w-full h-24"
                        placeholder="Enter task description"
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Priority */}
                      <div>
                        <label className="block text-sm font-medium text-white/90 mb-2">
                          Priority
                        </label>
                        <select
                          value={newTask.priority}
                          onChange={(e) => setNewTask(prev => ({ ...prev, priority: e.target.value }))}
                          className="glass-input w-full"
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                          <option value="urgent">Urgent</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Start Date */}
                      <div>
                        <label className="block text-sm font-medium text-white/90 mb-2">
                          Start Date
                        </label>
                        <input
                          type="date"
                          value={newTask.start_date}
                          onChange={(e) => setNewTask(prev => ({ ...prev, start_date: e.target.value }))}
                          className="glass-input w-full"
                        />
                      </div>

                      {/* Deadline */}
                      <div>
                        <label className="block text-sm font-medium text-white/90 mb-2">
                          Deadline
                        </label>
                        <input
                          type="date"
                          value={newTask.deadline}
                          onChange={(e) => setNewTask(prev => ({ ...prev, deadline: e.target.value }))}
                          className="glass-input w-full"
                        />
                      </div>
                    </div>

                    {/* Tags */}
                    <div>
                      <label className="block text-sm font-medium text-white/90 mb-2">
                        Tags (comma-separated)
                      </label>
                      <input
                        type="text"
                        value={newTask.tags}
                        onChange={(e) => setNewTask(prev => ({ ...prev, tags: e.target.value }))}
                        className="glass-input w-full"
                        placeholder="design, frontend, urgent"
                      />
                    </div>

                    {/* Notes */}
                    <div>
                      <label className="block text-sm font-medium text-white/90 mb-2">
                        Notes
                      </label>
                      <textarea
                        value={newTask.notes}
                        onChange={(e) => setNewTask(prev => ({ ...prev, notes: e.target.value }))}
                        className="glass-input w-full h-24"
                        placeholder="Additional notes"
                      />
                    </div>

                    {/* Submit Buttons */}
                    <div className="flex justify-end space-x-4">
                      <button
                        type="button"
                        onClick={() => setShowTaskModal(false)}
                        className="px-6 py-2 glass-card text-white/70 hover:text-white transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-6 py-2 glass-button-primary"
                      >
                        Create Task
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </GlassBackground>
  );
};

export default Dashboard;
