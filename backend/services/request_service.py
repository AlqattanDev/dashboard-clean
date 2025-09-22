"""
Request Service - Database operations for requests collection
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from .database import db

class RequestService:
    
    @staticmethod
    def create_request(user_id: str, function_id: str, 
                      parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new function execution request"""
        request_data = {
            "user_id": ObjectId(user_id),
            "function_id": ObjectId(function_id),
            "parameters": parameters or {},
            "status": "pending",
            "reviewed_by": None,
            "reviewed_at": None,
            "rejection_reason": None,
            "execution_result": None,
            "execution_time_ms": None,
            "error_message": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.requests.insert_one(request_data)
        request_data["_id"] = result.inserted_id
        return request_data
    
    @staticmethod
    def get_request_by_id(request_id: str) -> Optional[Dict[str, Any]]:
        """Get request by ID with user and function details"""
        try:
            # Get request
            request = db.requests.find_one({"_id": ObjectId(request_id)})
            if not request:
                return None
            
            # Get user details
            user = db.users.find_one({"_id": request["user_id"]})
            if user:
                request["user_username"] = user.get("username", "Unknown")
                request["user_email"] = user.get("email", "")
            
            # Get function details
            function = db.functions.find_one({"_id": request["function_id"]})
            if function:
                request["function_name"] = function.get("name", "Unknown Function")
                request["function_description"] = function.get("description", "")
            
            # Get reviewer details if exists
            if request.get("reviewed_by"):
                reviewer = db.users.find_one({"_id": request["reviewed_by"]})
                if reviewer:
                    request["reviewer_username"] = reviewer.get("username", "Unknown")
            
            # Format IDs
            request["id"] = str(request["_id"])
            request["user_id"] = str(request["user_id"])
            request["function_id"] = str(request["function_id"])
            if request.get("reviewed_by"):
                request["reviewed_by"] = str(request["reviewed_by"])
            del request["_id"]
            
            return request
        except Exception:
            return None
    
    @staticmethod
    def get_user_requests(user_id: str, skip: int = 0, limit: int = 50,
                         status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get requests for a specific user"""
        query = {"user_id": ObjectId(user_id)}
        
        if status_filter:
            query["status"] = status_filter
        
        return RequestService._get_requests_with_details(query, skip, limit)
    
    @staticmethod
    def get_all_requests(skip: int = 0, limit: int = 50,
                        status_filter: Optional[str] = None,
                        search: Optional[str] = None,
                        date_from: Optional[datetime] = None,
                        date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get all requests with filtering"""
        query = {}
        
        # Apply filters
        if status_filter:
            query["status"] = status_filter
        if date_from:
            query["created_at"] = {"$gte": date_from}
        if date_to:
            if "created_at" in query:
                query["created_at"]["$lte"] = date_to
            else:
                query["created_at"] = {"$lte": date_to}
        
        requests = RequestService._get_requests_with_details(query, skip, limit)
        
        # Apply search filter (on populated data)
        if search:
            filtered_requests = []
            search_lower = search.lower()
            for request in requests:
                if (search_lower in request.get("function_name", "").lower() or
                    search_lower in request.get("user_username", "").lower()):
                    filtered_requests.append(request)
            return filtered_requests
        
        return requests
    
    @staticmethod
    def get_pending_requests(limit: int = 50) -> List[Dict[str, Any]]:
        """Get all pending requests"""
        query = {"status": "pending"}
        return RequestService._get_requests_with_details(query, 0, limit)
    
    @staticmethod
    def _get_requests_with_details(query: Dict, skip: int, limit: int) -> List[Dict[str, Any]]:
        """Helper to get requests with user and function details"""
        requests = list(db.requests.find(query)
                       .sort("created_at", -1)
                       .skip(skip)
                       .limit(limit))
        
        # Populate user and function details
        for request in requests:
            # Get user details
            user = db.users.find_one({"_id": request["user_id"]})
            if user:
                request["user_username"] = user.get("username", "Unknown")
                request["user_email"] = user.get("email", "")
            
            # Get function details
            function = db.functions.find_one({"_id": request["function_id"]})
            if function:
                request["function_name"] = function.get("name", "Unknown Function")
                request["function_description"] = function.get("description", "")
            
            # Get reviewer details if exists
            if request.get("reviewed_by"):
                reviewer = db.users.find_one({"_id": request["reviewed_by"]})
                if reviewer:
                    request["reviewer_username"] = reviewer.get("username", "Unknown")
            
            # Format IDs
            request["id"] = str(request["_id"])
            request["user_id"] = str(request["user_id"])
            request["function_id"] = str(request["function_id"])
            if request.get("reviewed_by"):
                request["reviewed_by"] = str(request["reviewed_by"])
            del request["_id"]
        
        return requests
    
    @staticmethod
    def approve_request(request_id: str, reviewer_id: str) -> bool:
        """Approve a pending request"""
        try:
            result = db.requests.update_one(
                {"_id": ObjectId(request_id), "status": "pending"},
                {
                    "$set": {
                        "status": "approved",
                        "reviewed_by": ObjectId(reviewer_id),
                        "reviewed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    @staticmethod
    def reject_request(request_id: str, reviewer_id: str, reason: str) -> bool:
        """Reject a pending request"""
        try:
            result = db.requests.update_one(
                {"_id": ObjectId(request_id), "status": "pending"},
                {
                    "$set": {
                        "status": "rejected",
                        "reviewed_by": ObjectId(reviewer_id),
                        "reviewed_at": datetime.utcnow(),
                        "rejection_reason": reason,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    @staticmethod
    def complete_request(request_id: str, execution_result: Dict[str, Any],
                        execution_time_ms: int) -> bool:
        """Mark request as completed with result"""
        try:
            result = db.requests.update_one(
                {"_id": ObjectId(request_id)},
                {
                    "$set": {
                        "status": "completed",
                        "execution_result": execution_result,
                        "execution_time_ms": execution_time_ms,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    @staticmethod
    def fail_request(request_id: str, error_message: str) -> bool:
        """Mark request as failed with error"""
        try:
            result = db.requests.update_one(
                {"_id": ObjectId(request_id)},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": error_message,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    @staticmethod
    def delete_request(request_id: str, user_id: Optional[str] = None) -> bool:
        """Delete request (only pending requests can be deleted)"""
        try:
            query = {"_id": ObjectId(request_id), "status": "pending"}
            if user_id:
                query["user_id"] = ObjectId(user_id)
            
            result = db.requests.delete_one(query)
            return result.deleted_count > 0
        except Exception:
            return False
    
    @staticmethod
    def get_request_stats() -> Dict[str, int]:
        """Get request statistics"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        return {
            "total_requests": db.requests.count_documents({}),
            "pending_requests": db.requests.count_documents({"status": "pending"}),
            "completed_today": db.requests.count_documents({
                "status": "completed",
                "created_at": {"$gte": today}
            }),
            "failed_today": db.requests.count_documents({
                "status": "failed",
                "created_at": {"$gte": today}
            })
        }
    
    @staticmethod
    def get_user_request_count(user_id: str) -> int:
        """Get total request count for user"""
        return db.requests.count_documents({"user_id": ObjectId(user_id)})