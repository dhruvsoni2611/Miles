import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Sidebar, SkillsSelection } from '../components';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

// Status icon helper
const getStatusIcon = (status) => {
  switch (status) {
    case 'assigned':
    case 'todo':
      return '📋';
    case 'in_progress':
      return '⚡';
    case 'review':
    case 'in_review':
      return '👁️';
    case 'completed':
    case 'done':
      return '✅';
    case 'overdue':
      return '🚨';
    default:
      return '📋';
  }
};

// Status color helper
const getStatusColor = (status) => {
  switch (status) {
    case 'completed':
    case 'done':
      return 'text-green-600';
    case 'in_progress':
      return 'text-yellow-600';
    case 'review':
    case 'in_review':
      return 'text-purple-600';
    case 'overdue':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
};

const Dashboard = () => {
  const navigate = useNavigate();
  const { logout, ensureValidSession, isAuthenticated, loading: authLoading, user } = useAuth();

  // Tasks state
  const [tasks, setTasks] = useState([]);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [tasksError, setTasksError] = useState(null);

  // View mode state
  const [viewMode, setViewMode] = useState('created'); // 'created' or 'assigned'

  // Drag and drop state
  const [draggedTask, setDraggedTask] = useState(null);
  const [dragOverStatus, setDragOverStatus] = useState(null);

  // Task creation modal state
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    priority_score: 2, // medium
    difficulty_score: 3, // medium
    required_skills: [],
    status: 'todo',
    due_date: null, // Changed to null for DatePicker
    project_id: '',
    assigned_to: '' // Employee assignment
  });
  const [taskCreating, setTaskCreating] = useState(false);
  const [createTaskAssignmentMode, setCreateTaskAssignmentMode] = useState('auto'); // 'auto' or 'manual' - default to 'auto'

  // Assignable employees state
  const [assignableEmployees, setAssignableEmployees] = useState([]);
  const [employeesLoading, setEmployeesLoading] = useState(false);

  // Task assignment modal state
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [taskToAssign, setTaskToAssign] = useState(null);
  const [assigningTask, setAssigningTask] = useState(false);
  const [assignmentMode, setAssignmentMode] = useState('auto'); // 'auto' or 'manual' - default to 'auto'

  // Task completion modal state
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [taskToComplete, setTaskToComplete] = useState(null);
  const [submittingCompletion, setSubmittingCompletion] = useState(false);

  useEffect(() => {
    // Only check auth after AuthContext has finished loading
    if (!authLoading) {
      checkAuth();
    }
  }, [authLoading]);

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

      // Fetch tasks based on view mode
      fetchTasks();

    } catch (error) {
      console.error('Dashboard: Auth check error:', error);
      alert('Authentication failed. Please login again.');
      navigate('/login');
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/login');
    }
  };

  // Fetch tasks based on current view mode
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

      // Choose API endpoint based on view mode
      const endpoint = viewMode === 'created'
        ? 'http://localhost:8000/api/tasks/created'  // tasks I created
        : 'http://localhost:8000/api/tasks';         // tasks assigned to me

      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch tasks: ${response.status}`);
      }

      const data = await response.json();
      const userTasks = data.tasks || [];

      setTasks(userTasks);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setTasksError(error.message);
      setTasks([]);
    } finally {
      setTasksLoading(false);
    }
  };

  // Fetch assignable employees for task creation
  const fetchAssignableEmployees = async () => {
    try {
      setEmployeesLoading(true);

      const token = await ensureValidSession();

      const response = await fetch('http://localhost:8000/api/employees/managed', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch assignable employees: ${response.status}`);
      }

      const data = await response.json();
      setAssignableEmployees(data.employees || []);
    } catch (error) {
      console.error('Error fetching assignable employees:', error);
      setAssignableEmployees([]);
    } finally {
      setEmployeesLoading(false);
    }
  };

  // Group tasks by status
  const tasksByStatus = {
    assigned: tasks.filter(task => task.status === 'todo' || task.status === 'assigned'),
    in_progress: tasks.filter(task => task.status === 'in_progress'),
    in_review: tasks.filter(task => task.status === 'review' || task.status === 'in_review'),
    completed: tasks.filter(task => task.status === 'completed' || task.status === 'done'),
    overdue: tasks.filter(task => {
      if (!task.due_date) return false;
      const dueDate = new Date(task.due_date);
      const today = new Date();
      return dueDate < today && task.status !== 'completed' && task.status !== 'done';
    })
  };

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

      // Prevent moving completed tasks to other statuses
      if (taskData.status === 'done' && newStatus !== 'done') {
        alert('Completed tasks cannot be moved to another status');
        return;
      }

      console.log('Updating task status:', taskData.id, 'from', taskData.status, 'to', newStatus);

      // Special handling for completion - show rating modal
      if (newStatus === 'done') {
        setTaskToComplete(taskData);
        setShowCompletionModal(true);
        return; // Don't proceed with normal update
      }

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

  const handleCreateTask = async (e) => {
    e.preventDefault();

    if (!newTask.title.trim()) {
      alert('Task title is required');
      return;
    }

    try {
      setTaskCreating(true);

      const token = await ensureValidSession();

      // Prepare task data for API
      // For auto assignment, don't include assigned_to (will be assigned after creation)
      // For manual assignment, include assigned_to if selected
      const taskData = {
        title: newTask.title.trim(),
        description: newTask.description.trim(),
        priority_score: newTask.priority_score,
        difficulty_score: newTask.difficulty_score,
        status: newTask.status,
        due_date: newTask.due_date ? newTask.due_date.toISOString() : null,
        required_skills: [], // Can be extended later
        assigned_to: createTaskAssignmentMode === 'manual' ? (newTask.assigned_to || null) : null,
        rating_score: 0,
        justified: false,
        bonus: false
      };

      // Validate manual assignment
      if (createTaskAssignmentMode === 'manual' && !newTask.assigned_to) {
        alert('Please select an employee for manual assignment');
        setTaskCreating(false);
        return;
      }

      const response = await fetch('http://localhost:8000/api/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(taskData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to create task: ${response.status}`);
      }

      const createdTaskResponse = await response.json();
      console.log('Task created successfully:', createdTaskResponse);

      const taskId = createdTaskResponse.data?.task?.id;

      // If auto assignment mode, assign task using RL agent
      if (createTaskAssignmentMode === 'auto' && taskId) {
        try {
          const assignResponse = await fetch(`http://localhost:8000/api/tasks/${taskId}/assign?use_bandit=true`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({}), // Empty body for auto assignment
          });

          if (!assignResponse.ok) {
            const errorData = await assignResponse.json();
            console.warn('Auto assignment failed:', errorData);
            // Don't fail task creation if assignment fails
          } else {
            console.log('Task auto-assigned successfully');
          }
        } catch (assignError) {
          console.warn('Auto assignment error:', assignError);
          // Don't fail task creation if assignment fails
        }
      }

      // Reset form and close modal
      setNewTask({
        title: '',
        description: '',
        priority_score: 2,
        difficulty_score: 3,
        required_skills: [],
        status: 'todo',
        due_date: null,
        project_id: '',
        assigned_to: ''
      });
      setCreateTaskAssignmentMode('auto'); // Reset to default
      setShowTaskModal(false);

      // Refresh tasks list
      await fetchTasks();

      const assignmentMessage = createTaskAssignmentMode === 'auto'
        ? 'Task created and auto-assigned using AI!'
        : newTask.assigned_to
        ? 'Task created and assigned successfully!'
        : 'Task created successfully!';
      alert(assignmentMessage);

    } catch (error) {
      console.error('Error creating task:', error);
      alert(`Failed to create task: ${error.message}`);
    } finally {
      setTaskCreating(false);
    }
  };

  // Handle task assignment
  const handleAssignTask = async (taskId, employeeId = null) => {
    // For manual mode, employeeId is required
    if (assignmentMode === 'manual' && !employeeId) {
      alert('Please select an employee');
      return;
    }

    try {
      setAssigningTask(true);

      const token = await ensureValidSession();

      // Build request URL with use_bandit parameter
      const useBandit = assignmentMode === 'auto';
      const url = `http://localhost:8000/api/tasks/${taskId}/assign${useBandit ? '?use_bandit=true' : ''}`;

      // Build request body
      const requestBody = {};
      if (employeeId) {
        requestBody.employee_id = employeeId;
      }

      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to assign task: ${response.status}`);
      }

      const result = await response.json();
      console.log('Task assigned successfully:', result);

      // Close modal and refresh tasks
      setShowAssignModal(false);
      setTaskToAssign(null);
      setAssignmentMode('auto'); // Reset to default
      await fetchTasks();

      const assignmentMessage = assignmentMode === 'auto'
        ? 'Task assigned automatically using AI recommendation!'
        : 'Task assigned successfully!';
      alert(assignmentMessage);

    } catch (error) {
      console.error('Error assigning task:', error);
      alert(`Failed to assign task: ${error.message}`);
    } finally {
      setAssigningTask(false);
    }
  };

  // Handle task completion with automatic RL feedback calculation
  const handleTaskCompletion = async (taskId) => {
    try {
      setSubmittingCompletion(true);

      const token = await ensureValidSession();

      const response = await fetch(`http://localhost:8000/api/tasks/${taskId}/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          confirm: true
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to complete task: ${response.status}`);
      }

      const result = await response.json();
      console.log('Task completed with automatic RL feedback:', result);

      // Close modal and refresh tasks
      setShowCompletionModal(false);
      setTaskToComplete(null);
      await fetchTasks();

      // Show performance summary
      const metrics = result.data?.calculated_metrics;
      if (metrics) {
        const rewards = Object.entries(metrics.rewards).filter(([_, value]) => value).map(([key, _]) => key.replace('r_', '').replace('_', ' '));
        const penalties = Object.entries(metrics.penalties).filter(([_, value]) => value).map(([key, _]) => key.replace('p_', ''));

        let message = `Task completed successfully!\n\nPerformance Metrics:\n`;
        message += `Completion Time: ${metrics.completion_time_days} days\n`;

        if (rewards.length > 0) {
          message += `Rewards Earned: ${rewards.join(', ')}\n`;
        }
        if (penalties.length > 0) {
          message += `Penalties: ${penalties.join(', ')}\n`;
        }

        alert(message);
      } else {
        alert('Task completed successfully!');
      }

    } catch (error) {
      console.error('Error completing task:', error);
      alert(`Failed to complete task: ${error.message}`);
    } finally {
      setSubmittingCompletion(false);
    }
  };

  if (authLoading) {
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
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Title Bar */}
        <div className="bg-white border-b border-gray-200 shadow-sm">
          <div className="w-full px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-4">
                <h1 className="text-2xl font-bold text-gray-900">
                  {viewMode === 'created' ? 'Tasks I Created' : 'My Tasks'}
                </h1>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => {
                    setViewMode('assigned');
                    fetchTasks();
                  }}
                  className={`px-4 py-2 rounded-lg text-white transition-colors font-medium ${
                    viewMode === 'assigned'
                      ? 'bg-blue-600 hover:bg-blue-700'
                      : 'bg-gray-500 hover:bg-gray-600'
                  }`}
                >
                  My Tasks
                </button>
                <button
                  onClick={() => {
                    setViewMode('created');
                    fetchTasks();
                  }}
                  className={`px-4 py-2 rounded-lg text-white transition-colors font-medium ${
                    viewMode === 'created'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-gray-500 hover:bg-gray-600'
                  }`}
                >
                  Tasks I Created
                </button>
                <button
                  onClick={() => {
                    setShowTaskModal(true);
                    fetchAssignableEmployees(); // Fetch employees when modal opens
                  }}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white transition-colors font-medium flex items-center space-x-2"
                >
                  <span>➕</span>
                  <span>Create Task</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">

            {/* Tasks Display */}
            {user?.role === 'admin' && (
              <>
                <div className="flex justify-between items-center mb-8">
                  <h2 className="text-3xl font-bold text-gray-900">
                    {viewMode === 'created' ? 'Tasks I Created' : 'My Assigned Tasks'}
                  </h2>
                </div>

                {/* Loading State */}
                {tasksLoading && (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-200 border-t-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600 text-lg">Loading your tasks...</p>
                  </div>
                )}

                {/* Error State */}
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
                      </div>
                    </div>
                  </div>
                )}

                {/* Task Compartments */}
                {!tasksLoading && !tasksError && (
                  <>
                    {tasks.length === 0 ? (
                      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                        <div className="text-4xl mb-4">📋</div>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                          {viewMode === 'created' ? 'No tasks created yet' : 'No tasks assigned to you'}
                        </h3>
                        <p className="text-gray-600 mb-4">
                          {viewMode === 'created'
                            ? 'Tasks you create will appear here.'
                            : 'Tasks assigned to you will appear here.'
                          }
                        </p>
                        {viewMode === 'created' && (
                          <p className="text-sm text-gray-500">Use the "My Tasks" view to see tasks assigned to you.</p>
                        )}
                      </div>
                    ) : (
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

                                  <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                                    <span className="font-medium">
                                      👤 {task.assigned_to || 'Not assigned'}
                                    </span>
                                    {!task.assigned_to && viewMode === 'created' && (
                                      <button
                                        onClick={() => {
                                          setTaskToAssign(task);
                                          setShowAssignModal(true);
                                          fetchAssignableEmployees();
                                        }}
                                        className="px-2 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded transition-colors"
                                      >
                                        Assign
                                      </button>
                                    )}
                                  </div>

                                  <div className="flex items-center justify-between text-xs text-gray-500">
                                    <span className={`font-medium ${getStatusColor(task.status)}`}>
                                      {getStatusIcon(task.status)} {task.status.replace('_', ' ')}
                                    </span>
                                    {task.due_date && (
                                      <span className={`font-medium ${task.is_overdue ? 'text-red-600' : 'text-gray-600'}`}>
                                        Due: {new Date(task.due_date).toLocaleDateString()}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              ))}

                              {tasksByStatus.assigned.length === 0 && (
                                <div className="text-center py-8 text-gray-400">
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
                                <div className="text-center py-8 text-gray-400">
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
                                <div className="text-center py-8 text-gray-400">
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
                                <div className="text-center py-8 text-gray-400">
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
                                  {task.due_date && (
                                    <div className="text-xs text-red-600 font-medium">
                                      Due: {new Date(task.due_date).toLocaleDateString()}
                                    </div>
                                  )}
                                </div>
                              ))}

                              {tasksByStatus.overdue.length === 0 && (
                                <div className="text-center py-8 text-gray-400">
                                  <div className="text-2xl mb-2">{getStatusIcon('overdue')}</div>
                                  <p className="text-sm">No overdue tasks</p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Quick Stats */}
                        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
                            <div className="text-2xl font-bold text-gray-900">{tasks.length}</div>
                            <div className="text-sm text-gray-600">Total Created</div>
                          </div>
                          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
                            <div className="text-2xl font-bold text-blue-600">{tasksByStatus.assigned.length}</div>
                            <div className="text-sm text-gray-600">Active</div>
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
                      </>
                    )}
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Task Creation Modal */}
      {showTaskModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-2xl max-h-[95vh] overflow-hidden rounded-2xl shadow-2xl">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4">
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">Create New Task</h2>
                    <p className="text-purple-100 text-sm">Add a new task to your project</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setShowTaskModal(false);
                    setCreateTaskAssignmentMode('auto'); // Reset to default
                  }}
                  className="w-8 h-8 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center text-white transition-colors"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Form Content */}
            <div className="overflow-y-auto max-h-[calc(95vh-120px)]">
              <form onSubmit={handleCreateTask} className="p-6 space-y-6">
                {/* Task Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Task Title <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={newTask.title}
                    onChange={(e) => setNewTask(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full px-4 py-3 bg-white border border-black rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-black transition-colors"
                    placeholder="Enter task title..."
                  />
                </div>

                {/* Task Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={newTask.description}
                    onChange={(e) => setNewTask(prev => ({ ...prev, description: e.target.value }))}
                    rows={3}
                    className="w-full px-4 py-3 bg-white border border-black rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-black transition-colors"
                    placeholder="Enter task description..."
                  />
                </div>

                {/* Priority and Difficulty */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Priority Score <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={newTask.priority_score}
                      onChange={(e) => setNewTask(prev => ({ ...prev, priority_score: parseInt(e.target.value) }))}
                      className="w-full px-4 py-3 bg-white border border-black rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-black transition-colors"
                    >
                      <option value={1}>1 - Low</option>
                      <option value={2}>2 - Medium-Low</option>
                      <option value={3}>3 - Medium</option>
                      <option value={4}>4 - Medium-High</option>
                      <option value={5}>5 - High</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Difficulty Score <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={newTask.difficulty_score}
                      onChange={(e) => setNewTask(prev => ({ ...prev, difficulty_score: parseInt(e.target.value) }))}
                      className="w-full px-4 py-3 bg-white border border-black rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-black transition-colors"
                    >
                      <option value={1}>1 - Very Easy</option>
                      <option value={2}>2 - Easy</option>
                      <option value={3}>3 - Medium</option>
                      <option value={4}>4 - Hard</option>
                      <option value={5}>5 - Very Hard</option>
                      <option value={6}>6 - Expert</option>
                      <option value={7}>7 - Expert+</option>
                      <option value={8}>8 - Specialist</option>
                      <option value={9}>9 - Master</option>
                      <option value={10}>10 - Grandmaster</option>
                    </select>
                  </div>
                </div>

                {/* Required Skills */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Required Skills
                  </label>
                  <SkillsSelection
                    selectedSkills={newTask.required_skills}
                    onSkillsChange={(skills) => setNewTask(prev => ({ ...prev, required_skills: skills }))}
                    placeholder="Select skills required for this task..."
                  />
                </div>

                {/* Due Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Due Date
                  </label>
                  <div className="relative">
                    <DatePicker
                      selected={newTask.due_date}
                      onChange={(date) => setNewTask(prev => ({ ...prev, due_date: date }))}
                      dateFormat="yyyy-MM-dd hh:mm aa"
                      showTimeSelect
                      timeFormat="HH:mm"
                      timeIntervals={15}
                      minDate={new Date()}
                      placeholderText="Select due date and time"
                      className="w-full px-4 py-3 bg-white border border-black rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-black transition-colors"
                      wrapperClassName="w-full"
                    />
                    <div className="absolute right-3 top-3 pointer-events-none">
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Assignment Mode Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Assignment Mode
                  </label>
                  <div className="flex space-x-4">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        name="createTaskAssignmentMode"
                        value="auto"
                        checked={createTaskAssignmentMode === 'auto'}
                        onChange={(e) => setCreateTaskAssignmentMode(e.target.value)}
                        disabled={taskCreating}
                        className="w-4 h-4 text-purple-600 focus:ring-purple-500"
                      />
                      <span className="text-sm font-medium text-gray-700">
                        🤖 Auto Assignment
                      </span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        name="createTaskAssignmentMode"
                        value="manual"
                        checked={createTaskAssignmentMode === 'manual'}
                        onChange={(e) => setCreateTaskAssignmentMode(e.target.value)}
                        disabled={taskCreating}
                        className="w-4 h-4 text-purple-600 focus:ring-purple-500"
                      />
                      <span className="text-sm font-medium text-gray-700">
                        👤 Manual Selection
                      </span>
                    </label>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {createTaskAssignmentMode === 'auto' 
                      ? 'AI will automatically select the best employee based on skills and performance'
                      : 'You will manually select an employee from the list'}
                  </p>
                </div>

                {/* Employee Selection (only shown for manual mode) */}
                {createTaskAssignmentMode === 'manual' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Employee <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <select
                        value={newTask.assigned_to}
                        onChange={(e) => setNewTask(prev => ({ ...prev, assigned_to: e.target.value }))}
                        className="w-full px-4 py-3 pl-10 bg-white border border-black rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-black transition-colors"
                        disabled={employeesLoading || taskCreating}
                      >
                        <option value="">
                          {employeesLoading ? 'Loading employees...' : 'Choose an employee'}
                        </option>
                        {assignableEmployees.map((employee) => (
                          <option key={employee.auth_id} value={employee.auth_id}>
                            {employee.name} ({employee.email})
                          </option>
                        ))}
                      </select>
                      <div className="absolute left-3 top-3 pointer-events-none">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      </div>
                    </div>
                    {assignableEmployees.length > 0 && (
                      <p className="text-xs text-gray-500 mt-1">
                        {assignableEmployees.length} employees available for assignment
                      </p>
                    )}
                  </div>
                )}

                {/* Auto Assignment Info */}
                {createTaskAssignmentMode === 'auto' && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <svg className="w-5 h-5 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <p className="text-sm font-medium text-purple-900 mb-1">
                          AI-Powered Assignment
                        </p>
                        <p className="text-xs text-purple-700">
                          The system will automatically select the best employee using:
                          <br />• Skill similarity matching (OpenAI embeddings)
                          <br />• Contextual bandit algorithm (performance-based learning)
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={() => {
                      setShowTaskModal(false);
                      setCreateTaskAssignmentMode('auto'); // Reset to default
                    }}
                    className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors duration-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={taskCreating}
                    className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {taskCreating ? (
                      <span className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                        <span>Creating...</span>
                      </span>
                    ) : (
                      <span className="flex items-center space-x-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        <span>Create Task</span>
                      </span>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Task Assignment Modal */}
      {showAssignModal && taskToAssign && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-md max-h-[95vh] overflow-hidden rounded-2xl shadow-2xl">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">Assign Task</h2>
                    <p className="text-blue-100 text-sm">Assign task to an employee</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setShowAssignModal(false);
                    setTaskToAssign(null);
                    setAssignmentMode('auto'); // Reset to default
                  }}
                  className="w-8 h-8 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center text-white transition-colors"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Task Info */}
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <h3 className="font-medium text-gray-900 mb-1">{taskToAssign.title}</h3>
              <p className="text-sm text-gray-600">
                {taskToAssign.priority === 'urgent' && '🔴 '}
                {taskToAssign.priority === 'high' && '🟠 '}
                {taskToAssign.priority === 'medium' && '🟡 '}
                {taskToAssign.priority === 'low' && '🟢 '}
                {taskToAssign.priority} priority
              </p>
            </div>

            {/* Form Content */}
            <div className="p-6">
              <div className="space-y-4">
                {/* Assignment Mode Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Assignment Mode
                  </label>
                  <div className="flex space-x-4">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        name="assignmentMode"
                        value="auto"
                        checked={assignmentMode === 'auto'}
                        onChange={(e) => setAssignmentMode(e.target.value)}
                        disabled={assigningTask}
                        className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm font-medium text-gray-700">
                        🤖 Auto Assignment
                      </span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        name="assignmentMode"
                        value="manual"
                        checked={assignmentMode === 'manual'}
                        onChange={(e) => setAssignmentMode(e.target.value)}
                        disabled={assigningTask}
                        className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm font-medium text-gray-700">
                        👤 Manual Selection
                      </span>
                    </label>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {assignmentMode === 'auto' 
                      ? 'AI will automatically select the best employee based on skills and performance'
                      : 'You will manually select an employee from the list'}
                  </p>
                </div>

                {/* Employee Selection (only shown for manual mode) */}
                {assignmentMode === 'manual' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Employee <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="employeeSelect"
                      className="w-full px-4 py-3 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors"
                      disabled={employeesLoading || assigningTask}
                      defaultValue=""
                    >
                      <option value="" disabled>
                        {employeesLoading ? 'Loading employees...' : 'Choose an employee'}
                      </option>
                      {assignableEmployees.map((employee) => (
                        <option key={employee.auth_id} value={employee.auth_id}>
                          {employee.name} ({employee.email})
                        </option>
                      ))}
                    </select>
                    {assignableEmployees.length > 0 && (
                      <p className="text-xs text-gray-500 mt-1">
                        {assignableEmployees.length} employees available for assignment
                      </p>
                    )}
                  </div>
                )}

                {/* Auto Assignment Info */}
                {assignmentMode === 'auto' && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <p className="text-sm font-medium text-blue-900 mb-1">
                          AI-Powered Assignment
                        </p>
                        <p className="text-xs text-blue-700">
                          The system will automatically select the best employee using:
                          <br />• Skill similarity matching (OpenAI embeddings)
                          <br />• Contextual bandit algorithm (performance-based learning)
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-end space-x-4 pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAssignModal(false);
                      setTaskToAssign(null);
                      setAssignmentMode('auto'); // Reset to default
                    }}
                    disabled={assigningTask}
                    className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors duration-200 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (assignmentMode === 'manual') {
                        const selectElement = document.getElementById('employeeSelect');
                        const employeeId = selectElement.value;
                        if (employeeId) {
                          handleAssignTask(taskToAssign.id, employeeId);
                        } else {
                          alert('Please select an employee');
                        }
                      } else {
                        // Auto mode - no employee selection needed
                        handleAssignTask(taskToAssign.id);
                      }
                    }}
                    disabled={assigningTask || (assignmentMode === 'manual' && employeesLoading)}
                    className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {assigningTask ? (
                      <span className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                        <span>Assigning...</span>
                      </span>
                    ) : (
                      <span className="flex items-center space-x-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        <span>Assign Task</span>
                      </span>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Task Completion Modal */}
      {showCompletionModal && taskToComplete && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-md max-h-[95vh] overflow-hidden rounded-2xl shadow-2xl">
            {/* Header */}
            <div className="bg-gradient-to-r from-green-600 to-blue-600 px-6 py-4">
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">Complete Task</h2>
                    <p className="text-green-100 text-sm">Automatic performance evaluation</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setShowCompletionModal(false);
                    setTaskToComplete(null);
                  }}
                  className="w-8 h-8 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center text-white transition-colors"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Task Info */}
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <h3 className="font-medium text-gray-900 mb-1">{taskToComplete.title}</h3>
              <p className="text-sm text-gray-600">How was the task completed?</p>
            </div>

            {/* Confirmation Form */}
            <div className="p-6">
              <div className="space-y-4">
                {/* Performance Preview */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-blue-800 mb-2">Performance Evaluation</h4>
                  <p className="text-sm text-blue-700">
                    When you complete this task, the system will automatically evaluate performance based on:
                  </p>
                  <ul className="text-sm text-blue-700 mt-2 space-y-1">
                    <li>• Completion time vs expected time for difficulty</li>
                    <li>• On-time delivery (before due date)</li>
                    <li>• Task difficulty and priority</li>
                    <li>• Speed bonuses for quick completion</li>
                  </ul>
                  <p className="text-sm text-blue-700 mt-2 font-medium">
                    RL feedback will be automatically recorded for learning.
                  </p>
                </div>

                {/* Confirmation Question */}
                <div className="text-center">
                  <p className="text-gray-700 font-medium mb-4">
                    Are you sure you want to mark this task as completed?
                  </p>
                  <p className="text-sm text-gray-500">
                    This action will evaluate your performance and update the task status.
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-end space-x-4 pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCompletionModal(false);
                      setTaskToComplete(null);
                    }}
                    disabled={submittingCompletion}
                    className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors duration-200 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      handleTaskCompletion(taskToComplete.id);
                    }}
                    disabled={submittingCompletion}
                    className="px-6 py-3 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submittingCompletion ? (
                      <span className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                        <span>Completing...</span>
                      </span>
                    ) : (
                      <span className="flex items-center space-x-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>Complete Task</span>
                      </span>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;