"""
Function Management API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from services.function_service import FunctionService
from services.request_service import RequestService
from utils.dependencies import (
    get_current_user,
    require_admin,
    require_member_or_above
)

router = APIRouter(prefix="/api/v1/functions", tags=["functions"])

# Request/Response models
class FunctionFieldSchema(BaseModel):
    name: str
    type: str  # string, number, boolean
    required: bool = True
    description: Optional[str] = None

class FunctionCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    api_endpoint: str
    http_method: str = "POST"
    min_role: str = "member"
    required_fields: Optional[List[FunctionFieldSchema]] = []
    url_parameters: Optional[List[str]] = []
    request_headers: Optional[Dict[str, str]] = {}
    timeout: int = 30

class FunctionUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    min_role: Optional[str] = None
    required_fields: Optional[List[FunctionFieldSchema]] = None
    url_parameters: Optional[List[str]] = None
    request_headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None
    is_active: Optional[bool] = None

class FunctionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    api_endpoint: str
    http_method: str
    min_role: str
    required_fields: List[Dict[str, Any]]
    url_parameters: List[str]
    request_headers: Dict[str, str]
    timeout: int
    is_active: bool
    created_at: str
    updated_at: str
    can_execute: bool = False

class ExecuteRequest(BaseModel):
    parameters: Optional[Dict[str, Any]] = {}

class MessageResponse(BaseModel):
    message: str

# Function Management Endpoints

@router.get("/", response_model=List[FunctionResponse])
async def list_functions(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all functions accessible to current user
    Functions are filtered based on user role
    """
    try:
        user_role = current_user.get("role", "member")
        functions = FunctionService.get_all_functions(user_role=user_role)
        
        result = []
        for func in functions:
            result.append(FunctionResponse(
                id=func["id"],
                name=func["name"],
                description=func.get("description"),
                api_endpoint=func["api_endpoint"],
                http_method=func["http_method"],
                min_role=func["min_role"],
                required_fields=func.get("required_fields", []),
                url_parameters=func.get("url_parameters", []),
                request_headers=func.get("request_headers", {}),
                timeout=func.get("timeout", 30),
                is_active=func.get("is_active", True),
                created_at=func["created_at"].isoformat(),
                updated_at=func["updated_at"].isoformat(),
                can_execute=func.get("can_execute", False)
            ))
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve functions"
        )

@router.get("/list", response_model=List[FunctionResponse])
async def list_functions_alias(
    current_user: dict = Depends(get_current_user)
):
    """Alias for GET /functions (frontend compatibility)"""
    return await list_functions(current_user)

@router.get("/{function_id}", response_model=FunctionResponse)
async def get_function(
    function_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get specific function by ID
    """
    try:
        func = FunctionService.get_function_by_id(function_id)
        if not func:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Function not found"
            )
        
        # Check if user can execute this function
        user_role = current_user.get("role", "member")
        can_execute = FunctionService.can_user_execute_function(user_role, func.get("min_role", "admin"))
        
        return FunctionResponse(
            id=str(func["_id"]),
            name=func["name"],
            description=func.get("description"),
            api_endpoint=func["api_endpoint"],
            http_method=func["http_method"],
            min_role=func["min_role"],
            required_fields=func.get("required_fields", []),
            url_parameters=func.get("url_parameters", []),
            request_headers=func.get("request_headers", {}),
            timeout=func.get("timeout", 30),
            is_active=func.get("is_active", True),
            created_at=func["created_at"].isoformat(),
            updated_at=func["updated_at"].isoformat(),
            can_execute=can_execute
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve function"
        )

@router.post("/", response_model=FunctionResponse, status_code=status.HTTP_201_CREATED)
async def create_function(
    function_data: FunctionCreateRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Create new function (admin only)
    """
    # Validate role and HTTP method
    valid_roles = ["admin", "leader", "member"]
    valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    
    if function_data.min_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid min_role. Must be one of: {', '.join(valid_roles)}"
        )
    
    if function_data.http_method not in valid_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid http_method. Must be one of: {', '.join(valid_methods)}"
        )
    
    try:
        # Convert field schemas to dict
        required_fields = []
        if function_data.required_fields:
            required_fields = [field.dict() for field in function_data.required_fields]
        
        # Create function
        new_function = FunctionService.create_function(
            name=function_data.name,
            description=function_data.description,
            api_endpoint=function_data.api_endpoint,
            http_method=function_data.http_method,
            min_role=function_data.min_role,
            required_fields=required_fields,
            url_parameters=function_data.url_parameters or [],
            request_headers=function_data.request_headers or {},
            timeout=function_data.timeout
        )
        
        return FunctionResponse(
            id=str(new_function["_id"]),
            name=new_function["name"],
            description=new_function.get("description"),
            api_endpoint=new_function["api_endpoint"],
            http_method=new_function["http_method"],
            min_role=new_function["min_role"],
            required_fields=new_function.get("required_fields", []),
            url_parameters=new_function.get("url_parameters", []),
            request_headers=new_function.get("request_headers", {}),
            timeout=new_function.get("timeout", 30),
            is_active=new_function.get("is_active", True),
            created_at=new_function["created_at"].isoformat(),
            updated_at=new_function["updated_at"].isoformat(),
            can_execute=True  # Admin can execute any function
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create function"
        )

@router.put("/{function_id}", response_model=FunctionResponse)
async def update_function(
    function_id: str,
    function_data: FunctionUpdateRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Update function (admin only)
    """
    # Check if function exists
    existing_function = FunctionService.get_function_by_id(function_id)
    if not existing_function:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Function not found"
        )
    
    # Validate role and HTTP method if provided
    if function_data.min_role is not None:
        valid_roles = ["admin", "leader", "member"]
        if function_data.min_role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid min_role. Must be one of: {', '.join(valid_roles)}"
            )
    
    if function_data.http_method is not None:
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if function_data.http_method not in valid_methods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid http_method. Must be one of: {', '.join(valid_methods)}"
            )
    
    try:
        # Prepare update data
        update_data = {}
        if function_data.name is not None:
            update_data["name"] = function_data.name
        if function_data.description is not None:
            update_data["description"] = function_data.description
        if function_data.api_endpoint is not None:
            update_data["api_endpoint"] = function_data.api_endpoint
        if function_data.http_method is not None:
            update_data["http_method"] = function_data.http_method
        if function_data.min_role is not None:
            update_data["min_role"] = function_data.min_role
        if function_data.required_fields is not None:
            update_data["required_fields"] = [field.dict() for field in function_data.required_fields]
        if function_data.url_parameters is not None:
            update_data["url_parameters"] = function_data.url_parameters
        if function_data.request_headers is not None:
            update_data["request_headers"] = function_data.request_headers
        if function_data.timeout is not None:
            update_data["timeout"] = function_data.timeout
        if function_data.is_active is not None:
            update_data["is_active"] = function_data.is_active
        
        # Update function
        updated_function = FunctionService.update_function(function_id, update_data)
        
        return FunctionResponse(
            id=str(updated_function["_id"]),
            name=updated_function["name"],
            description=updated_function.get("description"),
            api_endpoint=updated_function["api_endpoint"],
            http_method=updated_function["http_method"],
            min_role=updated_function["min_role"],
            required_fields=updated_function.get("required_fields", []),
            url_parameters=updated_function.get("url_parameters", []),
            request_headers=updated_function.get("request_headers", {}),
            timeout=updated_function.get("timeout", 30),
            is_active=updated_function.get("is_active", True),
            created_at=updated_function["created_at"].isoformat(),
            updated_at=updated_function["updated_at"].isoformat(),
            can_execute=True  # Admin can execute any function
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update function"
        )

@router.delete("/{function_id}", response_model=MessageResponse)
async def delete_function(
    function_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Delete function (admin only)
    """
    # Check if function exists
    existing_function = FunctionService.get_function_by_id(function_id)
    if not existing_function:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Function not found"
        )
    
    try:
        # Delete function
        success = FunctionService.delete_function(function_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete function"
            )
        
        return MessageResponse(message="Function deleted successfully")
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete function"
        )

@router.post("/{function_id}/execute", response_model=Dict[str, Any])
async def execute_function(
    function_id: str,
    execute_data: ExecuteRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Execute function by creating a request
    Creates a request in pending status for approval workflow
    """
    # Check if function exists
    func = FunctionService.get_function_by_id(function_id)
    if not func:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Function not found"
        )
    
    # Check if function is active
    if not func.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Function is not active"
        )
    
    # Check if user can execute this function
    user_role = current_user.get("role", "member")
    if not FunctionService.can_user_execute(user_role, func.get("min_role", "admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to execute this function"
        )
    
    try:
        # Create request for function execution
        request = RequestService.create_request(
            user_id=current_user["id"],
            function_id=function_id,
            parameters=execute_data.parameters
        )
        
        # Auto-approve for admin users
        if user_role == "admin":
            RequestService.approve_request(
                request_id=str(request["_id"]),
                reviewer_id=current_user.get("id")
            )
            # Update the status in the response to reflect the auto-approval
            request["status"] = "approved"
        
        return {
            "message": "Function execution request created successfully",
            "request_id": str(request["_id"]),
            "status": request["status"],
            "created_at": request["created_at"].isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create function execution request"
        )