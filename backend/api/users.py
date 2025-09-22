"""
User Management API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from services.user_service import UserService
from utils.dependencies import (
    get_current_user, 
    require_admin, 
    AuthDependencies
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Request/Response models
class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "member"
    password: str

class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None

class MessageResponse(BaseModel):
    message: str

# User Management Endpoints

@router.get("/", response_model=List[UserResponse])
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role"),
    current_user: dict = Depends(require_admin)
):
    """
    Get list of all users (admin only)
    Supports pagination and role filtering
    """
    try:
        # Calculate skip value for pagination
        skip = (page - 1) * limit
        
        users = UserService.get_all_users(
            skip=skip, 
            limit=limit, 
            role_filter=role
        )
        
        return [
            UserResponse(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                full_name=user.get("full_name"),
                role=user["role"],
                is_active=user["is_active"],
                created_at=user["created_at"].isoformat(),
                last_login=user["last_login"].isoformat() if user.get("last_login") else None
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.get("/list", response_model=List[UserResponse])
async def list_users_alias(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    role: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin)
):
    """Alias for GET /users (frontend compatibility)"""
    return await list_users(page, limit, role, current_user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get specific user by ID
    Access control: Admin can view any, users can view self
    """
    try:
        # Check access permissions
        user_role = current_user.get("role", "member")
        current_user_id = current_user.get("id")
        
        # Only admin can view other users, users can view themselves
        if user_role != "admin" and current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own profile."
            )
        
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user.get("full_name"),
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"].isoformat(),
            last_login=user["last_login"].isoformat() if user.get("last_login") else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Create new user (admin only)
    """
    # Validate role
    valid_roles = ["admin", "leader", "member"]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    try:
        # Create user
        new_user = UserService.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role,
            full_name=user_data.full_name
        )
        
        return UserResponse(
            id=str(new_user["_id"]),
            username=new_user["username"],
            email=new_user["email"],
            full_name=new_user.get("full_name"),
            role=new_user["role"],
            is_active=new_user["is_active"],
            created_at=new_user["created_at"].isoformat(),
            last_login=None
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user
    Access control: Admin can modify any, leader can modify members, users can modify self
    """
    # Check access permissions first
    user_role = current_user.get("role", "member")
    current_user_id = current_user.get("id")
    
    # Check if user exists
    existing_user = UserService.get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Access control logic
    if user_role == "admin":
        # Admin can modify anyone
        pass
    elif user_role == "leader":
        # Leader can modify members and themselves
        if current_user_id != user_id and existing_user.get("role") != "member":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Leaders can only modify their own profile and member accounts."
            )
    elif current_user_id != user_id:
        # Regular users can only modify themselves
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only modify your own profile."
        )
    
    # Validate role if provided
    if user_data.role is not None:
        valid_roles = ["admin", "leader", "member"]
        if user_data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        # Only admin can change roles
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can change user roles"
            )
    
    try:
        # Prepare update data
        update_data = {}
        if user_data.email is not None:
            update_data["email"] = user_data.email
        if user_data.full_name is not None:
            update_data["full_name"] = user_data.full_name
        if user_data.role is not None:
            update_data["role"] = user_data.role
        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active
        
        # Update user
        success = UserService.update_user(user_id, update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
        
        # Get updated user data
        updated_user = UserService.get_user_by_id(user_id)
        
        return UserResponse(
            id=updated_user["id"],
            username=updated_user["username"],
            email=updated_user["email"],
            full_name=updated_user.get("full_name"),
            role=updated_user["role"],
            is_active=updated_user["is_active"],
            created_at=updated_user["created_at"].isoformat(),
            last_login=updated_user["last_login"].isoformat() if updated_user.get("last_login") else None
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Delete user (admin only)
    """
    # Check if user exists
    existing_user = UserService.get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if current_user.get("id") == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        # Delete user
        success = UserService.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
        
        return MessageResponse(message="User deleted successfully")
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )