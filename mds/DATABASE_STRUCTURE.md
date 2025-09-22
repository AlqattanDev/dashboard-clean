# MongoDB Database Structure - Clean Dashboard

## Overview

This document describes the complete MongoDB database structure for the Clean Dashboard project. We use **pure PyMongo** (no ODM) for maximum simplicity and minimal dependencies.

## Database Schema

```
Database: clean_dashboard
├── users          (User accounts and authentication)
├── functions      (Available API functions)
└── requests       (Function execution requests)
```

---

## Collection Relationships

```ascii
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│     USERS       │         │   FUNCTIONS     │         │    REQUESTS     │
│                 │         │                 │         │                 │
│ _id (ObjectId)  │◄────┐   │ _id (ObjectId)  │◄────┐   │ _id (ObjectId)  │
│ username        │     │   │ name            │     │   │ user_id         │──┐
│ email           │     │   │ description     │     │   │ function_id     │──┼──┐
│ role            │     │   │ api_endpoint    │     │   │ parameters      │  │  │
│ password_hash   │     │   │ http_method     │     │   │ status          │  │  │
│ is_active       │     │   │ min_role        │     │   │ reviewed_by     │──┘  │
│ created_at      │     │   │ required_fields │     │   │ reviewed_at     │     │
│ last_login      │     │   │ timeout         │     │   │ rejection_reason│     │
└─────────────────┘     │   │ is_active       │     │   │ execution_result│     │
                        │   │ created_at      │     │   │ execution_time  │     │
                        │   └─────────────────┘     │   │ error_message   │     │
                        │                           │   │ created_at      │     │
                        └───────────────────────────┘   │ updated_at      │     │
                                                        └─────────────────┘     │
                                                                                │
                        Relationships:                                          │
                        • requests.user_id → users._id (Creator)               │
                        • requests.function_id → functions._id (What to run)   │
                        • requests.reviewed_by → users._id (Who approved)  ────┘
```

---

## Detailed Collection Schemas

### 1. Users Collection

**Purpose**: Store user accounts, authentication, and role-based access control

```javascript
{
  "_id": ObjectId("..."),              // MongoDB auto-generated ID
  "username": "john_doe",              // Unique username (3-50 chars)
  "email": "john@company.com",         // Unique email address
  "full_name": "John Doe",             // Optional display name
  "role": "member",                    // Role: "admin", "leader", "member"
  "is_active": true,                   // Account status
  "password_hash": "$2b$12$...",       // Bcrypt hashed password
  "created_at": ISODate("2024-01-01"), // Account creation time
  "last_login": ISODate("2024-01-15")  // Last login timestamp (optional)
}
```

**Indexes:**
- `username` (unique)
- `email` (unique) 
- `role` (for filtering)
- `is_active` (for filtering)
- `created_at` (for sorting)

**Role Hierarchy:**
```
admin (level 1)     → Can do everything
  └── leader (level 2)  → Can manage members, approve member requests
      └── member (level 3)  → Can execute functions, manage own profile
```

---

### 2. Functions Collection

**Purpose**: Define available API functions that users can execute

```javascript
{
  "_id": ObjectId("..."),              // MongoDB auto-generated ID
  "name": "System Health Check",       // Function display name
  "description": "Check system status", // Function description
  "api_endpoint": "http://api.example.com/health", // Target API URL
  "http_method": "GET",                // HTTP method (GET, POST, PUT, DELETE)
  "min_role": "member",                // Minimum role required to execute
  "required_fields": [                 // Parameters needed for execution
    {
      "name": "check_type",
      "type": "string",
      "required": true,
      "description": "Type of health check to perform"
    }
  ],
  "url_parameters": ["id", "format"],  // URL path parameters
  "request_headers": {                 // Custom headers to send
    "Authorization": "Bearer token",
    "Content-Type": "application/json"
  },
  "timeout": 30,                       // Request timeout in seconds
  "is_active": true,                   // Function availability
  "created_at": ISODate("2024-01-01"), // Creation time
  "updated_at": ISODate("2024-01-01")  // Last modification time
}
```

**Indexes:**
- `name` (for searching)
- `min_role` (for filtering)
- `is_active` (for filtering)
- `created_at` (for sorting)

---

### 3. Requests Collection

**Purpose**: Track function execution requests and approval workflow

```javascript
{
  "_id": ObjectId("..."),              // MongoDB auto-generated ID
  "user_id": ObjectId("..."),          // Reference to users._id (who requested)
  "function_id": ObjectId("..."),      // Reference to functions._id (what to run)
  "parameters": {                      // Function execution parameters
    "check_type": "full",
    "environment": "production"
  },
  "status": "pending",                 // Status: "pending", "approved", "rejected", "completed", "failed"
  "reviewed_by": ObjectId("..."),      // Reference to users._id (who reviewed) - optional
  "reviewed_at": ISODate("2024-01-01"), // Review timestamp - optional
  "rejection_reason": "Not authorized", // Reason for rejection - optional
  "execution_result": {               // Function response - optional
    "status": "success",
    "data": { "cpu": "45%", "memory": "2.1GB" }
  },
  "execution_time_ms": 1250,          // Execution duration in milliseconds - optional
  "error_message": "Connection timeout", // Error details if failed - optional
  "created_at": ISODate("2024-01-01"), // Request creation time
  "updated_at": ISODate("2024-01-01")  // Last modification time
}
```

**Indexes:**
- `user_id` (for user-specific queries)
- `function_id` (for function-specific queries)
- `status` (for filtering by status)
- `created_at` (for sorting)
- `reviewed_by` (for reviewer queries)

---

## Request Workflow States

```ascii
┌─────────────┐    approve()    ┌─────────────┐    execute()    ┌─────────────┐
│   PENDING   │ ──────────────► │  APPROVED   │ ──────────────► │ COMPLETED   │
│             │                 │             │                 │             │
│ Created by  │                 │ Reviewed by │                 │ Has result  │
│ member      │                 │ admin/leader│                 │ & timing    │
└─────────────┘                 └─────────────┘                 └─────────────┘
       │                               │                               │
       │ reject()                      │ execute()                     │
       ▼                               ▼                               │
┌─────────────┐                 ┌─────────────┐                       │
│  REJECTED   │                 │   FAILED    │◄──────────────────────┘
│             │                 │             │        error during
│ Has reason  │                 │ Has error   │        execution
│ from admin  │                 │ message     │
└─────────────┘                 └─────────────┘
```

**Status Transitions:**
- `pending` → `approved` (by admin/leader)
- `pending` → `rejected` (by admin/leader with reason)
- `approved` → `completed` (successful execution)
- `approved` → `failed` (execution error)

---

## Role-Based Access Control

### Access Matrix

| Action | Admin | Leader | Member |
|--------|-------|--------|--------|
| **Users** |  |  |  |
| View all users | ✅ | ❌ | ❌ |
| Create users | ✅ | ❌ | ❌ |
| Edit any user | ✅ | ❌ | ❌ |
| Edit members only | ✅ | ✅ | ❌ |
| Edit own profile | ✅ | ✅ | ✅ |
| Delete users | ✅ | ❌ | ❌ |
| **Functions** |  |  |  |
| View functions | ✅ | ✅ | ✅ |
| Create functions | ✅ | ❌ | ❌ |
| Edit functions | ✅ | ❌ | ❌ |
| Delete functions | ✅ | ❌ | ❌ |
| Execute functions | ✅ | ✅ | ✅ |
| **Requests** |  |  |  |
| View all requests | ✅ | ✅ | ❌ |
| View own requests | ✅ | ✅ | ✅ |
| Create requests | ✅ | ✅ | ✅ |
| Approve any request | ✅ | ❌ | ❌ |
| Approve member requests | ✅ | ✅ | ❌ |
| Cancel own pending | ✅ | ✅ | ✅ |

### Function Execution Rules

```ascii
Function min_role: "admin"     → Only admins can execute
Function min_role: "leader"    → Leaders and admins can execute  
Function min_role: "member"    → Everyone can execute

User Role Hierarchy:
admin ──► can execute: admin, leader, member functions
leader ──► can execute: leader, member functions  
member ──► can execute: member functions only
```

---

## Sample Data

### Sample Users
```javascript
// Default Admin
{
  "username": "admin",
  "email": "admin@dashboard.local", 
  "role": "admin",
  "password": "admin123" // Will be hashed
}

// Sample Leader
{
  "username": "leader1",
  "email": "leader@company.com",
  "role": "leader", 
  "password": "leader123" // Will be hashed
}

// Sample Member
{
  "username": "member1", 
  "email": "member@company.com",
  "role": "member",
  "password": "member123" // Will be hashed
}
```

### Sample Functions
```javascript
// Health Check (Everyone can use)
{
  "name": "System Health Check",
  "description": "Check the overall health of the system",
  "api_endpoint": "http://localhost:8000/health",
  "http_method": "GET",
  "min_role": "member",
  "required_fields": [],
  "timeout": 10
}

// User Report (Leaders and above)
{
  "name": "User Count Report", 
  "description": "Generate a report of total users",
  "api_endpoint": "http://localhost:8000/api/reports/users",
  "http_method": "GET", 
  "min_role": "leader",
  "required_fields": [],
  "timeout": 30
}

// System Backup (Admin only)
{
  "name": "System Backup",
  "description": "Initiate a system backup process", 
  "api_endpoint": "http://localhost:8000/api/admin/backup",
  "http_method": "POST",
  "min_role": "admin",
  "required_fields": [
    {
      "name": "backup_type",
      "type": "string", 
      "required": true,
      "description": "Type of backup (full, incremental)"
    }
  ],
  "timeout": 300
}
```

---

## Database Operations

### Connection Setup
```python
from pymongo import MongoClient
from services.database import db

# Connect to MongoDB
db.connect("mongodb://localhost:27017", "clean_dashboard")

# Initialize with sample data
from services.user_service import create_default_admin
from services.function_service import create_sample_functions

create_default_admin()
create_sample_functions()
```

### Query Examples
```python
# Get all active functions a user can execute
user_role = "member"
accessible_functions = FunctionService.get_functions_for_user(user_role)

# Get pending requests for admin review  
pending_requests = RequestService.get_pending_requests()

# Create a new request
request = RequestService.create_request(
    user_id="user_object_id",
    function_id="function_object_id", 
    parameters={"backup_type": "full"}
)

# Approve request
RequestService.approve_request(request_id, reviewer_id)
```

---

## Performance Considerations

### Indexes Strategy
- **Unique indexes** on username/email prevent duplicates
- **Compound indexes** on frequently queried combinations
- **Sparse indexes** on optional fields like last_login
- **TTL indexes** could be added for request cleanup (if needed)

### Query Optimization
- Use projection to limit returned fields
- Paginate large result sets (skip/limit)
- Pre-populate user/function names to avoid joins
- Cache frequently accessed data in application layer

---

This structure provides a clean, scalable foundation for the dashboard with clear relationships and efficient querying patterns.