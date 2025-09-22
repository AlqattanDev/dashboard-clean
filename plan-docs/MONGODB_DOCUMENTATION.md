# MongoDB Database Structure Documentation

## Overview
The clean dashboard uses MongoDB with Beanie ODM for data persistence. This document outlines all required collections, models, and relationships.

## Collections

### 1. Users Collection
**Collection Name**: `users`

**Fields**:
- `_id`: ObjectId (auto-generated)
- `username`: String (3-50 chars, unique, required)
- `email`: EmailStr (unique, required)
- `full_name`: String (optional)
- `role`: Enum ["admin", "leader", "member"] (default: "member")
- `is_active`: Boolean (default: true)
- `created_at`: DateTime (UTC, auto-generated)
- `last_login`: DateTime (UTC, optional)
- `password_hash`: String (optional, for local auth)
- `ldap_dn`: String (optional, for LDAP auth)

**Indexes**:
- `username` (unique)
- `email` (unique)
- `role`
- `is_active`
- `created_at`

**Role Hierarchy**:
```python
ROLE_HIERARCHY = {"admin": 1, "leader": 2, "member": 3}
```

**Key Methods**:
- `can_execute_function(required_role)` - Check if user can execute function
- `can_modify_user(target_user)` - Check if user can modify another user
- `can_view_user_data(target_user)` - Check if user can view another user's data

### 2. Functions Collection
**Collection Name**: `functions`

**Fields**:
- `_id`: ObjectId (auto-generated)
- `name`: String (1-200 chars, required)
- `description`: String (max 1000 chars, optional)
- `api_endpoint`: String (required)
- `http_method`: Enum ["GET", "POST", "PUT", "DELETE", "PATCH"] (default: "POST")
- `min_role`: RoleType (default: "admin")
- `required_fields`: List[Dict] (JSON schema for parameters)
- `url_parameters`: List[String] (parameters to append to URL)
- `request_headers`: Dict[String, String] (custom headers)
- `timeout`: Integer (1-300 seconds, default: 30)
- `is_active`: Boolean (default: true)
- `created_at`: DateTime (UTC, auto-generated)
- `updated_at`: DateTime (UTC, auto-updated)

**Indexes**:
- `name`
- `min_role`
- `is_active`
- `created_at`

**Key Methods**:
- `get_active_functions()` - Get all active functions
- `get_functions_for_role(user_role)` - Get functions accessible to role

### 3. Requests Collection
**Collection Name**: `requests`

**Fields**:
- `_id`: ObjectId (auto-generated)
- `user`: Link[User] (foreign key to users)
- `function`: Link[Function] (foreign key to functions)
- `parameters`: Dict (function execution parameters)
- `status`: Enum ["pending", "approved", "rejected", "completed"] (default: "pending")
- `reviewed_by`: Link[User] (optional, who approved/rejected)
- `reviewed_at`: DateTime (UTC, optional)
- `rejection_reason`: String (optional)
- `execution_result`: Dict (optional, function response)
- `execution_time_ms`: Integer (optional, execution duration)
- `error_message`: String (optional, if execution failed)
- `created_at`: DateTime (UTC, auto-generated)
- `updated_at`: DateTime (UTC, auto-updated)

**Indexes**:
- `status`
- `created_at`
- `user`
- `function`

**Key Methods**:
- `approve(reviewer)` - Approve request
- `reject(reviewer, reason)` - Reject request
- `complete(result, execution_time)` - Mark as completed
- `fail(error_message)` - Mark as failed
- `get_pending_requests()` - Get all pending requests
- `get_user_requests(user_id)` - Get requests for specific user

## Relationships

### User ↔ Requests
- One user can have many requests
- Each request belongs to one user
- Link field: `Request.user → User`

### Function ↔ Requests
- One function can have many requests
- Each request executes one function
- Link field: `Request.function → Function`

### User ↔ Request Reviews
- One user can review many requests
- Each request can be reviewed by one user
- Link field: `Request.reviewed_by → User`

## Authentication Models

### Login Schema
```python
class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1)
```

### JWT Token Structure
```python
{
    "sub": "user_id",
    "username": "username",
    "role": "admin|leader|member",
    "exp": timestamp,
    "iat": timestamp
}
```

## API Request/Response Models

### User Management
- `UserCreate`: username, email, full_name?, role?, password?
- `UserUpdate`: email?, full_name?, role?, is_active?
- `UserResponse`: id, username, email, full_name?, role, is_active, created_at, last_login?

### Function Management
- `FunctionCreate`: name, description?, api_endpoint, http_method?, min_role?, required_fields?, url_parameters?, request_headers?, timeout?
- `FunctionUpdate`: All fields optional
- `FunctionResponse`: All fields + can_execute (calculated)
- `FunctionExecute`: parameters

### Request Management
- `RequestCreate`: function_id, parameters?
- `RequestApprove`: request_id
- `RequestReject`: request_id, reason
- `RequestResponse`: All fields + user_username, function_name, reviewer_username

## Business Rules

### Role-Based Access Control
1. **Admin**: Can access all functions, manage all users, approve any request
2. **Leader**: Can access leader+ functions, manage members, approve member requests
3. **Member**: Can access member+ functions, manage own profile, create requests

### Function Execution Flow
1. User creates request with function and parameters
2. Request enters "pending" status
3. Admin/Leader reviews and approves/rejects
4. If approved, function executes automatically
5. Result stored in request with "completed" status
6. If execution fails, marked with error message

### User Management Rules
- Admin can modify any user
- Leader can modify members only
- Users can modify their own profile
- Username and email must be unique
- Role changes require appropriate permissions

## Required Environment Variables

```bash
# MongoDB Connection
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=clean_dashboard

# JWT Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional: LDAP Integration
LDAP_ENABLED=false
LDAP_SERVER=ldap://localhost:389
LDAP_BASE_DN=dc=example,dc=com
```

## Database Initialization

### Default Admin User
```python
{
    "username": "admin",
    "email": "admin@dashboard.local",
    "full_name": "System Administrator",
    "role": "admin",
    "is_active": true,
    "password_hash": "hashed_default_password"
}
```

### Sample Function
```python
{
    "name": "Health Check",
    "description": "Check system health status",
    "api_endpoint": "http://localhost:8000/health",
    "http_method": "GET",
    "min_role": "member",
    "required_fields": [],
    "is_active": true
}
```

This structure provides a complete, simplified database schema that supports all frontend functionality while maintaining clean separation of concerns.