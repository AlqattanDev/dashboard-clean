# Authentication System - Clean Dashboard

## Overview

The Clean Dashboard uses a **JWT-based authentication system** that supports both local database authentication and LDAP integration for enterprise environments.

## Architecture

```ascii
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │     Backend     │    │   Auth Store    │
│                 │    │                 │    │                 │
│ Login Form      │───►│ /api/v1/auth/   │───►│ Local Database  │
│ JWT Token       │◄───│ login           │    │      OR         │
│ Storage         │    │                 │    │ LDAP Server     │
│                 │    │ JWT Validation  │    │                 │
│ All API Calls   │───►│ Middleware      │    │                 │
│ Include Token   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Authentication Flow

### 1. Initial Login
```ascii
User Enter Credentials
        │
        ▼
┌─────────────────┐
│ POST /auth/login│
│ {username, pwd} │
└─────────────────┘
        │
        ▼
┌─────────────────┐    YES    ┌─────────────────┐
│ Check Local DB  │ ────────► │ Return JWT      │
│ or LDAP Server  │           │ + User Info     │
└─────────────────┘           └─────────────────┘
        │ NO                          │
        ▼                            ▼
┌─────────────────┐           ┌─────────────────┐
│ Return 401      │           │ Frontend Stores │
│ Unauthorized    │           │ Token in        │
└─────────────────┘           │ localStorage    │
                              └─────────────────┘
```

### 2. Subsequent API Calls
```ascii
Frontend API Call
        │
        ▼
┌─────────────────┐
│ Include Header: │
│ Authorization:  │
│ Bearer <token>  │
└─────────────────┘
        │
        ▼
┌─────────────────┐    VALID   ┌─────────────────┐
│ JWT Middleware  │ ─────────► │ Process Request │
│ Validates Token │            │ + Check Roles   │
└─────────────────┘            └─────────────────┘
        │ INVALID
        ▼
┌─────────────────┐
│ Return 401      │
│ Unauthorized    │
└─────────────────┘
```

## JWT Token Structure

### Token Payload
```javascript
{
  "sub": "user_id_from_database",    // Subject (user ID)
  "username": "john_doe",            // Username
  "role": "admin",                   // User role (admin/leader/member)
  "email": "john@company.com",       // User email
  "type": "access",                  // Token type
  "iat": 1640995200,                // Issued at (timestamp)
  "exp": 1641081600                  // Expires at (timestamp)
}
```

### Token Security Features
- **Signed with HS256**: Prevents tampering
- **Time-limited**: 30-minute default expiration
- **Role-based**: Includes user role for authorization
- **Stateless**: No server-side session storage needed

## Authentication Methods

### 1. Local Database Authentication

**Development Mode** (default):
```python
# In .env file
LDAP_ENABLED=false

# Uses bcrypt password hashing
# Validates against users collection in MongoDB
```

**Process**:
1. User submits username/password
2. Look up user in `users` collection
3. Verify password using bcrypt
4. Create JWT token with user information
5. Return token to frontend

### 2. LDAP Authentication

**Production Mode**:
```python
# In .env file
LDAP_ENABLED=true
LDAP_SERVER=ldaps://ldap.company.com:636
LDAP_BASE_DN=dc=company,dc=com
LDAP_USER_DN_TEMPLATE=uid={username},ou=people,{base_dn}
```

**Process**:
1. User submits username/password
2. Connect to LDAP server
3. Bind with user credentials (authenticate)
4. Search for user attributes and groups
5. Determine role based on LDAP groups
6. Create/update user in local database
7. Create JWT token and return

### LDAP Group to Role Mapping

```python
# Admin roles (highest privilege)
admin_groups = [
    'cn=admins',
    'cn=administrators', 
    'cn=dashboard-admins'
]

# Leader roles (middle privilege)
leader_groups = [
    'cn=leaders',
    'cn=managers',
    'cn=dashboard-leaders'
]

# Default: member role (basic privilege)
```

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Purpose | Rate Limit |
|--------|----------|---------|------------|
| POST | `/api/v1/auth/login` | Login with credentials | 5/minute |
| POST | `/api/v1/auth/refresh` | Refresh JWT token | 10/minute |
| GET | `/api/v1/auth/me` | Get current user info | Standard |
| POST | `/api/v1/auth/logout` | Logout (client-side) | Standard |
| POST | `/api/v1/auth/validate` | Validate token | Standard |

### Login Request/Response

**Request**:
```json
POST /api/v1/auth/login
{
  "username": "john_doe",
  "password": "secure_password"
}
```

**Success Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "64a7b8c9d1e2f3g4h5i6j7k8",
    "username": "john_doe",
    "email": "john@company.com",
    "full_name": "John Doe",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

**Error Response**:
```json
{
  "detail": "Invalid username or password"
}
```

## Role-Based Authorization

### Authorization Decorators

```python
from utils.dependencies import require_admin, require_leader_or_admin, get_current_user

# Require admin role
@app.get("/admin-only")
async def admin_endpoint(current_user: dict = Depends(require_admin)):
    pass

# Require leader or admin role  
@app.get("/leader-access")
async def leader_endpoint(current_user: dict = Depends(require_leader_or_admin)):
    pass

# Any authenticated user
@app.get("/authenticated")
async def auth_endpoint(current_user: dict = Depends(get_current_user)):
    pass
```

### Role Hierarchy

```ascii
admin (Level 1)
├── Can access ALL endpoints
├── Can manage all users
├── Can create/edit/delete functions
└── Can approve any requests

leader (Level 2)  
├── Can access leader+ endpoints
├── Can manage member users only
├── Can view all functions
└── Can approve member requests

member (Level 3)
├── Can access member+ endpoints  
├── Can manage own profile only
├── Can execute permitted functions
└── Can create execution requests
```

## Security Features

### Password Security
- **Bcrypt hashing**: Industry-standard password hashing
- **Salt rounds**: 12 rounds (secure but performant)
- **No plaintext storage**: Passwords never stored in plain text

### JWT Security
- **Strong secret key**: Configurable secret for signing
- **Token expiration**: Configurable expiration time
- **Algorithm validation**: Only accepts expected algorithm
- **Payload validation**: Validates token structure and content

### Rate Limiting
- **Login attempts**: 5 attempts per minute per IP
- **Token refresh**: 10 attempts per minute per IP
- **General API**: 100 requests per minute per IP

### Input Validation
- **Pydantic models**: Type checking and validation
- **SQL injection protection**: MongoDB doesn't use SQL
- **XSS prevention**: Proper input sanitization

## Configuration

### Environment Variables

```bash
# Required
JWT_SECRET_KEY=your-secret-key-here
MONGODB_URL=mongodb://localhost:27017

# Optional LDAP
LDAP_ENABLED=false
LDAP_SERVER=ldap://localhost:389
LDAP_BASE_DN=dc=example,dc=com
LDAP_USER_DN_TEMPLATE=uid={username},ou=users,{base_dn}

# Optional tuning
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
LOGIN_RATE_LIMIT_PER_MINUTE=5
```

### Production LDAP Example

```bash
# Production LDAP configuration
LDAP_ENABLED=true
LDAP_SERVER=ldaps://ldap.company.com:636
LDAP_BASE_DN=dc=company,dc=com
LDAP_USER_DN_TEMPLATE=uid={username},ou=people,{base_dn}

# Secure JWT key (use a strong random key)
JWT_SECRET_KEY=your-256-bit-random-secret-key-here
```

## Frontend Integration

### Token Storage
```javascript
// Store token after login
localStorage.setItem('token', response.access_token);

// Include in API calls
const token = localStorage.getItem('token');
fetch('/api/v1/users', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Remove on logout
localStorage.removeItem('token');
```

### Authentication State Management
The frontend uses Alpine.js for authentication state:

```javascript
// Main app component
function app() {
  return {
    isAuthenticated: false,
    user: null,
    
    async checkAuth() {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const response = await fetch('/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        this.user = await response.json();
        this.isAuthenticated = true;
      } else {
        localStorage.removeItem('token');
      }
    }
  }
}
```

## Error Handling

### Common Error Responses

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 401 | Invalid/expired token | Redirect to login |
| 403 | Insufficient permissions | Show access denied |
| 429 | Rate limit exceeded | Show retry message |
| 422 | Validation error | Show field errors |

### Error Response Format
```json
{
  "detail": "Error message",
  "error": "error_code",
  "remaining_attempts": 3
}
```

## Testing Authentication

### Test Users (Development)
```bash
# Default admin (created automatically)
Username: admin
Password: admin123
Role: admin

# Create test users via API or database
```

### Manual Testing
```bash
# Login test
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Protected endpoint test
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Troubleshooting

### Common Issues

**1. "Could not validate credentials"**
- Check token format in Authorization header
- Verify JWT secret key matches
- Check token expiration

**2. "LDAP authentication error"**
- Verify LDAP server connectivity
- Check LDAP configuration in .env
- Validate user DN template format

**3. "Rate limit exceeded"**
- Wait for rate limit window to reset
- Check IP-based rate limiting configuration

**4. "User account is disabled"**
- Check `is_active` field in user document
- Admin can reactivate user account

This authentication system provides a secure, scalable foundation that works for both development (local) and production (LDAP) environments.