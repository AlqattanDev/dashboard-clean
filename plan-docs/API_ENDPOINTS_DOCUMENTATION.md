# API Endpoints Documentation

## Overview
Complete list of all API endpoints required for the clean dashboard implementation.

## Base Configuration
- **Base URL**: `http://localhost:8000`
- **API Version**: `/api/v1`
- **Authentication**: Bearer token in Authorization header
- **Rate Limiting**: Configured per endpoint

## Authentication Endpoints

### POST `/api/v1/auth/login`
**Purpose**: Authenticate user and return access token
**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```
**Response**:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "admin|leader|member",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-01T00:00:00Z"
  }
}
```
**Rate Limit**: 5/minute
**Status Codes**: 200, 401, 429

### POST `/api/v1/auth/refresh`
**Purpose**: Refresh access token
**Headers**: Authorization: Bearer {token}
**Response**: Same as login
**Rate Limit**: 10/minute
**Status Codes**: 200, 401

### GET `/api/v1/auth/me`
**Purpose**: Get current user information
**Headers**: Authorization: Bearer {token}
**Response**: UserResponse object
**Status Codes**: 200, 401

### POST `/api/v1/auth/logout`
**Purpose**: Logout user (session cleanup)
**Headers**: Authorization: Bearer {token}
**Response**:
```json
{
  "message": "Logged out successfully"
}
```
**Status Codes**: 200, 401

### POST `/api/v1/auth/validate`
**Purpose**: Validate token for frontend session checks
**Headers**: Authorization: Bearer {token}
**Response**:
```json
{
  "valid": true,
  "user": {UserResponse}
}
```
**Status Codes**: 200, 401

## User Management Endpoints

### GET `/api/v1/users`
**Purpose**: Get all users (admin only)
**Headers**: Authorization: Bearer {token}
**Response**: Array of UserResponse
**Required Role**: admin
**Status Codes**: 200, 401, 403

### GET `/api/v1/users/list`
**Purpose**: Alias for GET /users (frontend compatibility)
**Same as GET `/api/v1/users`

### GET `/api/v1/users/{user_id}`
**Purpose**: Get specific user by ID
**Headers**: Authorization: Bearer {token}
**Response**: UserResponse
**Access Control**: Admin can view any, others can view self
**Status Codes**: 200, 401, 403, 404

### POST `/api/v1/users`
**Purpose**: Create new user
**Headers**: Authorization: Bearer {token}
**Request Body**:
```json
{
  "username": "string",
  "email": "user@example.com",
  "full_name": "string",
  "role": "admin|leader|member",
  "password": "string"
}
```
**Response**: UserResponse
**Required Role**: admin
**Status Codes**: 201, 400, 401, 403, 409

### PUT `/api/v1/users/{user_id}`
**Purpose**: Update user
**Headers**: Authorization: Bearer {token}
**Request Body**:
```json
{
  "email": "user@example.com",
  "full_name": "string",
  "role": "admin|leader|member",
  "is_active": true
}
```
**Response**: UserResponse
**Access Control**: Admin can modify any, leader can modify members, users can modify self
**Status Codes**: 200, 400, 401, 403, 404

### DELETE `/api/v1/users/{user_id}`
**Purpose**: Delete user (admin only)
**Headers**: Authorization: Bearer {token}
**Response**:
```json
{
  "message": "User deleted successfully"
}
```
**Required Role**: admin
**Status Codes**: 200, 401, 403, 404

### GET `/api/v1/users/{user_id}/profile`
**Purpose**: Get user profile page (returns HTML for frontend)
**Status Codes**: 200, 404

### GET `/api/v1/users/{user_id}/edit`
**Purpose**: Get user edit form (returns HTML for frontend)
**Required Role**: Based on access control rules
**Status Codes**: 200, 401, 403, 404

## Function Management Endpoints

### GET `/api/v1/functions`
**Purpose**: Get all functions accessible to current user
**Headers**: Authorization: Bearer {token}
**Response**: Array of FunctionResponse with can_execute field
**Status Codes**: 200, 401

### GET `/api/v1/functions/list`
**Purpose**: Alias for GET /functions (frontend compatibility)
**Same as GET `/api/v1/functions`

### GET `/api/v1/functions/{function_id}`
**Purpose**: Get specific function by ID
**Headers**: Authorization: Bearer {token}
**Response**: FunctionResponse
**Status Codes**: 200, 401, 403, 404

### POST `/api/v1/functions`
**Purpose**: Create new function
**Headers**: Authorization: Bearer {token}
**Request Body**:
```json
{
  "name": "string",
  "description": "string",
  "api_endpoint": "string",
  "http_method": "GET|POST|PUT|DELETE|PATCH",
  "min_role": "admin|leader|member",
  "required_fields": [
    {
      "name": "string",
      "type": "string|number|boolean",
      "required": true,
      "description": "string"
    }
  ],
  "url_parameters": ["param1", "param2"],
  "request_headers": {
    "Header-Name": "value"
  },
  "timeout": 30
}
```
**Response**: FunctionResponse
**Required Role**: admin
**Status Codes**: 201, 400, 401, 403

### PUT `/api/v1/functions/{function_id}`
**Purpose**: Update function
**Headers**: Authorization: Bearer {token}
**Request Body**: Same as create (all fields optional)
**Response**: FunctionResponse
**Required Role**: admin
**Status Codes**: 200, 400, 401, 403, 404

### DELETE `/api/v1/functions/{function_id}`
**Purpose**: Delete function
**Headers**: Authorization: Bearer {token}
**Response**:
```json
{
  "message": "Function deleted successfully"
}
```
**Required Role**: admin
**Status Codes**: 200, 401, 403, 404

### GET `/api/v1/functions/{function_id}/form`
**Purpose**: Get function execution form (HTML for frontend)
**Headers**: Authorization: Bearer {token}
**Status Codes**: 200, 401, 403, 404

### GET `/api/v1/functions/{function_id}/details`
**Purpose**: Get function details page (HTML for frontend)
**Headers**: Authorization: Bearer {token}
**Status Codes**: 200, 401, 403, 404

### GET `/api/v1/functions/{function_id}/edit`
**Purpose**: Get function edit form (HTML for frontend)
**Headers**: Authorization: Bearer {token}
**Required Role**: admin
**Status Codes**: 200, 401, 403, 404

### POST `/api/v1/functions/{function_id}/execute`
**Purpose**: Execute function (creates request for approval)
**Headers**: Authorization: Bearer {token}
**Request Body**:
```json
{
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  }
}
```
**Response**: RequestResponse (newly created request)
**Rate Limit**: 10/minute
**Status Codes**: 201, 400, 401, 403, 404

## Request Management Endpoints

### GET `/api/v1/requests`
**Purpose**: Get requests based on user role
- Admin/Leader: All requests
- Member: Own requests only
**Headers**: Authorization: Bearer {token}
**Response**: Array of RequestResponse with additional fields:
```json
[
  {
    "id": "string",
    "user_id": "string",
    "function_id": "string",
    "parameters": {},
    "status": "pending|approved|rejected|completed",
    "reviewed_by": "string",
    "reviewed_at": "string",
    "rejection_reason": "string",
    "execution_result": {},
    "execution_time_ms": 1000,
    "error_message": "string",
    "created_at": "string",
    "updated_at": "string",
    "user_username": "string",
    "function_name": "string",
    "reviewer_username": "string"
  }
]
```
**Status Codes**: 200, 401

### GET `/api/v1/requests/list`
**Purpose**: Alias for GET /requests (frontend compatibility)
**Same as GET `/api/v1/requests`

### GET `/api/v1/requests/my-requests`
**Purpose**: Get current user's requests only
**Headers**: Authorization: Bearer {token}
**Response**: Array of RequestResponse
**Status Codes**: 200, 401

### GET `/api/v1/requests/pending`
**Purpose**: Get all pending requests (leader/admin only)
**Headers**: Authorization: Bearer {token}
**Response**: Array of RequestResponse
**Required Role**: leader or admin
**Status Codes**: 200, 401, 403

### GET `/api/v1/requests/{request_id}`
**Purpose**: Get specific request by ID
**Headers**: Authorization: Bearer {token}
**Response**: RequestResponse
**Access Control**: Admin/leader can view any, members can view own
**Status Codes**: 200, 401, 403, 404

### POST `/api/v1/requests/{request_id}/approve`
**Purpose**: Approve request
**Headers**: Authorization: Bearer {token}
**Response**: RequestResponse (updated)
**Required Role**: leader or admin
**Status Codes**: 200, 401, 403, 404, 409

### POST `/api/v1/requests/{request_id}/reject`
**Purpose**: Reject request
**Headers**: Authorization: Bearer {token}
**Request Body**:
```json
{
  "request_id": "string",
  "reason": "string"
}
```
**Response**: RequestResponse (updated)
**Required Role**: leader or admin
**Status Codes**: 200, 400, 401, 403, 404, 409

### DELETE `/api/v1/requests/{request_id}`
**Purpose**: Cancel request (user can cancel own pending requests)
**Headers**: Authorization: Bearer {token}
**Response**:
```json
{
  "message": "Request cancelled successfully"
}
```
**Access Control**: User can cancel own pending requests, admin can cancel any
**Status Codes**: 200, 401, 403, 404, 409

## Dashboard Endpoints (Optional - for enhanced frontend)

### GET `/api/v1/dashboard/stats`
**Purpose**: Get dashboard statistics
**Headers**: Authorization: Bearer {token}
**Response**:
```json
{
  "total_functions": 10,
  "total_users": 25,
  "pending_requests": 5,
  "completed_requests_today": 15,
  "my_pending_requests": 2
}
```
**Status Codes**: 200, 401

### GET `/api/v1/dashboard/functions`
**Purpose**: Get recent/popular functions for quick access
**Headers**: Authorization: Bearer {token}
**Response**: Array of FunctionResponse (limited)
**Status Codes**: 200, 401

### GET `/api/v1/dashboard/activity`
**Purpose**: Get recent activity feed
**Headers**: Authorization: Bearer {token}
**Response**: Array of activity items
**Status Codes**: 200, 401

## System Endpoints

### GET `/health`
**Purpose**: Health check
**Response**:
```json
{
  "status": "healthy",
  "service": "dashboard-backend",
  "version": "3.0.0"
}
```
**Status Codes**: 200

### GET `/api`
**Purpose**: API information
**Response**:
```json
{
  "service": "Operations Dashboard API",
  "version": "3.0.0",
  "docs": "/docs"
}
```
**Status Codes**: 200

## Frontend Routes (Static HTML)

### GET `/`
**Purpose**: Serve main SPA HTML
**Response**: index.html

### GET `/dashboard`
**Purpose**: Serve dashboard page (SPA)
**Response**: index.html

### GET `/login`
**Purpose**: Serve login page (SPA)
**Response**: index.html

### GET `/functions`
**Purpose**: Serve functions page (SPA)
**Response**: index.html

### GET `/users`
**Purpose**: Serve users page (SPA)
**Response**: index.html

### GET `/requests`
**Purpose**: Serve requests page (SPA)
**Response**: index.html

## Error Response Format

All API endpoints return errors in this format:
```json
{
  "detail": "Error message",
  "error": "error_code",
  "remaining_attempts": 3
}
```

## Authentication Flow

1. **Login**: POST `/api/v1/auth/login` → Returns token
2. **Include Token**: All subsequent requests include `Authorization: Bearer {token}`
3. **Token Refresh**: POST `/api/v1/auth/refresh` when token expires
4. **Validation**: Frontend can use POST `/api/v1/auth/validate` to check token
5. **Logout**: POST `/api/v1/auth/logout` for cleanup

## Role-Based Access Summary

### Admin Role
- All endpoints accessible
- Can manage users and functions
- Can approve/reject any request

### Leader Role
- Can manage member users only
- Can approve/reject member requests
- Can access leader+ functions

### Member Role
- Can view own profile only
- Can create function execution requests
- Can access member+ functions

## Rate Limiting

- Login: 5 attempts per minute
- Token refresh: 10 per minute
- Function execution: 10 per minute
- Default: 100 requests per minute

This covers all endpoints needed for the complete dashboard functionality.