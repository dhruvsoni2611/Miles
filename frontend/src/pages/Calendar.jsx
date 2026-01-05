import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const Calendar = () => {
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState([]);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [tasksError, setTasksError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const navigate = useNavigate();
  const { logout, ensureValidSession, isAuthenticated, loading: authLoading, user } = useAuth();

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
      setTasks([]);
    } finally {
      setTasksLoading(false);
    }
  };

  useEffect(() => {
    // Only check auth after AuthContext has finished loading
    if (!authLoading) {
      checkAuth();
    }
  }, [authLoading]);

  // Fetch tasks when user is authenticated
  useEffect(() => {
    if (user) {
      fetchTasks();
    }
  }, [user]);

  const checkAuth = async () => {
    try {
      // Check if user is authenticated via AuthContext
      if (!isAuthenticated()) {
        console.log('Calendar: No authenticated user, redirecting to login');
        navigate('/login');
        return;
      }

      // Check user role - allow managers and admins to access calendar
      if (!user || (user.role !== 'manager' && user.role !== 'admin')) {
        console.log('Calendar: User does not have required role (manager/admin)');
        alert('Access denied. Only managers and administrators can access the calendar.');
        navigate('/login');
        return;
      }

      console.log('Calendar: Authentication successful for user:', user.email, 'role:', user.role);

    } catch (error) {
      console.error('Calendar: Auth check error:', error);
      alert('Authentication failed. Please login again.');
      navigate('/login');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      console.log('Demo: Logging out');
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/login');
    }
  };

  // Group tasks by due date
  const tasksByDueDate = tasks.reduce((acc, task) => {
    if (!task.due_date) {
      if (!acc['no-due-date']) acc['no-due-date'] = [];
      acc['no-due-date'].push(task);
      return acc;
    }

    const dateKey = new Date(task.due_date).toDateString();
    if (!acc[dateKey]) acc[dateKey] = [];
    acc[dateKey].push(task);
    return acc;
  }, {});

  // Get tasks for selected date
  const selectedDateKey = selectedDate.toDateString();
  const selectedDateTasks = tasksByDueDate[selectedDateKey] || [];

  // Get upcoming tasks (next 7 days)
  const getUpcomingTasks = () => {
    const today = new Date();
    const upcomingTasks = [];

    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      const dateKey = date.toDateString();

      if (tasksByDueDate[dateKey]) {
        upcomingTasks.push({
          date: dateKey,
          tasks: tasksByDueDate[dateKey],
          isToday: i === 0,
          isTomorrow: i === 1
        });
      }
    }

    return upcomingTasks;
  };

  const upcomingTasks = getUpcomingTasks();

  const getStatusColor = (status) => {
    switch (status) {
      case 'todo': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'review': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'done': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'urgent': return '🔴';
      case 'high': return '🟠';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  };

  if (loading || authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-2 border-blue-200 border-t-blue-600 mx-auto"></div>
          <p className="mt-6 text-gray-600 font-medium">Loading calendar...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="w-full px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span>Back to Dashboard</span>
              </button>
              <div className="h-10 w-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">Task Calendar</h1>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Welcome, {user?.name || user?.email?.split('@')[0]}</span>
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

      {/* Main Content */}
      <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Calendar Picker */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Date</h2>
              <DatePicker
                selected={selectedDate}
                onChange={(date) => setSelectedDate(date)}
                inline
                minDate={new Date()}
                className="w-full"
              />
            </div>

            {/* Upcoming Tasks Summary */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Tasks</h2>
              <div className="space-y-3">
                {upcomingTasks.map((day, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className={`text-sm font-medium ${
                        day.isToday ? 'text-blue-600' :
                        day.isTomorrow ? 'text-orange-600' : 'text-gray-600'
                      }`}>
                        {day.isToday ? 'Today' :
                         day.isTomorrow ? 'Tomorrow' :
                         day.date.split(' ').slice(0, 3).join(' ')}
                      </span>
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                        {day.tasks.length} tasks
                      </span>
                    </div>
                    <div className="space-y-1">
                      {day.tasks.slice(0, 3).map((task) => (
                        <div key={task.id} className="flex items-center space-x-2">
                          <span className="text-xs">{getPriorityIcon(task.priority)}</span>
                          <span className="text-xs text-gray-600 truncate">{task.title}</span>
                        </div>
                      ))}
                      {day.tasks.length > 3 && (
                        <span className="text-xs text-gray-500">+{day.tasks.length - 3} more</span>
                      )}
                    </div>
                  </div>
                ))}
                {upcomingTasks.length === 0 && (
                  <p className="text-gray-500 text-sm">No upcoming tasks</p>
                )}
              </div>
            </div>
          </div>

          {/* Tasks for Selected Date */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  Tasks for {selectedDate.toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </h2>
                <span className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                  {selectedDateTasks.length} tasks
                </span>
              </div>

              {tasksLoading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-200 border-t-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600 text-lg">Loading tasks...</p>
                </div>
              ) : tasksError ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800">{tasksError}</p>
                  <button
                    onClick={fetchTasks}
                    className="mt-2 bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded text-sm transition-colors"
                  >
                    Try Again
                  </button>
                </div>
              ) : selectedDateTasks.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <h3 className="mt-4 text-lg font-medium text-gray-900">No tasks due</h3>
                  <p className="mt-2 text-gray-500">No tasks are scheduled for this date.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {selectedDateTasks.map((task) => (
                    <div key={task.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <h3 className="text-lg font-medium text-gray-900 mb-1">{task.title}</h3>
                          {task.description && (
                            <p className="text-gray-600 text-sm mb-2">{task.description}</p>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(task.status)}`}>
                            {task.status.replace('_', ' ')}
                          </span>
                          <span className="text-sm">{getPriorityIcon(task.priority)}</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-sm text-gray-500">
                        <div className="flex items-center space-x-4">
                          <span>Difficulty: {task.difficulty_level}/10</span>
                          {task.progress !== undefined && (
                            <span>Progress: {task.progress}%</span>
                          )}
                        </div>
                        {task.assigned_to && (
                          <span className="flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            Assigned
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Calendar;
