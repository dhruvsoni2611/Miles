import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

// Calendar Component for Due Date Selection
const CalendarDatePicker = ({ selectedDate, onDateChange, placeholder = "Select due date" }) => {
  return (
    <div className="relative">
      <DatePicker
        selected={selectedDate ? new Date(selectedDate) : null}
        onChange={(date) => onDateChange(date ? date.toISOString().split('T')[0] : '')}
        minDate={new Date()}
        dateFormat="yyyy-MM-dd"
        placeholderText={placeholder}
        className="w-full px-4 py-2 pl-10 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors"
        calendarClassName="custom-calendar"
      />
      <svg className="w-5 h-5 text-gray-400 absolute left-3 top-2.5 z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    </div>
  );
};

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const navigate = useNavigate();
  const { logout, ensureValidSession, isAuthenticated, loading: authLoading, user } = useAuth();

  // Tasks state
  const [tasks, setTasks] = useState([]);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [tasksError, setTasksError] = useState(null);

  // Managed employees state
  const [managedEmployees, setManagedEmployees] = useState([]);
  const [employeesLoading, setEmployeesLoading] = useState(false);
  const [employeesError, setEmployeesError] = useState(null);

  // Modal states
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);

  // New employee form
  const [newEmployee, setNewEmployee] = useState({
    email: '',
    name: '',
    profile_picture: ''
  });

  // New task form
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    project_id: '',
    priority: 'medium',
    difficulty_level: 1,
    required_skills: '',
    status: 'todo',
    assigned_to: '',
    due_date: ''
  });


  // Fetch managed employees from API
  const fetchManagedEmployees = async () => {
    try {
      setEmployeesLoading(true);
      setEmployeesError(null);

      // Ensure we have a valid token
      let token;
      try {
        token = await ensureValidSession();
      } catch (authError) {
        console.error('Authentication error:', authError);
        setEmployeesError('Please login to view employees');
        setManagedEmployees([]);
        setEmployeesLoading(false);
        return;
      }

      const response = await fetch('http://localhost:8000/api/employees/managed', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch employees: ${response.status}`);
      }

      const data = await response.json();
      setManagedEmployees(data.employees || []);
    } catch (error) {
      console.error('Error fetching managed employees:', error);
      setEmployeesError(error.message);
      setManagedEmployees([]);
    } finally {
      setEmployeesLoading(false);
    }
  };

  // Fetch tasks from API
  const fetchTasks = async () => {
    try {
      setTasksLoading(true);
      setTasksError(null);

      // Ensure we have a valid token
      let token;
      try {
        token = await ensureValidSession();
      } catch (authError) {
        console.error('Authentication error:', authError);
        setTasksError('Please login to view tasks');
        setTasks([]);
        setTasksLoading(false);
        return;
      }

      const response = await fetch('http://localhost:8000/api/tasks', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch tasks: ${response.status}`);
      }

      const data = await response.json();
      setTasks(data.tasks || []);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setTasksError(error.message);
      setTasks([]); // Fallback to empty array
    } finally {
      setTasksLoading(false);
    }
  };

  // Drag and drop state
  const [draggedTask, setDraggedTask] = useState(null);
  const [dragOverStatus, setDragOverStatus] = useState(null);

  // Drag and drop handlers
  const handleDragStart = (e, task) => {
    setDraggedTask(task);
    e.dataTransfer.setData('application/json', JSON.stringify(task));
    e.dataTransfer.effectAllowed = 'move';
    e.target.style.opacity = '0.5';
  };

  const handleDragEnd = (e) => {
    setDraggedTask(null);
    setDragOverStatus(null);
    e.target.style.opacity = '1';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDragEnter = (status) => {
    setDragOverStatus(status);
  };

  const handleDragLeave = () => {
    setDragOverStatus(null);
  };

  const handleDrop = async (e, newStatus) => {
    e.preventDefault();
    setDragOverStatus(null);

    try {
      const taskData = JSON.parse(e.dataTransfer.getData('application/json'));

      // Don't update if status is already the same
      if (taskData.status === newStatus) {
        return;
      }

      console.log('Updating task status:', taskData.id, 'from', taskData.status, 'to', newStatus);

      // Optimistically update the UI first for better UX
      setTasks(prevTasks =>
        prevTasks.map(task =>
          task.id === taskData.id
            ? { ...task, status: newStatus }
            : task
        )
      );

      // Get valid token
      const token = await ensureValidSession();

      // Update task status via API
      const response = await fetch(`http://localhost:8000/api/tasks/${taskData.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: newStatus
        }),
      });

      if (!response.ok) {
        // Revert the optimistic update on failure
        console.error('API call failed, reverting UI update');
        setTasks(prevTasks =>
          prevTasks.map(task =>
            task.id === taskData.id
              ? { ...task, status: taskData.status } // Revert to original status
              : task
          )
        );
        throw new Error(`Failed to update task status: ${response.status}`);
      }

      console.log('Task status updated successfully');

      // Refresh tasks after successful update to ensure data consistency
      await fetchTasks();

    } catch (error) {
      console.error('Error updating task status:', error);
      alert(`Failed to update task status: ${error.message}`);
    }
  };

  useEffect(() => {
    // Only check auth after AuthContext has finished loading
    if (!authLoading) {
    checkAuth();
    fetchProjects();
    }
  }, [authLoading]);

  // Fetch tasks when user is authenticated
  useEffect(() => {
    if (user) {
      fetchTasks();
    }
  }, [user]);

  const fetchProjects = async () => {
    try {
      // For demo purposes, use hardcoded projects
      // In production, this would fetch from: /api/projects
      const demoProjects = [
        { id: 'demo-project-1', name: 'Website Redesign' },
        { id: 'demo-project-2', name: 'Mobile App Development' },
        { id: 'demo-project-3', name: 'API Integration' },
        { id: 'demo-project-4', name: 'Database Optimization' }
      ];
      setProjects(demoProjects);
    } catch (error) {
      console.error('Error fetching projects:', error);
    }
  };

  const checkAuth = async () => {
    try {
      // Check if user is authenticated via AuthContext
      if (!isAuthenticated()) {
        console.log('Dashboard: No authenticated user, redirecting to login');
        navigate('/login');
        return;
      }

      // Check user role - allow managers and admins to access dashboard
      if (!user || (user.role !== 'manager' && user.role !== 'admin')) {
        console.log('Dashboard: User does not have required role (manager/admin)');
        alert('Access denied. Only managers and administrators can access the dashboard.');
        navigate('/login');
        return;
      }

      console.log('Dashboard: Authentication successful for user:', user.email, 'role:', user.role);

    } catch (error) {
      console.error('Dashboard: Auth check error:', error);
      alert('Authentication failed. Please login again.');
      navigate('/login');
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
    // Check if user is authenticated
    if (!isAuthenticated()) {
      alert('Please login to add tasks');
      navigate('/login');
      return;
    }

    // Check if user is admin
    if (user?.role !== 'admin') {
      alert('Only administrators can add tasks.');
      return;
    }

    // Fetch managed employees when opening the modal
    fetchManagedEmployees();
    setShowTaskModal(true);
  };

  const handleAddEmployee = () => {
    // Check if user is authenticated
    if (!isAuthenticated()) {
      alert('Please login to add employees');
      navigate('/login');
      return;
    }

    // Check if user is manager or admin
    if (user?.role !== 'manager' && user?.role !== 'admin') {
      alert('Only managers and administrators can add employees.');
      return;
    }

    setShowEmployeeModal(true);
  };

  const handleTaskSubmit = async (e) => {
    e.preventDefault();

    // Check if user is authenticated
    if (!isAuthenticated()) {
      alert('Please login to create tasks');
      navigate('/login');
      return;
    }

    try {
      // Ensure user is authenticated and get valid token
      let token;
      try {
        token = await ensureValidSession();
      } catch (authError) {
        console.error('Authentication error:', authError);
        if (authError.message.includes('No active session')) {
          alert('Your session has expired. Please login again.');
          navigate('/login');
          return;
        }
        throw new Error(`Authentication failed: ${authError.message}`);
      }

      const taskData = {
        title: newTask.title,
        description: newTask.description,
        priority: newTask.priority, // Send as string, backend converts to int
        difficulty_level: parseInt(newTask.difficulty_level),
        required_skills: newTask.required_skills ? newTask.required_skills.split(',').map(skill => skill.trim()).filter(skill => skill) : [],
        status: newTask.status,
        assigned_to: newTask.assigned_to || null,
        due_date: newTask.due_date ? new Date(newTask.due_date).toISOString() : null
      };

      console.log('Creating task with data:', taskData);

      // Make authenticated API call to backend
      const response = await fetch('http://localhost:8000/api/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(taskData),
      });

      if (!response.ok) {
        let errorMessage = `Failed to create task (${response.status})`;

        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (typeof errorData === 'object') {
            // Handle different error response formats
            errorMessage = JSON.stringify(errorData, null, 2);
          }
        } catch (parseError) {
          // If we can't parse JSON, use the status text
          errorMessage = `Failed to create task: ${response.status} ${response.statusText}`;
        }

        throw new Error(errorMessage);
      }

      const createdTask = await response.json();
      console.log('Task created successfully:', createdTask);

      // Reset form and close modal
      setNewTask({
        title: '',
        description: '',
        project_id: '',
        priority: 'medium',
        difficulty_level: 1,
        required_skills: '',
        status: 'todo',
        assigned_to: '',
        due_date: ''
      });
      setShowTaskModal(false);

      // Show success message
      alert('Task created successfully! Check console for task data.');

    } catch (error) {
      console.error('Error creating task:', error);
      alert(`Failed to create task: ${error.message}`);
    }
  };

  const handleEmployeeSubmit = async (e) => {
    e.preventDefault();

    // Check if user is authenticated
    if (!isAuthenticated()) {
      alert('Please login to create employees');
      navigate('/login');
      return;
    }

    try {
      // Ensure user is authenticated and get valid token
      let token;
      try {
        token = await ensureValidSession();
      } catch (authError) {
        console.error('Authentication error:', authError);
        if (authError.message.includes('No active session')) {
          alert('Your session has expired. Please login again.');
          navigate('/login');
          return;
        }
        throw new Error(`Authentication failed: ${authError.message}`);
      }

      const employeeData = {
        email: newEmployee.email,
        name: newEmployee.name,
        profile_picture: newEmployee.profile_picture || null
      };

      console.log('Creating employee with data:', employeeData);

      // Make authenticated API call to backend
      const response = await fetch('http://localhost:8000/api/employees', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(employeeData),
      });

      if (!response.ok) {
        let errorMessage = `Failed to create employee (${response.status})`;

        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (typeof errorData === 'object') {
            errorMessage = JSON.stringify(errorData, null, 2);
          }
        } catch (parseError) {
          errorMessage = `Failed to create employee: ${response.status} ${response.statusText}`;
        }

        throw new Error(errorMessage);
      }

      const createdEmployee = await response.json();
      console.log('Employee created successfully:', createdEmployee);

      // Reset form and close modal
      setNewEmployee({
        email: '',
        name: '',
        profile_picture: ''
      });
      setShowEmployeeModal(false);

      // Show success message
      alert('Employee created successfully! Check console for employee data.');

    } catch (error) {
      console.error('Error creating employee:', error);
      alert(`Failed to create employee: ${error.message}`);
    }
  };



  // Group tasks by status
  const tasksByStatus = {
    assigned: tasks.filter(task => task.status === 'assigned' || task.status === 'todo'),
    in_progress: tasks.filter(task => task.status === 'in_progress'),
    in_review: tasks.filter(task => task.status === 'review'),
    completed: tasks.filter(task => task.status === 'completed' || task.status === 'done'),
    overdue: tasks.filter(task => task.is_overdue === true)
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'assigned':
      case 'todo': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'in_progress': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      case 'in_review': return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'completed': return 'bg-green-500/20 text-green-300 border-green-500/30';
      case 'overdue': return 'bg-red-500/20 text-red-300 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'assigned':
      case 'todo': return '📋';
      case 'in_progress': return '⚡';
      case 'in_review': return '👁️';
      case 'completed': return '✅';
      case 'overdue': return '🚨';
      default: return '📝';
    }
  };

  if (loading || authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-2 border-blue-200 border-t-blue-600 mx-auto"></div>
          <p className="mt-6 text-gray-600 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
        {/* Title Bar */}
        <div className="bg-white border-b border-gray-200 shadow-sm">
          <div className="w-full px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-4">
                <div className="h-10 w-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <h1 className="text-2xl font-bold text-gray-900">WorkVillage</h1>
              </div>

              <div className="flex items-center space-x-4">
                <span className="text-gray-600">Welcome, {user?.name || user?.email?.split('@')[0]}</span>
                <button
                  onClick={() => navigate('/calendar')}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white transition-colors flex items-center space-x-2 font-medium"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>Calendar</span>
                </button>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleAddTask}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white transition-colors flex items-center space-x-2 font-medium"
                >
                  <span>➕</span>
                  <span>Add Task</span>
                </button>

                <button
                  onClick={handleAddEmployee}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white transition-colors flex items-center space-x-2 font-medium"
                >
                  <span>👥</span>
                  <span>Add Employee</span>
                </button>

                <button
                  onClick={handleLogout}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-gray-700 transition-colors font-medium"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="w-full px-4 sm:px-6 lg:px-8 py-8">

          {/* Task Compartments Header */}
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900">Task Management</h2>
            <div className="flex space-x-3">
              <button
                onClick={handleAddTask}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white transition-colors flex items-center space-x-2 font-medium shadow-sm"
              >
                <span>➕</span>
                <span>Add Task</span>
              </button>

              <button
                onClick={handleAddEmployee}
                className="px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg text-white transition-colors flex items-center space-x-2 font-medium shadow-sm"
              >
                <span>👥</span>
                <span>Add Employee</span>
              </button>
            </div>
          </div>

          {/* Loading and Error States */}
          {tasksLoading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-200 border-t-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 text-lg">Loading your tasks...</p>
            </div>
          )}

          {tasksError && (
            <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6 mb-6">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3 flex-1">
                  <h3 className="text-sm font-medium text-red-800">
                    Failed to load tasks
                  </h3>
                  <div className="mt-1 text-sm text-red-600">
                    <p>{tasksError}</p>
                  </div>
                  <div className="mt-3">
                    <button
                      onClick={fetchTasks}
                      className="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded text-sm transition-colors border border-red-300"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Only show task compartments when not loading and no errors */}
          {!tasksLoading && !tasksError && (
            <>
              {/* Task Compartments */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {/* Assigned Tasks */}
            <div
              className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 transition-all ${
                dragOverStatus === 'assigned' ? 'border-blue-400 bg-blue-50 shadow-lg' : ''
              }`}
              onDragOver={handleDragOver}
              onDragEnter={() => handleDragEnter('assigned')}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, 'todo')}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <span className="mr-2">{getStatusIcon('assigned')}</span>
                  Assigned Tasks
                </h3>
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                  {tasksByStatus.assigned.length}
                </span>
              </div>

              <div className="space-y-3">
                {tasksByStatus.assigned.map((task) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, task)}
                    onDragEnd={handleDragEnd}
                    className="bg-gray-50 rounded-lg p-3 border border-gray-200 hover:shadow-md transition-all cursor-move"
                  >
                    <h4 className="text-gray-900 font-medium text-sm mb-2">{task.title}</h4>
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                      <span className="capitalize font-medium">
                        {task.priority === 'urgent' && '🔴 '}
                        {task.priority === 'high' && '🟠 '}
                        {task.priority === 'medium' && '🟡 '}
                        {task.priority === 'low' && '🟢 '}
                        {task.priority}
                      </span>
                      {task.created_at && (
                        <span>
                          📅 {new Date(task.created_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    {/* Task Actions */}
                    <div className="flex items-center justify-end space-x-2">
                      {(task.status === 'assigned' || task.status === 'in_progress') && (
                        <button
                          onClick={() => alert(`Mark complete: ${task.title}`)}
                          className="px-2 py-1 bg-green-100 hover:bg-green-200 text-green-700 rounded text-xs transition-colors font-medium"
                        >
                          Complete
                        </button>
                      )}
                      <button
                        onClick={() => alert(`Edit task: ${task.title}`)}
                        className="px-2 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded text-xs transition-colors font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => alert(`Delete task: ${task.title}`)}
                        className="px-2 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded text-xs transition-colors font-medium"
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
            <div
              className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 transition-all ${
                dragOverStatus === 'in_progress' ? 'border-yellow-400 bg-yellow-50 shadow-lg' : ''
              }`}
              onDragOver={handleDragOver}
              onDragEnter={() => handleDragEnter('in_progress')}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, 'in_progress')}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <span className="mr-2">{getStatusIcon('in_progress')}</span>
                  In Progress
                </h3>
                <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                  {tasksByStatus.in_progress.length}
                </span>
              </div>

              <div className="space-y-3">
                {tasksByStatus.in_progress.map((task) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, task)}
                    onDragEnd={handleDragEnd}
                    className="bg-gray-50 rounded-lg p-3 border border-gray-200 hover:shadow-md transition-all cursor-move"
                  >
                    <h4 className="text-gray-900 font-medium text-sm mb-2">{task.title}</h4>
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                      <span className="capitalize font-medium">
                        {task.priority === 'urgent' && '🔴 '}
                        {task.priority === 'high' && '🟠 '}
                        {task.priority === 'medium' && '🟡 '}
                        {task.priority === 'low' && '🟢 '}
                        {task.priority}
                      </span>
                      <div className="flex items-center space-x-1">
                        <div className="w-16 bg-gray-200 rounded-full h-1">
                          <div
                            className="bg-yellow-500 h-1 rounded-full"
                            style={{ width: `${task.progress || 0}%` }}
                          ></div>
                        </div>
                        <span className="font-medium">{task.progress || 0}%</span>
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
            <div
              className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 transition-all ${
                dragOverStatus === 'review' ? 'border-purple-400 bg-purple-50 shadow-lg' : ''
              }`}
              onDragOver={handleDragOver}
              onDragEnter={() => handleDragEnter('review')}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, 'review')}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <span className="mr-2">{getStatusIcon('in_review')}</span>
                  In Review
                </h3>
                <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                  {tasksByStatus.in_review.length}
                </span>
              </div>

              <div className="space-y-3">
                {tasksByStatus.in_review.map((task) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, task)}
                    onDragEnd={handleDragEnd}
                    className="bg-gray-50 rounded-lg p-3 border border-gray-200 hover:shadow-md transition-all cursor-move"
                  >
                    <h4 className="text-gray-900 font-medium text-sm mb-2">{task.title}</h4>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span className="capitalize font-medium">
                        {task.priority === 'urgent' && '🔴 '}
                        {task.priority === 'high' && '🟠 '}
                        {task.priority === 'medium' && '🟡 '}
                        {task.priority === 'low' && '🟢 '}
                        {task.priority}
                      </span>
                      <span className="font-medium">⏳ Awaiting review</span>
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
            <div
              className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 transition-all ${
                dragOverStatus === 'done' ? 'border-green-400 bg-green-50 shadow-lg' : ''
              }`}
              onDragOver={handleDragOver}
              onDragEnter={() => handleDragEnter('done')}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, 'done')}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <span className="mr-2">{getStatusIcon('completed')}</span>
                  Completed
                </h3>
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                  {tasksByStatus.completed.length}
                </span>
              </div>

              <div className="space-y-3">
                {tasksByStatus.completed.map((task) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, task)}
                    onDragEnd={handleDragEnd}
                    className="bg-green-50 rounded-lg p-3 border border-green-200 hover:shadow-md transition-all cursor-move"
                  >
                    <h4 className="text-gray-900 font-medium text-sm mb-2 line-through opacity-75">{task.title}</h4>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span className="capitalize font-medium">
                        {task.priority === 'urgent' && '🔴 '}
                        {task.priority === 'high' && '🟠 '}
                        {task.priority === 'medium' && '🟡 '}
                        {task.priority === 'low' && '🟢 '}
                        {task.priority}
                      </span>
                      <span className="font-medium text-green-600">✅ Done</span>
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
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <span className="mr-2">{getStatusIcon('overdue')}</span>
                  Overdue
                </h3>
                <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
                  {tasksByStatus.overdue.length}
                </span>
              </div>

              <div className="space-y-3">
                {tasksByStatus.overdue.map((task) => (
                  <div key={task.id} className="bg-red-50 rounded-lg p-3 border border-red-200 hover:shadow-md transition-shadow">
                    <h4 className="text-gray-900 font-medium text-sm mb-2">{task.title}</h4>
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                      <span className="capitalize font-medium">
                        {task.priority === 'urgent' && '🔴 '}
                        {task.priority === 'high' && '🟠 '}
                        {task.priority === 'medium' && '🟡 '}
                        {task.priority === 'low' && '🟢 '}
                        {task.priority}
                      </span>
                      <span className="font-medium text-red-600">🚨 Overdue</span>
                    </div>
                    {task.deadline && (
                      <div className="text-xs text-red-600 font-medium">
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
            </>
          )}

          {/* Quick Stats */}
          <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-2xl font-bold text-gray-900">{tasks.length}</div>
              <div className="text-sm text-gray-600">Total Tasks</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">{tasksByStatus.assigned.length}</div>
              <div className="text-sm text-gray-600">Assigned</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-2xl font-bold text-yellow-600">{tasksByStatus.in_progress.length}</div>
              <div className="text-sm text-gray-600">In Progress</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-2xl font-bold text-green-600">{tasksByStatus.completed.length}</div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
          </div>

          {/* Task Modal */}
          {showTaskModal && (
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-white w-full max-w-4xl max-h-[95vh] overflow-hidden rounded-2xl shadow-2xl">
                {/* Header */}
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                      </div>
                      <div>
                        <h2 className="text-xl font-bold text-white">Create New Task</h2>
                        <p className="text-blue-100 text-sm">Fill in the details below</p>
                      </div>
                    </div>
                    <button
                      onClick={() => setShowTaskModal(false)}
                      className="w-8 h-8 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center text-white transition-colors"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                {/* Form Content */}
                <div className="overflow-y-auto max-h-[calc(95vh-120px)]">
                  <form onSubmit={handleTaskSubmit} className="p-6 space-y-6">
                    {/* Essential Information Card */}
                    <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                      <div className="flex items-center space-x-2 mb-4">
                        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h3 className="text-lg font-semibold text-gray-900">Essential Information</h3>
                      </div>

                      {/* Title */}
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Task Title <span className="text-red-500">*</span>
                        </label>
                        <div className="relative">
                          <input
                            type="text"
                            required
                            value={newTask.title}
                            onChange={(e) => setNewTask(prev => ({ ...prev, title: e.target.value }))}
                            className="w-full px-4 py-3 pl-10 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors"
                            placeholder="Enter a clear, descriptive title"
                          />
                          <svg className="w-5 h-5 text-gray-400 absolute left-3 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                          </svg>
                        </div>
                      </div>

                      {/* Description */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Description
                        </label>
                        <textarea
                          value={newTask.description}
                          onChange={(e) => setNewTask(prev => ({ ...prev, description: e.target.value }))}
                          className="w-full px-4 py-3 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors resize-none"
                          placeholder="Provide detailed information about this task..."
                          rows="3"
                        />
                      </div>
                    </div>

                    {/* Task Details Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Priority & Difficulty Card */}
                      <div className="bg-white border border-gray-200 rounded-xl p-6">
                        <div className="flex items-center space-x-2 mb-4">
                          <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                          </svg>
                          <h3 className="text-lg font-semibold text-gray-900">Priority & Difficulty</h3>
                        </div>

                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Priority Level
                            </label>
                            <select
                              value={newTask.priority}
                              onChange={(e) => setNewTask(prev => ({ ...prev, priority: e.target.value }))}
                              className="w-full px-3 py-2 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors"
                            >
                              <option value="low">🟢 Low Priority</option>
                              <option value="medium">🟡 Medium Priority</option>
                              <option value="high">🟠 High Priority</option>
                              <option value="urgent">🔴 Urgent Priority</option>
                            </select>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Difficulty Level
                            </label>
                            <div className="relative">
                              <input
                                type="number"
                                min="1"
                                max="10"
                                value={newTask.difficulty_level}
                                onChange={(e) => setNewTask(prev => ({ ...prev, difficulty_level: e.target.value }))}
                                className="w-full px-4 py-2 pl-10 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors"
                                placeholder="1-10"
                              />
                              <svg className="w-5 h-5 text-gray-400 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                              </svg>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Assignment & Timeline Card */}
                      <div className="bg-white border border-gray-200 rounded-xl p-6">
                        <div className="flex items-center space-x-2 mb-4">
                          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <h3 className="text-lg font-semibold text-gray-900">Assignment & Timeline</h3>
                        </div>

                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Assign To
                            </label>
                            <div className="relative">
                              <select
                                value={newTask.assigned_to}
                                onChange={(e) => setNewTask(prev => ({ ...prev, assigned_to: e.target.value }))}
                                className="w-full px-4 py-2 pl-10 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors"
                              >
                                <option value="">Select an employee (optional)</option>
                                {managedEmployees.map((employee) => (
                                  <option key={employee.auth_id} value={employee.auth_id}>
                                    {employee.name} ({employee.email})
                                  </option>
                                ))}
                              </select>
                              <svg className="w-5 h-5 text-gray-400 absolute left-3 top-2.5 z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                              </svg>
                            </div>
                            {employeesLoading && (
                              <p className="text-sm text-gray-500 mt-1">Loading employees...</p>
                            )}
                            {employeesError && (
                              <p className="text-sm text-red-500 mt-1">Error loading employees: {employeesError}</p>
                            )}
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Due Date
                            </label>
                            <CalendarDatePicker
                              selectedDate={newTask.due_date}
                              onDateChange={(date) => setNewTask(prev => ({ ...prev, due_date: date }))}
                              placeholder="Select due date"
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Additional Details */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Project & Status Card */}
                      <div className="bg-white border border-gray-200 rounded-xl p-6">
                        <div className="flex items-center space-x-2 mb-4">
                          <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                          </svg>
                          <h3 className="text-lg font-semibold text-gray-900">Project & Status</h3>
                        </div>

                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Project
                            </label>
                            <select
                              value={newTask.project_id}
                              onChange={(e) => setNewTask(prev => ({ ...prev, project_id: e.target.value }))}
                              className="w-full px-3 py-2 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors"
                            >
                              <option value="">Select a project</option>
                              {projects.map((project) => (
                                <option key={project.id} value={project.id}>
                                  {project.name}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Status
                            </label>
                            <select
                              value={newTask.status}
                              onChange={(e) => setNewTask(prev => ({ ...prev, status: e.target.value }))}
                              className="w-full px-3 py-2 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors"
                            >
                              <option value="todo">📝 To Do</option>
                              <option value="in_progress">⚡ In Progress</option>
                              <option value="review">👁️ Review</option>
                              <option value="done">✅ Done</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      {/* Skills & Notes Card */}
                      <div className="bg-white border border-gray-200 rounded-xl p-6">
                        <div className="flex items-center space-x-2 mb-4">
                          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                          <h3 className="text-lg font-semibold text-gray-900">Skills & Notes</h3>
                        </div>

                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Required Skills
                            </label>
                            <input
                              type="text"
                              value={newTask.required_skills}
                              onChange={(e) => setNewTask(prev => ({ ...prev, required_skills: e.target.value }))}
                              className="w-full px-3 py-2 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors"
                              placeholder="JavaScript, React, Python"
                            />
                          </div>

                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                      <button
                        type="button"
                        onClick={() => setShowTaskModal(false)}
                        className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors duration-200"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5"
                      >
                        <span className="flex items-center space-x-2">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                          <span>Create Task</span>
                        </span>
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          )}

          {/* Employee Modal */}
          {showEmployeeModal && (
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-white w-full max-w-2xl max-h-[95vh] overflow-hidden rounded-2xl shadow-2xl">
                {/* Header */}
                <div className="bg-gradient-to-r from-green-600 to-blue-600 px-6 py-4">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                        </svg>
                      </div>
                      <div>
                        <h2 className="text-xl font-bold text-white">Add New Employee</h2>
                        <p className="text-green-100 text-sm">Create a new team member</p>
                      </div>
                    </div>
                    <button
                      onClick={() => setShowEmployeeModal(false)}
                      className="w-8 h-8 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center text-white transition-colors"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                {/* Form Content */}
                <div className="overflow-y-auto max-h-[calc(95vh-120px)]">
                  <form onSubmit={handleEmployeeSubmit} className="p-6 space-y-6">
                    {/* Employee Information Card */}
                    <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                      <div className="flex items-center space-x-2 mb-4">
                        <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        <h3 className="text-lg font-semibold text-gray-900">Employee Information</h3>
                      </div>

                      {/* Email */}
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Email Address <span className="text-red-500">*</span>
                        </label>
                        <div className="relative">
                          <input
                            type="email"
                            required
                            value={newEmployee.email}
                            onChange={(e) => setNewEmployee(prev => ({ ...prev, email: e.target.value }))}
                            className="w-full px-4 py-3 pl-10 bg-white border border-black rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-black transition-colors"
                            placeholder="employee@company.com"
                          />
                          <svg className="w-5 h-5 text-gray-400 absolute left-3 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                        </div>
                      </div>

                      {/* Name */}
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Full Name <span className="text-red-500">*</span>
                        </label>
                        <div className="relative">
                          <input
                            type="text"
                            required
                            value={newEmployee.name}
                            onChange={(e) => setNewEmployee(prev => ({ ...prev, name: e.target.value }))}
                            className="w-full px-4 py-3 pl-10 bg-white border border-black rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-black transition-colors"
                            placeholder="John Doe"
                          />
                          <svg className="w-5 h-5 text-gray-400 absolute left-3 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                        </div>
                      </div>

                      {/* Profile Picture URL */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Profile Picture URL
                        </label>
                        <div className="relative">
                          <input
                            type="url"
                            value={newEmployee.profile_picture}
                            onChange={(e) => setNewEmployee(prev => ({ ...prev, profile_picture: e.target.value }))}
                            className="w-full px-4 py-3 pl-10 bg-white border border-black rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-black transition-colors"
                            placeholder="https://example.com/profile.jpg"
                          />
                          <svg className="w-5 h-5 text-gray-400 absolute left-3 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Optional: Leave empty to use default profile picture</p>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                      <button
                        type="button"
                        onClick={() => setShowEmployeeModal(false)}
                        className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors duration-200"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-8 py-3 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5"
                      >
                        <span className="flex items-center space-x-2">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                          </svg>
                          <span>Add Employee</span>
                        </span>
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          )}

        </div>
    </div>
  );
};

export default Dashboard;
