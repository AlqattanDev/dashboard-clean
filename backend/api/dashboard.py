"""
Dashboard API endpoints
Provides aggregated statistics and dashboard data
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, date
from typing import Dict, Any
from services.database import db
from utils.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get dashboard statistics including counts and recent activity
    """
    try:
        # Get database collections
        functions_collection = db.functions
        users_collection = db.users
        requests_collection = db.requests
        
        # Count totals
        total_functions = functions_collection.count_documents({})
        total_users = users_collection.count_documents({})
        
        # Count pending requests
        pending_requests = requests_collection.count_documents({"status": "pending"})
        
        # Count completed requests today
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        completed_requests_today = requests_collection.count_documents({
            "status": "completed",
            "updated_at": {"$gte": today_start}
        })
        
        # Count current user's pending requests
        my_pending_requests = requests_collection.count_documents({
            "status": "pending",
            "user_id": current_user["id"]
        })
        
        return {
            "total_functions": total_functions,
            "total_users": total_users,
            "pending_requests": pending_requests,
            "completed_requests_today": completed_requests_today,
            "my_pending_requests": my_pending_requests
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

@router.get("/recent-activity")
def get_recent_activity(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get recent activity including functions and requests
    """
    try:
        # Get database collections
        functions_collection = db.functions
        requests_collection = db.requests
        users_collection = db.users
        
        # Get recent functions (last 10, sorted by creation date)
        recent_functions_cursor = functions_collection.find().sort("created_at", -1).limit(10)
        recent_functions = []
        for func in recent_functions_cursor:
            func["_id"] = str(func["_id"])
            recent_functions.append(func)
        
        # Get recent requests (last 10, sorted by creation date)
        recent_requests_cursor = requests_collection.find().sort("created_at", -1).limit(10)
        recent_requests = []
        for req in recent_requests_cursor:
            req["_id"] = str(req["_id"])
            
            # Get user information for the request
            if req.get("user_id"):
                user = users_collection.find_one({"_id": req["user_id"]})
                if user:
                    req["user_username"] = user.get("username", "Unknown")
                else:
                    req["user_username"] = "Unknown"
            else:
                req["user_username"] = "System"
                
            # Get function name for the request
            if req.get("function_id"):
                func = functions_collection.find_one({"_id": req["function_id"]})
                if func:
                    req["function_name"] = func.get("name", "Unknown Function")
                else:
                    req["function_name"] = "Unknown Function"
            else:
                req["function_name"] = "Unknown Function"
                
            recent_requests.append(req)
        
        return {
            "recent_functions": recent_functions,
            "recent_requests": recent_requests
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent activity: {str(e)}")