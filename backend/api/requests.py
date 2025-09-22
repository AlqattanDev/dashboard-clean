"""
Request Management API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from services.request_service import RequestService
from services.function_service import FunctionService
from utils.dependencies import (
    get_current_user,
    require_leader_or_admin,
    require_member_or_above
)

router = APIRouter(prefix="/api/v1/requests", tags=["requests"])

# Request/Response models
class RequestResponse(BaseModel):
    id: str
    user_id: str
    user_username: str
    user_email: str
    function_id: str
    function_name: str
    function_description: Optional[str] = None
    parameters: Dict[str, Any]
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

class ApprovalRequest(BaseModel):
    pass  # No additional data needed for approval

class RejectionRequest(BaseModel):
    reason: str

class MessageResponse(BaseModel):
    message: str

# Request Management Endpoints

@router.get("/", response_model=List[RequestResponse])
async def list_requests(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get requests based on user role
    - Members: See only their own requests
    - Leaders/Admins: See all requests
    """
    try:
        user_role = current_user.get("role", "member")
        user_id = current_user.get("id")
        
        # Calculate skip for pagination
        skip = (page - 1) * limit
        
        # Role-based filtering
        if user_role == "member":
            # Members can only see their own requests
            requests = RequestService.get_user_requests(
                user_id=user_id,
                skip=skip,
                limit=limit,
                status_filter=status_filter
            )
        else:
            # Leaders and admins can see all requests
            requests = RequestService.get_all_requests(
                skip=skip,
                limit=limit,
                status_filter=status_filter
            )
        
        result = []
        for req in requests:
            result.append(RequestResponse(
                id=req.get("id", str(req.get("_id", ""))),
                user_id=req.get("user_id", ""),
                user_username=req.get("user_username", "Unknown"),
                user_email=req.get("user_email", ""),
                function_id=req.get("function_id", ""),
                function_name=req.get("function_name", "Unknown"),
                function_description=req.get("function_description"),
                parameters=req.get("parameters", {}),
                status=req["status"],
                reviewed_by=req.get("reviewed_by"),
                reviewed_at=req["reviewed_at"].isoformat() if req.get("reviewed_at") else None,
                rejection_reason=req.get("rejection_reason"),
                execution_result=req.get("execution_result"),
                execution_time_ms=req.get("execution_time_ms"),
                error_message=req.get("error_message"),
                created_at=req["created_at"].isoformat(),
                updated_at=req["updated_at"].isoformat()
            ))
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve requests"
        )

@router.get("/list", response_model=List[RequestResponse])
async def list_requests_alias(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Alias for GET /requests (frontend compatibility)"""
    return await list_requests(page, limit, status_filter, current_user)

@router.get("/{request_id}", response_model=RequestResponse)
async def get_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get specific request by ID
    Access control: Users can view own requests, leaders/admins can view all
    """
    try:
        request = RequestService.get_request_by_id(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        
        # Check access permissions
        user_role = current_user.get("role", "member")
        user_id = current_user.get("id")
        
        if user_role == "member" and str(request["user_id"]) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own requests."
            )
        
        return RequestResponse(
            id=request.get("id", str(request.get("_id", ""))),
            user_id=request.get("user_id", ""),
            user_username=request.get("user_username", "Unknown"),
            user_email=request.get("user_email", ""),
            function_id=request.get("function_id", ""),
            function_name=request.get("function_name", "Unknown"),
            function_description=request.get("function_description"),
            parameters=request.get("parameters", {}),
            status=request["status"],
            reviewed_by=request.get("reviewed_by"),
            reviewed_at=request["reviewed_at"].isoformat() if request.get("reviewed_at") else None,
            rejection_reason=request.get("rejection_reason"),
            execution_result=request.get("execution_result"),
            execution_time_ms=request.get("execution_time_ms"),
            error_message=request.get("error_message"),
            created_at=request["created_at"].isoformat(),
            updated_at=request["updated_at"].isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve request"
        )

@router.post("/{request_id}/approve", response_model=RequestResponse)
async def approve_request(
    request_id: str,
    approval_data: ApprovalRequest,
    current_user: dict = Depends(require_leader_or_admin)
):
    """
    Approve request (leader/admin only)
    Changes status from pending to approved
    """
    try:
        # Check if request exists and is pending
        request = RequestService.get_request_by_id(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        
        if request["status"] != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve request with status: {request['status']}"
            )
        
        # Approve request
        success = RequestService.approve_request(
            request_id=request_id,
            reviewer_id=current_user.get("id")
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to approve request"
            )
        
        # Get the updated request to return
        updated_request = RequestService.get_request_by_id(request_id)
        
        return RequestResponse(
            id=updated_request.get("id", ""),
            user_id=updated_request.get("user_id", ""),
            user_username=updated_request.get("user_username", "Unknown"),
            user_email=updated_request.get("user_email", ""),
            function_id=updated_request.get("function_id", ""),
            function_name=updated_request.get("function_name", "Unknown"),
            function_description=updated_request.get("function_description"),
            parameters=updated_request.get("parameters", {}),
            status=updated_request["status"],
            reviewed_by=updated_request.get("reviewed_by"),
            reviewed_at=updated_request["reviewed_at"].isoformat() if updated_request.get("reviewed_at") else None,
            rejection_reason=updated_request.get("rejection_reason"),
            execution_result=updated_request.get("execution_result"),
            execution_time_ms=updated_request.get("execution_time_ms"),
            error_message=updated_request.get("error_message"),
            created_at=updated_request["created_at"].isoformat(),
            updated_at=updated_request["updated_at"].isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve request"
        )

@router.post("/{request_id}/reject", response_model=RequestResponse)
async def reject_request(
    request_id: str,
    rejection_data: RejectionRequest,
    current_user: dict = Depends(require_leader_or_admin)
):
    """
    Reject request (leader/admin only)
    Changes status from pending to rejected with reason
    """
    try:
        # Check if request exists and is pending
        request = RequestService.get_request_by_id(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        
        if request["status"] != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject request with status: {request['status']}"
            )
        
        # Reject request
        success = RequestService.reject_request(
            request_id=request_id,
            reviewer_id=current_user.get("id"),
            reason=rejection_data.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reject request"
            )
        
        # Get the updated request to return
        updated_request = RequestService.get_request_by_id(request_id)
        
        return RequestResponse(
            id=updated_request.get("id", ""),
            user_id=updated_request.get("user_id", ""),
            user_username=updated_request.get("user_username", "Unknown"),
            user_email=updated_request.get("user_email", ""),
            function_id=updated_request.get("function_id", ""),
            function_name=updated_request.get("function_name", "Unknown"),
            function_description=updated_request.get("function_description"),
            parameters=updated_request.get("parameters", {}),
            status=updated_request["status"],
            reviewed_by=updated_request.get("reviewed_by"),
            reviewed_at=updated_request["reviewed_at"].isoformat() if updated_request.get("reviewed_at") else None,
            rejection_reason=updated_request.get("rejection_reason"),
            execution_result=updated_request.get("execution_result"),
            execution_time_ms=updated_request.get("execution_time_ms"),
            error_message=updated_request.get("error_message"),
            created_at=updated_request["created_at"].isoformat(),
            updated_at=updated_request["updated_at"].isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject request"
        )

@router.delete("/{request_id}", response_model=MessageResponse)
async def cancel_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel/delete request
    Access control: Request creator or admin can cancel
    """
    try:
        # Check if request exists
        request = RequestService.get_request_by_id(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        
        # Check access permissions
        user_role = current_user.get("role", "member")
        user_id = current_user.get("id")
        
        # Allow deletion if: user owns the request OR user is admin
        if user_role != "admin" and str(request["user_id"]) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only cancel your own requests."
            )
        
        # Check if request can be cancelled
        if request["status"] in ["completed", "failed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel request with status: {request['status']}"
            )
        
        # Cancel/delete request
        success = RequestService.delete_request(request_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel request"
            )
        
        return MessageResponse(message="Request cancelled successfully")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel request"
        )