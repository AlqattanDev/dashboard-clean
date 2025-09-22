"""
FastAPI dependencies for authentication and authorization
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.user_service import UserService
from utils.security import SecurityUtils

# Security scheme for JWT bearer tokens
security = HTTPBearer()

class AuthDependencies:
    
    @staticmethod
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current authenticated user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Extract token from credentials
            token = credentials.credentials
            
            # Verify and decode token
            user_data = SecurityUtils.extract_user_from_token(token)
            if not user_data or not user_data.get("id"):
                raise credentials_exception
            
            # Get full user data from database
            user = UserService.get_user_by_id(user_data["id"])
            if not user:
                raise credentials_exception
            
            # Check if user is active
            if not user.get("is_active", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is disabled"
                )
            
            return user
            
        except Exception:
            raise credentials_exception
    
    @staticmethod
    async def get_current_active_user(current_user: dict = Depends(lambda: AuthDependencies.get_current_user)):
        """Get current active user (alias for get_current_user)"""
        return current_user
    
    @staticmethod
    def require_role(required_role: str):
        """Create a dependency that requires a specific role or higher"""
        async def role_checker(current_user: dict = Depends(AuthDependencies.get_current_user)):
            user_role = current_user.get("role", "")
            
            if not UserService.can_user_access_role(user_role, required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. {required_role.title()} role required."
                )
            
            return current_user
        return role_checker
    
    @staticmethod
    def require_admin():
        """Dependency that requires admin role"""
        return AuthDependencies.require_role("admin")
    
    @staticmethod
    def require_leader_or_admin():
        """Dependency that requires leader or admin role"""
        return AuthDependencies.require_role("leader")
    
    @staticmethod
    def require_member_or_above():
        """Dependency that requires member, leader, or admin role"""
        return AuthDependencies.require_role("member")
    
    @staticmethod
    async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
        """Get current user if token is provided, None otherwise"""
        if not credentials:
            return None
        
        try:
            token = credentials.credentials
            user_data = SecurityUtils.extract_user_from_token(token)
            if not user_data or not user_data.get("id"):
                return None
            
            user = UserService.get_user_by_id(user_data["id"])
            if not user or not user.get("is_active", False):
                return None
            
            return user
        except Exception:
            return None
    
    @staticmethod
    def can_modify_user(target_user_id: str):
        """Create a dependency that checks if current user can modify target user"""
        async def modifier_checker(current_user: dict = Depends(AuthDependencies.get_current_user)):
            # Admin can modify anyone
            if current_user.get("role") == "admin":
                return current_user
            
            # Users can modify themselves
            if current_user.get("id") == target_user_id:
                return current_user
            
            # Leader can modify members
            if current_user.get("role") == "leader":
                target_user = UserService.get_user_by_id(target_user_id)
                if target_user and target_user.get("role") == "member":
                    return current_user
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Cannot modify this user."
            )
        
        return modifier_checker
    
    @staticmethod
    def can_view_user(target_user_id: str):
        """Create a dependency that checks if current user can view target user"""
        async def viewer_checker(current_user: dict = Depends(AuthDependencies.get_current_user)):
            # Admin can view anyone
            if current_user.get("role") == "admin":
                return current_user
            
            # Users can view themselves
            if current_user.get("id") == target_user_id:
                return current_user
            
            # For now, only admin can view other users
            # This can be modified based on requirements
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Cannot view this user."
            )
        
        return viewer_checker

# Convenience functions for common auth patterns
get_current_user = AuthDependencies.get_current_user
require_admin = AuthDependencies.require_admin()
require_leader_or_admin = AuthDependencies.require_leader_or_admin()
require_member_or_above = AuthDependencies.require_member_or_above()