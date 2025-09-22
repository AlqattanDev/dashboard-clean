"""
MongoDB Database Connection and Collections
Pure PyMongo implementation for simplicity
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, OperationFailure
from typing import Optional, Dict, List, Any
import os
from datetime import datetime
import hashlib

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        
    def connect(self, mongodb_url: str = "mongodb://localhost:27017", db_name: str = "clean_dashboard"):
        """Connect to MongoDB"""
        self.client = MongoClient(mongodb_url)
        self.db = self.client[db_name]
        self.setup_collections()
        
    def setup_collections(self):
        """Create collections and indexes"""
        # Users collection
        self.users = self.db.users
        self.users.create_index([("username", ASCENDING)], unique=True)
        self.users.create_index([("email", ASCENDING)], unique=True)
        self.users.create_index([("role", ASCENDING)])
        self.users.create_index([("is_active", ASCENDING)])
        self.users.create_index([("created_at", DESCENDING)])
        
        # Functions collection
        self.functions = self.db.functions
        self.functions.create_index([("name", ASCENDING)])
        self.functions.create_index([("min_role", ASCENDING)])
        self.functions.create_index([("is_active", ASCENDING)])
        self.functions.create_index([("created_at", DESCENDING)])
        
        # Requests collection
        self.requests = self.db.requests
        self.requests.create_index([("user_id", ASCENDING)])
        self.requests.create_index([("function_id", ASCENDING)])
        self.requests.create_index([("status", ASCENDING)])
        self.requests.create_index([("created_at", DESCENDING)])
        self.requests.create_index([("reviewed_by", ASCENDING)])
        
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

# Global database instance
db = Database()


# Collection Schemas and Relationships:

"""
USERS COLLECTION:
{
    "_id": ObjectId,
    "username": str (unique, 3-50 chars),
    "email": str (unique, email format),
    "full_name": str (optional),
    "role": str ("admin", "leader", "member"),
    "is_active": bool (default: True),
    "password_hash": str,
    "created_at": datetime,
    "last_login": datetime (optional)
}

FUNCTIONS COLLECTION:
{
    "_id": ObjectId,
    "name": str (1-200 chars),
    "description": str (max 1000 chars),
    "api_endpoint": str (URL),
    "http_method": str ("GET", "POST", "PUT", "DELETE", "PATCH"),
    "min_role": str ("admin", "leader", "member"),
    "required_fields": [
        {
            "name": str,
            "type": str ("string", "number", "boolean"),
            "required": bool,
            "description": str
        }
    ],
    "url_parameters": [str] (parameters to append to URL),
    "request_headers": {str: str} (custom headers),
    "timeout": int (1-300 seconds, default: 30),
    "is_active": bool (default: True),
    "created_at": datetime,
    "updated_at": datetime
}

REQUESTS COLLECTION:
{
    "_id": ObjectId,
    "user_id": ObjectId (reference to users._id),
    "function_id": ObjectId (reference to functions._id),
    "parameters": dict (function execution parameters),
    "status": str ("pending", "approved", "rejected", "completed", "failed"),
    "reviewed_by": ObjectId (optional, reference to users._id),
    "reviewed_at": datetime (optional),
    "rejection_reason": str (optional),
    "execution_result": dict (optional, function response),
    "execution_time_ms": int (optional, execution duration),
    "error_message": str (optional, if execution failed),
    "created_at": datetime,
    "updated_at": datetime
}

RELATIONSHIPS:
- requests.user_id → users._id (many-to-one)
- requests.function_id → functions._id (many-to-one)  
- requests.reviewed_by → users._id (many-to-one, optional)

ROLE HIERARCHY:
admin > leader > member
- admin: can access all functions, manage all users, approve any request
- leader: can access leader+ functions, manage members, approve member requests
- member: can access member+ functions, manage own profile, create requests
"""