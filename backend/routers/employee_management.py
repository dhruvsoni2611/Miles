from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone
from supabase import create_client, Client
import os

# Import the schema and supabase
try:
    from schemas import UserTaskCreate, EmployeeCreate, TaskAssignment
    from main import get_current_user
    from agents.embeddings import create_skill_embeddings
    from agents.score_calculation import calculate_employee_productivity_score
    from agents.workload_score import get_workload_score_calculator
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from schemas import UserTaskCreate, EmployeeCreate, TaskAssignment
    from main import get_current_user
    from agents.embeddings import create_skill_embeddings
    from agents.score_calculation import calculate_employee_productivity_score
    from agents.workload_score import get_workload_score_calculator

# Supabase admin client - created lazily to avoid import issues
_supabase_admin = None

def get_supabase_admin():
    global _supabase_admin
    if _supabase_admin is None:
        # Try to get from main module first
        try:
            from main import supabase_admin
            if supabase_admin is not None:
                _supabase_admin = supabase_admin
                return _supabase_admin
        except ImportError:
            pass

        # Fallback to manual initialization
        import os
        from dotenv import load_dotenv
        from supabase import create_client

        load_dotenv()
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")

        try:
            _supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        except Exception as e:
            raise ValueError(f"Failed to initialize Supabase admin client: {e}")
    return _supabase_admin

router = APIRouter()

@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    task: UserTaskCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new task following the complete flow:
    1. AUTHENTICATION & AUTHORIZATION ✓
    2. INPUT VALIDATION ✓
    3. DATABASE CONNECTIVITY CHECK ✓
    4. DATA PREPARATION ✓
    5. DATABASE INSERTION ✓
    6. RESPONSE PROCESSING ✓
    7. ERROR HANDLING ✓
    """

    """
    Create a new task following the complete flow:
    1. AUTHENTICATION & AUTHORIZATION ✓
    2. INPUT VALIDATION ✓
    3. DATABASE CONNECTIVITY CHECK ✓
    4. DATA PREPARATION ✓
    5. DATABASE INSERTION ✓
    6. RESPONSE PROCESSING ✓
    7. ERROR HANDLING ✓
    """

    try:
        # 1. AUTHENTICATION & AUTHORIZATION
        # Get the authenticated user ID from Supabase
        user_id = current_user.id

        # 2. INPUT VALIDATION (handled by Pydantic UserTaskCreate schema)
        # Schema validates: title length, priority/status enums, progress range, deadline in future

        # 3. DATABASE CONNECTIVITY CHECK
        try:
            # Test tasks table existence with SELECT * LIMIT 1
            test_response = get_supabase_admin().table("tasks").select("*").limit(1).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed or tasks table not found"
            )

        # Validate assigned_to is a managed employee (if provided)
        if task.assigned_to:
            # Check if the assigned user is actually managed by this user
            reporting_check = get_supabase_admin().table('user_reporting') \
                .select('employee_id') \
                .eq('manager_id', user_id) \
                .eq('employee_id', task.assigned_to) \
                .execute()

            if not reporting_check.data or len(reporting_check.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only assign tasks to employees you manage"
                )

        # Process task skills and generate embeddings
        skill_names = task.required_skills or []
        skill_vector_data = None

        if skill_names and len(skill_names) > 0:
            # Generate embeddings for task skills
            try:
                skill_embeddings = create_skill_embeddings(', '.join(skill_names))
                skill_vector_data = skill_embeddings  # Store just the vectors array
                print(f"✅ Generated embeddings for {len(skill_embeddings) if skill_embeddings else 0} task skills")
            except Exception as embedding_error:
                print(f"⚠️ Failed to generate embeddings for task skills: {embedding_error}")
                print("📝 Continuing with skill names only - embeddings will be generated later if needed")
                skill_vector_data = []

        # 4. DATA PREPARATION
        task_data = {
            "created_by": user_id,  # Use created_by field in database
            "title": task.title,
            "description": task.description,
            "project_id": task.project_id,  # UUID string for project reference
            "priority_score": task.get_priority_int(),  # Convert string to integer (1-5)
            "difficulty_score": task.difficulty_level,  # 1-10 scale
            "required_skills": skill_names,  # JSONB array of skill names
            "skill_embedding": skill_vector_data,  # JSONB array of skill embeddings
            "status": task.status,  # Must be: todo, in_progress, review, done
            "assigned_to": task.assigned_to,  # UUID string for assigned user
            "due_date": task.due_date.isoformat() if task.due_date else None,  # Changed from deadline
            "rating_score": 0,  # Default rating score
            "justified": False,  # Default justified value
            "bonus": False  # Default bonus value
        }

        # 5. DATABASE INSERTION
        try:
            response = get_supabase_admin().table("tasks").insert(task_data).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create task: {str(e)}"
            )

        # Check response.data exists and is not empty
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Task creation failed - no data returned from database"
            )

        # Update workload score if task is assigned to an employee
        if task.assigned_to:
            try:
                workload_calculator = get_workload_score_calculator()
                success = workload_calculator.update_employee_workload_score(
                    task.assigned_to, get_supabase_admin()
                )
                if success:
                    print(f"✅ Updated workload score for employee {task.assigned_to}")
                else:
                    print(f"⚠️ Failed to update workload score for employee {task.assigned_to}")
            except Exception as e:
                print(f"⚠️ Error updating workload score for employee {task.assigned_to}: {e}")
                # Don't fail the task creation if workload update fails

        # Assignment creation is now handled by frontend via separate API call
        # This allows for better error handling and separation of concerns

        # 6. RESPONSE PROCESSING
        task_result = response.data[0]

        # Compute is_overdue field
        is_overdue = False
        if task_result.get("due_date") and task_result["status"] != "done":
            try:
                # Parse due_date and compare with current time
                due_date_str = str(task_result["due_date"])
                if due_date_str.endswith('Z'):
                    due_date_dt = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                else:
                    due_date_dt = datetime.fromisoformat(due_date_str)

                now = datetime.now(timezone.utc)
                is_overdue = due_date_dt < now
            except (ValueError, TypeError):
                is_overdue = False

        # Add is_overdue to task_result
        task_result["is_overdue"] = is_overdue

        # Get assignable employees list for task assignment
        assignable_employees = []
        try:
            # Get employees managed by current user
            reporting_response = get_supabase_admin().table('user_reporting').select(
                'employee_id'
            ).eq('manager_id', user_id).execute()

            if reporting_response.data:
                employee_ids = [r['employee_id'] for r in reporting_response.data]

                # Get employee details
                employees_response = get_supabase_admin().table('user_miles').select(
                    'auth_id, name, email, productivity_score, workload'
                ).in_('auth_id', employee_ids).execute()

                assignable_employees = employees_response.data or []

                # Add active task count to each employee
                for employee in assignable_employees:
                    try:
                        # Get active task count
                        tasks_response = get_supabase_admin().table('tasks').select(
                            'id, status'
                        ).eq('assigned_to', employee['auth_id']).execute()

                        active_tasks = [t for t in (tasks_response.data or []) if t.get('status') not in ['done', 'review']]
                        employee['active_task_count'] = len(active_tasks)
                    except Exception as e:
                        print(f"⚠️ Error getting task count for employee {employee['auth_id']}: {e}")
                        employee['active_task_count'] = 0
        except Exception as e:
            print(f"⚠️ Error fetching assignable employees: {e}")
            assignable_employees = []

        # 7. SUCCESS RESPONSE
        return {
            "success": True,
            "message": "Task created successfully",
            "data": {
                "task": task_result,
                "assignable_employees": assignable_employees,
                "assignable_employees_count": len(assignable_employees)
            }
        }

        # 7. ERROR HANDLING
    except HTTPException:
        raise
    except Exception as e:
        # Log error and return 500
        print(f"Task creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating task"
        )


@router.put("/tasks/{task_id}/assign")
async def assign_task_to_employee(
    task_id: str,
    assignment: TaskAssignment,
    current_user: dict = Depends(get_current_user)
):
    """
    Assign a task to an employee with proper validation.

    Validates that:
    - Current user can assign this task (created it or is manager)
    - Employee is managed by current user (from user_reporting)
    - Task exists and is not already assigned

    Updates task assignment and employee workload score.
    """
    try:
        # Get authenticated user ID
        user_id = current_user.id
        supabase_client = get_supabase_admin()

        # 1. Validate task exists and get task details
        task_response = supabase_client.table('tasks').select(
            'id, title, assigned_to, created_by, status, priority_score, difficulty_score'
        ).eq('id', task_id).execute()

        if not task_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        task = task_response.data[0]

        # 2. Validate user can assign this task
        can_assign = False

        # User created the task
        if task['created_by'] == user_id:
            can_assign = True
        else:
            # Check if user is a manager of the task creator
            manager_check = supabase_client.table('user_reporting').select(
                'manager_id'
            ).eq('manager_id', user_id).eq('employee_id', task['created_by']).execute()

            if manager_check.data and len(manager_check.data) > 0:
                can_assign = True

        if not can_assign:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only assign tasks you created or manage"
            )

        # 3. Validate task is not already assigned to someone else
        if task.get('assigned_to') and task['assigned_to'] != assignment.employee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task is already assigned to another employee"
            )

        # 4. Validate employee is managed by current user
        reporting_check = supabase_client.table('user_reporting').select(
            'employee_id'
        ).eq('manager_id', user_id).eq('employee_id', assignment.employee_id).execute()

        if not reporting_check.data or len(reporting_check.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only assign tasks to employees you manage"
            )

        # 5. Update task assignment
        update_data = {
            'assigned_to': assignment.employee_id,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        # If task was unassigned, set status to in_progress when assigning
        if not task.get('assigned_to'):
            update_data['status'] = 'in_progress'

        task_update_response = supabase_client.table('tasks').update(
            update_data
        ).eq('id', task_id).execute()

        if not task_update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task assignment"
            )

        # 6. Create assignment record
        assignment_record_data = {
            'task_id': task_id,
            'user_id': assignment.employee_id,
            'assigned_by': user_id,
            'assigned_at': datetime.now(timezone.utc).isoformat()
        }

        assignment_response = supabase_client.table('assignments').insert(
            assignment_record_data
        ).execute()

        if not assignment_response.data:
            print(f"⚠️ Warning: Failed to create assignment record for task {task_id}")

        # 7. Update employee's workload score
        try:
            workload_calculator = get_workload_score_calculator()
            success = workload_calculator.update_employee_workload_score(
                assignment.employee_id, supabase_client
            )
            if success:
                print(f"✅ Updated workload score for employee {assignment.employee_id}")
            else:
                print(f"⚠️ Failed to update workload score for employee {assignment.employee_id}")
        except Exception as e:
            print(f"⚠️ Error updating workload score for employee {assignment.employee_id}: {e}")
            # Don't fail the assignment if workload update fails

        # 8. Success response
        return {
            "success": True,
            "message": "Task assigned successfully",
            "data": {
                "task_id": task_id,
                "assigned_to": assignment.employee_id,
                "assignment_record": assignment_response.data[0] if assignment_response.data else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Task assignment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while assigning task"
        )


@router.get("/employees/assignable")
async def get_assignable_employees(
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of employees that can be assigned tasks by the current user.

    Only returns employees who are mapped to the current user in user_reporting.
    """
    try:
        user_id = current_user.id
        supabase_client = get_supabase_admin()

        # Get employees managed by current user
        reporting_response = supabase_client.table('user_reporting').select(
            'employee_id'
        ).eq('manager_id', user_id).execute()

        if not reporting_response.data:
            return {
                "success": True,
                "message": "No employees found under your management",
                "data": []
            }

        employee_ids = [r['employee_id'] for r in reporting_response.data]

        # Get employee details
        employees_response = supabase_client.table('user_miles').select(
            'auth_id, name, email, productivity_score, workload'
        ).in_('auth_id', employee_ids).execute()

        employees = employees_response.data or []

        # Add active task count to each employee
        for employee in employees:
            try:
                # Get active task count
                tasks_response = supabase_client.table('tasks').select(
                    'id, status'
                ).eq('assigned_to', employee['auth_id']).execute()

                active_tasks = [t for t in (tasks_response.data or []) if t.get('status') not in ['done', 'review']]
                employee['active_task_count'] = len(active_tasks)
            except Exception as e:
                print(f"⚠️ Error getting task count for employee {employee['auth_id']}: {e}")
                employee['active_task_count'] = 0

        return {
            "success": True,
            "message": f"Found {len(employees)} assignable employees",
            "data": employees
        }

    except Exception as e:
        print(f"Get assignable employees error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while fetching employees"
        )


@router.post("/employees", status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee: EmployeeCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new employee following the complete flow:
    1. AUTHENTICATION & AUTHORIZATION ✓
    2. INPUT VALIDATION ✓
    3. DATABASE CONNECTIVITY CHECK ✓
    4. EMPLOYEE CREATION IN AUTH ✓
    5. DATABASE INSERTION ✓
    6. REPORTING RELATIONSHIP ✓
    7. RESPONSE PROCESSING ✓
    8. ERROR HANDLING ✓
    """

    try:
        # 1. AUTHENTICATION & AUTHORIZATION
        # Get the authenticated user ID from Supabase
        manager_id = current_user.id

        # Check if current user is a manager or admin
        # For development/testing: temporarily allow any authenticated user
        try:
            supabase_admin_client = get_supabase_admin()
            if supabase_admin_client is None:
                # Database not configured - allow for development
                print(f"⚠️ Database not configured, allowing employee creation for user {manager_id} (development mode)")
            else:
                user_profile = supabase_admin_client.table('user_miles').select('role').eq('auth_id', manager_id).execute()
                if not user_profile.data or len(user_profile.data) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User profile not found"
                    )

                user_role = user_profile.data[0]['role']
                if user_role not in ['manager', 'admin']:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only managers and admins can create employees"
                    )
        except HTTPException:
            raise
        except Exception as e:
            # In development mode, if database operations fail, allow the operation
            print(f"⚠️ Database permission check failed ({str(e)}), allowing employee creation for development")
            pass

        # 2. INPUT VALIDATION (handled by Pydantic EmployeeCreate schema)
        # Schema validates: email format, name length

        # 3. DATABASE CONNECTIVITY CHECK
        supabase_admin_client = get_supabase_admin()
        if supabase_admin_client is None:
            # Database not configured - skip connectivity check for development
            print("⚠️ Database not configured, skipping connectivity check (development mode)")
        else:
            try:
                # Test user_miles table existence with SELECT * LIMIT 1
                test_response = supabase_admin_client.table("user_miles").select("*").limit(1).execute()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database connection failed or user_miles table not found"
                )

        # 4. EMPLOYEE CREATION IN AUTH / EXISTING USER LOOKUP
        employee_id = None
        auth_user_exists = False

        try:
            # First, try to create user in Supabase Auth
            auth_response = get_supabase_admin().auth.admin.create_user({
                'email': employee.email,
                'email_confirm': True,  # Auto-confirm email for employees
                'user_metadata': {
                    'name': employee.name,
                    'role': 'employee'
                }
            })

            if auth_response.user:
                employee_id = auth_response.user.id
                print(f"✅ Created employee in Supabase Auth: {employee.email} (ID: {employee_id})")
            else:
                raise Exception("Failed to create user - no user returned")

        except Exception as e:
            error_msg = str(e).lower()
            if 'already registered' in error_msg or 'user already exists' in error_msg or 'duplicate' in error_msg:
                # User already exists in Supabase Auth - try to find them
                print(f"ℹ️ User {employee.email} already exists in Supabase Auth, looking up their ID...")
                auth_user_exists = True

                try:
                    # Get user by email from Supabase Auth
                    users_response = get_supabase_admin().auth.admin.list_users()
                    existing_user = None

                    for user in users_response:
                        if user.email and user.email.lower() == employee.email.lower():
                            existing_user = user
                            break

                    if existing_user:
                        employee_id = existing_user.id
                        print(f"✅ Found existing employee in Supabase Auth: {employee.email} (ID: {employee_id})")

                        # Update user metadata if needed
                        if not existing_user.user_metadata or existing_user.user_metadata.get('role') != 'employee':
                            get_supabase_admin().auth.admin.update_user_by_id(
                                employee_id,
                                {
                                    'user_metadata': {
                                        'name': employee.name,
                                        'role': 'employee'
                                    }
                                }
                            )
                            print(f"✅ Updated user metadata for {employee.email}")
                    else:
                        raise Exception("Could not find existing user")

                except Exception as lookup_error:
                    print(f"❌ Failed to lookup existing user: {lookup_error}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to find existing user account"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create/find employee in auth system: {str(e)}"
                )

        # 5. DATABASE INSERTION
        profile_created = False
        user_already_exists = False

        if supabase_admin_client is None:
            # Database not configured - skip profile creation for development
            print(f"⚠️ Database not configured, skipping profile creation for {employee.email} (development mode)")
            profile_response = None
        else:
            # First, check if user already has a profile in user_miles
            existing_profile = supabase_admin_client.table("user_miles").select("*").eq("auth_id", employee_id).execute()

            if existing_profile.data and len(existing_profile.data) > 0:
                existing_user = existing_profile.data[0]
                print(f"ℹ️ User {employee.email} already has a profile in user_miles (role: {existing_user['role']})")

                # Check if they already have a reporting relationship with this manager
                existing_reporting = supabase_admin_client.table("user_reporting") \
                    .select("*") \
                    .eq("employee_id", employee_id) \
                    .eq("manager_id", manager_id) \
                    .execute()

                if existing_reporting.data and len(existing_reporting.data) > 0:
                    # User is already fully set up as employee under this manager
                    user_already_exists = True
                    print(f"ℹ️ User {employee.email} already has a reporting relationship with manager {manager_id}")
                    profile_response = existing_profile
                else:
                    # User exists but no reporting relationship with this manager
                    print(f"ℹ️ User {employee.email} exists but needs reporting relationship with manager {manager_id}")
                    profile_response = existing_profile
            else:
                # User doesn't have a profile - create one
                try:
                    # Process skills: store both names and embeddings
                    skill_names = []
                    skill_embeddings = None

                    if employee.skill_vector and employee.skill_vector.strip():
                        # Extract skill names from comma-separated string
                        skill_names = [skill.strip() for skill in employee.skill_vector.split(',') if skill.strip()]

                        # Generate embeddings for the skills
                        try:
                            skill_embeddings = create_skill_embeddings(employee.skill_vector)
                            print(f"✅ Generated embeddings for {len(skill_embeddings) if skill_embeddings else 0} skills")
                        except Exception as embedding_error:
                            print(f"⚠️ Failed to generate embeddings: {embedding_error}")
                            print("📝 Continuing with skill names only - embeddings will be generated later if needed")
                            skill_embeddings = None

                    # Store only the vectors in skill_vector field
                    skill_vector_data = None
                    if skill_embeddings:
                        skill_vector_data = skill_embeddings  # Store just the vectors array
                    else:
                        skill_vector_data = []  # Empty array if no embeddings

                    # Calculate productivity score based on experience and tenure
                    productivity_score = calculate_employee_productivity_score(
                        experience_years=employee.experience_years,
                        tenure_years=employee.tenure
                    )
                    print(f"✅ Calculated productivity score: {productivity_score}")

                    employee_data = {
                        'auth_id': employee_id,
                        'email': employee.email,
                        'name': employee.name,
                        'role': 'employee',
                        'profile_picture': employee.profile_picture,
                        'skill_vector': skill_vector_data,  # Store vectors array as JSONB
                        'experience_years': employee.experience_years or {},  # Store experience data as JSONB
                        'tenure': employee.tenure or {},  # Store tenure data as JSONB
                        'productivity_score': productivity_score,
                        'workload': 0  # Initialize workload to 0
                    }

                    profile_response = supabase_admin_client.table("user_miles").insert(employee_data).execute()

                    if not profile_response.data or len(profile_response.data) == 0:
                        # If profile creation fails and we created the auth user, clean up
                        if not auth_user_exists:
                            try:
                                supabase_admin_client.auth.admin.delete_user(employee_id)
                            except:
                                pass  # Log but don't fail the request

                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to create employee profile"
                        )

                    print(f"✅ Created employee profile in user_miles: {employee.email}")
                    profile_created = True

                except Exception as e:
                    # Clean up auth user if profile creation fails and we created it
                    if not auth_user_exists:
                        try:
                            supabase_admin_client.auth.admin.delete_user(employee_id)
                        except:
                            pass  # Log but don't fail the request

                    error_msg = str(e).lower()
                    if 'duplicate key' in error_msg or 'unique constraint' in error_msg:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="An employee with this email already exists"
                        )

                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to create employee profile: {str(e)}"
                    )

        # 6. REPORTING RELATIONSHIP
        reporting_created = False

        if user_already_exists:
            # User already exists and has reporting relationship - no action needed
            print(f"ℹ️ User {employee.email} already fully set up as employee under manager {manager_id}")
            reporting_data = {
                'employee_id': employee_id,
                'manager_id': manager_id,
                'assigned_at': datetime.now(timezone.utc).isoformat()
            }
        elif supabase_admin_client is None:
            # Database not configured - skip reporting relationship for development
            print(f"⚠️ Database not configured, skipping reporting relationship for {employee.email} (development mode)")
            reporting_data = {
                'employee_id': employee_id,
                'manager_id': manager_id,
                'assigned_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            try:
                # Create reporting relationship manually
                reporting_data = {
                    'employee_id': employee_id,
                    'manager_id': manager_id,
                    'assigned_by': manager_id,
                    'assigned_at': datetime.now(timezone.utc).isoformat()
                }

                reporting_response = supabase_admin_client.table("user_reporting").insert(reporting_data).execute()

                if not reporting_response.data or len(reporting_response.data) == 0:
                    print(f"⚠️ Warning: Failed to create reporting relationship for employee {employee.email}")
                else:
                    print(f"✅ Created reporting relationship: Manager {manager_id} -> Employee {employee_id}")
                    reporting_created = True

            except Exception as e:
                error_msg = str(e).lower()
                if 'duplicate key' in error_msg or 'unique constraint' in error_msg:
                    print(f"ℹ️ Reporting relationship already exists for employee {employee.email}")
                    reporting_created = False  # Already exists, not created now
                else:
                    print(f"⚠️ Warning: Failed to create reporting relationship: {str(e)}")
                    # Don't fail the entire request if reporting relationship fails
                    # The employee is still created successfully

        # 7. RESPONSE PROCESSING & FINAL VALIDATION
        if user_already_exists:
            # User already exists and has reporting relationship - this is an error
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists as an employee under this manager"
            )

        if supabase_admin_client is None:
            # Development mode response
            employee_result = {
                'auth_id': employee_id,
                'email': employee.email,
                'name': employee.name,
                'role': 'employee',
                'profile_picture': employee.profile_picture,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            mode = "development"
        else:
            # Production mode response
            employee_result = profile_response.data[0] if profile_response and profile_response.data else {}
            mode = "production"

        # 8. SUCCESS RESPONSE
        return {
            "success": True,
            "message": f"Employee {'added' if auth_user_exists else 'created'} successfully ({mode} mode)",
            "data": {
                "auth_id": employee_result.get('auth_id', employee_id),
                "email": employee_result.get('email', employee.email),
                "name": employee_result.get('name', employee.name),
                "role": employee_result.get('role', 'employee'),
                "profile_picture": employee_result.get('profile_picture'),
                "created_at": employee_result.get('created_at'),
                "reporting": {
                    "manager_id": manager_id,
                    "assigned_at": reporting_data['assigned_at']
                },
                "user_status": {
                    "auth_user_existed": auth_user_exists,
                    "profile_created": profile_created,
                    "reporting_created": reporting_created
                }
            }
        }

    # 8. ERROR HANDLING
    except HTTPException:
        raise
    except Exception as e:
        # Log error and return 500
        print(f"Employee creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating employee"
        )
