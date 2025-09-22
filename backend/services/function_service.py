"""
Function Service - Database operations for functions collection
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from .database import db

class FunctionService:
    
    @staticmethod
    def create_function(name: str, description: str, api_endpoint: str,
                       http_method: str = "POST", min_role: str = "member",
                       required_fields: Optional[List[Dict]] = None,
                       url_parameters: Optional[List[str]] = None,
                       request_headers: Optional[Dict[str, str]] = None,
                       timeout: int = 30) -> Dict[str, Any]:
        """Create a new function"""
        function_data = {
            "name": name,
            "description": description,
            "api_endpoint": api_endpoint,
            "http_method": http_method,
            "min_role": min_role,
            "required_fields": required_fields or [],
            "url_parameters": url_parameters or [],
            "request_headers": request_headers or {},
            "timeout": timeout,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.functions.insert_one(function_data)
        function_data["_id"] = result.inserted_id
        return function_data
    
    @staticmethod
    def get_function_by_id(function_id: str) -> Optional[Dict[str, Any]]:
        """Get function by ID"""
        try:
            function = db.functions.find_one({"_id": ObjectId(function_id)})
            if function:
                function["id"] = str(function["_id"])
                del function["_id"]
            return function
        except Exception:
            return None
    
    @staticmethod
    def get_all_functions(skip: int = 0, limit: int = 100,
                         role_filter: Optional[str] = None,
                         method_filter: Optional[str] = None,
                         search: Optional[str] = None,
                         user_role: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all functions with filtering"""
        query = {"is_active": True}
        
        # Apply filters
        if role_filter:
            query["min_role"] = role_filter
        if method_filter:
            query["http_method"] = method_filter
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        functions = list(db.functions.find(query)
                        .sort("created_at", -1)
                        .skip(skip)
                        .limit(limit))
        
        # Format functions and add can_execute field
        for function in functions:
            function["id"] = str(function["_id"])
            del function["_id"]
            
            # Add can_execute based on user role
            if user_role:
                function["can_execute"] = FunctionService.can_user_execute(
                    user_role, function["min_role"]
                )
        
        return functions
    
    @staticmethod
    def get_functions_for_user(user_role: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get functions that user can execute"""
        # Get role hierarchy level
        role_hierarchy = {"admin": 1, "leader": 2, "member": 3}
        user_level = role_hierarchy.get(user_role, 999)
        
        # Find functions user can access
        accessible_roles = [role for role, level in role_hierarchy.items() if level >= user_level]
        
        query = {
            "is_active": True,
            "min_role": {"$in": accessible_roles}
        }
        
        functions = list(db.functions.find(query)
                        .sort("created_at", -1)
                        .limit(limit))
        
        # Format functions
        for function in functions:
            function["id"] = str(function["_id"])
            del function["_id"]
            function["can_execute"] = True
        
        return functions
    
    @staticmethod
    def update_function(function_id: str, update_data: Dict[str, Any]) -> bool:
        """Update function"""
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = db.functions.update_one(
                {"_id": ObjectId(function_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    @staticmethod
    def delete_function(function_id: str) -> bool:
        """Delete function (soft delete by setting is_active=False)"""
        try:
            result = db.functions.update_one(
                {"_id": ObjectId(function_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    @staticmethod
    def can_user_execute(user_role: str, required_role: str) -> bool:
        """Check if user role can execute function with required role"""
        role_hierarchy = {"admin": 1, "leader": 2, "member": 3}
        user_level = role_hierarchy.get(user_role, 999)
        required_level = role_hierarchy.get(required_role, 1)
        return user_level <= required_level
    
    @staticmethod
    def get_function_count() -> int:
        """Get total count of active functions"""
        return db.functions.count_documents({"is_active": True})

# Initialize sample functions
def create_sample_functions():
    """Create sample functions for testing"""
    sample_functions = [
        {
            "name": "System Health Check",
            "description": "Check the overall health of the system",
            "api_endpoint": "http://localhost:8000/health",
            "http_method": "GET",
            "min_role": "member",
            "required_fields": [],
            "timeout": 10
        },
        {
            "name": "User Count Report",
            "description": "Generate a report of total users in the system",
            "api_endpoint": "http://localhost:8000/api/reports/users",
            "http_method": "GET",
            "min_role": "leader",
            "required_fields": [],
            "timeout": 30
        },
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
                    "required": True,
                    "description": "Type of backup (full, incremental)"
                }
            ],
            "timeout": 300
        }
    ]
    
    for func_data in sample_functions:
        # Check if function already exists
        existing = db.functions.find_one({"name": func_data["name"]})
        if not existing:
            FunctionService.create_function(**func_data)
            print(f"✅ Sample function created: {func_data['name']}")
    
    print("ℹ️ Sample functions initialization complete")