import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Sidebar, SkillsSelection, SkillExperienceInput, TenureInput } from '../components';

const EmployeeManagement = () => {
  const [managedEmployees, setManagedEmployees] = useState([]);
  const [employeesLoading, setEmployeesLoading] = useState(false);
  const [employeesError, setEmployeesError] = useState(null);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const { ensureValidSession, isAuthenticated, user } = useAuth();

  // New employee form
  const [newEmployee, setNewEmployee] = useState({
    email: '',
    name: '',
    profile_picture: '',
    skill_vector: [],
    experience_years: {},
    tenure_years: {}
  });

  // Tenure skills state (separate from main skills)
  const [tenureSkills, setTenureSkills] = useState([]);

  // Fetch managed employees from API
  const fetchManagedEmployees = async () => {
    try {
      console.log('🔄 Starting to fetch managed employees...');
      setEmployeesLoading(true);
      setEmployeesError(null);

      // Ensure we have a valid token
      let token;
      try {
        console.log('🔐 Getting authentication token...');
        token = await ensureValidSession();
        console.log('✅ Got valid token');
      } catch (authError) {
        console.error('❌ Authentication error:', authError);
        setEmployeesError('Please login to view employees');
        setManagedEmployees([]);
        setEmployeesLoading(false);
        return;
      }

      console.log('📡 Making API call to /api/employees/managed');
      const response = await fetch('http://localhost:8000/api/employees/managed', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log('📥 API response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API error response:', errorText);
        throw new Error(`Failed to fetch employees: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ API response data:', data);
      setManagedEmployees(data.employees || []);
      console.log(`📊 Set ${data.employees?.length || 0} employees in state`);
    } catch (error) {
      console.error('❌ Error fetching managed employees:', error);
      setEmployeesError(error.message);
      setManagedEmployees([]);
    } finally {
      setEmployeesLoading(false);
      console.log('🏁 Finished fetching employees');
    }
  };

  const handleAddEmployee = () => {
    // Check if user is authenticated
    if (!isAuthenticated()) {
      alert('Please login to add employees');
      return;
    }

    // Check if user is manager or admin
    if (user?.role !== 'manager' && user?.role !== 'admin') {
      alert('Only managers and administrators can add employees.');
      return;
    }

    setShowEmployeeModal(true);
  };

  const handleEmployeeSubmit = async (e) => {
    e.preventDefault();

    // Check if user is authenticated
    if (!isAuthenticated()) {
      alert('Please login to create employees');
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
          return;
        }
        throw new Error(`Authentication failed: ${authError.message}`);
      }

      const employeeData = {
        email: newEmployee.email,
        name: newEmployee.name,
        profile_picture: newEmployee.profile_picture || null,
        skill_vector: newEmployee.skill_vector.length > 0 ? newEmployee.skill_vector.join(', ') : '',
        experience_years: newEmployee.experience_years || {},
        tenure: newEmployee.tenure_years || {}
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
        profile_picture: '',
        skill_vector: [],
        experience_years: {},
        tenure_years: {}
      });
      setTenureSkills([]);
      setShowEmployeeModal(false);

      // Refresh the employee list
      fetchManagedEmployees();

      // Show success message
      alert('Employee created successfully! Check console for employee data.');

    } catch (error) {
      console.error('Error creating employee:', error);
      alert(`Failed to create employee: ${error.message}`);
    }
  };

  useEffect(() => {
    if (user) {
      fetchManagedEmployees();
    }
  }, [user]);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 shadow-sm">
          <div className="w-full px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-4">
                <h1 className="text-2xl font-bold text-gray-900">Team</h1>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={fetchManagedEmployees}
                  disabled={employeesLoading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 rounded-lg text-white transition-colors flex items-center space-x-2 font-medium"
                >
                  <span>🔄</span>
                  <span>{employeesLoading ? 'Loading...' : 'Refresh'}</span>
                </button>
                <button
                  onClick={handleAddEmployee}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white transition-colors flex items-center space-x-2 font-medium"
                >
                  <span>👥</span>
                  <span>Add Employee</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-6">
          {/* Loading State */}
          {employeesLoading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-200 border-t-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 text-lg">Loading employees...</p>
            </div>
          )}

          {/* Error State */}
          {employeesError && (
            <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6 mb-6">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3 flex-1">
                  <h3 className="text-sm font-medium text-red-800">
                    Failed to load employees
                  </h3>
                  <div className="mt-1 text-sm text-red-600">
                    <p>{employeesError}</p>
                  </div>
                  <div className="mt-3">
                    <button
                      onClick={fetchManagedEmployees}
                      className="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded text-sm transition-colors border border-red-300"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Employee List */}
          {!employeesLoading && !employeesError && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">
                  Team Members ({managedEmployees.length})
                </h2>
              </div>

              {managedEmployees.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                  <div className="text-4xl mb-4">👥</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No employees found</h3>
                  <p className="text-gray-600 mb-4">Get started by adding your first team member.</p>
                  <button
                    onClick={handleAddEmployee}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white transition-colors font-medium"
                  >
                    Add First Employee
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {managedEmployees.map((employee) => (
                    <div key={employee.auth_id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                      <div className="flex items-center space-x-4 mb-4">
                        <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium text-lg">
                          {employee.name?.charAt(0)?.toUpperCase() || employee.email?.charAt(0)?.toUpperCase() || 'U'}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold text-gray-900 truncate">{employee.name}</h3>
                          <p className="text-sm text-gray-600 truncate">{employee.email}</p>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Role:</span>
                          <span className="font-medium capitalize">{employee.role || 'Employee'}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Status:</span>
                          <span className={`font-medium ${employee.is_active ? 'text-green-600' : 'text-red-600'}`}>
                            {employee.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        {/* Skills are now stored as vectors only - display removed */}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Employee Modal */}
        {showEmployeeModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white w-full max-w-5xl max-h-[95vh] overflow-hidden rounded-2xl shadow-2xl">
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
                    <div className="mb-4">
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

                    {/* Skills */}
                    <SkillsSelection
                      selectedSkills={newEmployee.skill_vector}
                      onSkillsChange={(skills) => setNewEmployee(prev => ({ ...prev, skill_vector: skills }))}
                      placeholder="Select employee skills..."
                    />

                    {/* Skill Experience */}
                    <SkillExperienceInput
                      selectedSkills={newEmployee.skill_vector}
                      experienceData={newEmployee.experience_years}
                      onExperienceChange={(experience) => setNewEmployee(prev => ({ ...prev, experience_years: experience }))}
                      placeholder="No skills selected yet..."
                    />

                    {/* Company Tenure */}
                    <TenureInput
                      selectedSkills={tenureSkills}
                      tenureData={newEmployee.tenure_years}
                      onTenureChange={(tenure) => setNewEmployee(prev => ({ ...prev, tenure_years: tenure }))}
                      onSkillsChange={setTenureSkills}
                      placeholder="Select skills for tenure tracking..."
                    />
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

export default EmployeeManagement;
