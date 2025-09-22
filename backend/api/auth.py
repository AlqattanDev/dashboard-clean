"""
Authentication API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from services.auth_service import AuthService
from utils.dependencies import get_current_user, security
from config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class TokenValidationResponse(BaseModel):
    valid: bool
    user: Optional[dict] = None

class MessageResponse(BaseModel):
    message: str

# Authentication endpoints
@router.post("/login", response_model=LoginResponse)
async def login(request_data: LoginRequest):
    """
    Authenticate user and return JWT token
    Supports both local and LDAP authentication
    """
    # Authenticate user
    success, user_data, error_message = AuthService.authenticate_user(
        request_data.username, 
        request_data.password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message or "Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create login response with JWT token
    return AuthService.create_login_response(user_data)

@router.post("/refresh", response_model=dict)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Refresh an existing JWT token
    """
    token = credentials.credentials
    
    success, new_token, error_message = AuthService.refresh_user_token(token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message or "Token refresh failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "access_token": new_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return current_user

@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (client should discard token)
    In a stateless JWT system, logout is handled client-side
    """
    return {"message": "Logged out successfully"}

@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate a JWT token and return user information
    Used by frontend for session checks
    """
    token = credentials.credentials
    
    success, user_data, error_message = AuthService.validate_token(token)
    
    if not success:
        return TokenValidationResponse(valid=False, user=None)
    
    return TokenValidationResponse(
        valid=True,
        user={
            "id": user_data["id"],
            "username": user_data["username"],
            "email": user_data.get("email", ""),
            "full_name": user_data.get("full_name", ""),
            "role": user_data["role"],
            "is_active": user_data.get("is_active", True),
            "created_at": user_data.get("created_at"),
            "last_login": user_data.get("last_login")
        }
    )