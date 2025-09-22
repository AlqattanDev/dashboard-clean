"""
Authentication Service - Handles both local and LDAP authentication
"""

import os
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from services.user_service import UserService
from utils.security import SecurityUtils
from config import settings

# LDAP support (optional)
try:
    import ldap3
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False

class AuthService:
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate user using local database or LDAP
        Returns: (success, user_data, error_message)
        """
        
        # Check if LDAP is enabled and available
        if settings.ldap_enabled and LDAP_AVAILABLE:
            return AuthService._authenticate_ldap(username, password)
        else:
            return AuthService._authenticate_local(username, password)
    
    @staticmethod
    def _authenticate_local(username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Authenticate against local database"""
        try:
            # Get user from database
            user = UserService.get_user_by_username(username)
            if not user:
                return False, None, "Invalid username or password"
            
            # Check if user is active
            if not user.get("is_active", False):
                return False, None, "User account is disabled"
            
            # Verify password
            if not UserService.verify_password(password, user.get("password_hash", "")):
                return False, None, "Invalid username or password"
            
            # Update last login
            UserService.update_last_login(str(user["_id"]))
            
            # Format user data
            user_data = {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user.get("email", ""),
                "full_name": user.get("full_name", ""),
                "role": user.get("role", "member"),
                "is_active": user.get("is_active", True),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login")
            }
            
            return True, user_data, None
            
        except Exception as e:
            return False, None, f"Authentication error: {str(e)}"
    
    @staticmethod
    def _authenticate_ldap(username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Authenticate against LDAP server"""
        if not LDAP_AVAILABLE:
            return False, None, "LDAP not available. Install python-ldap3."
        
        try:
            # LDAP configuration from settings
            ldap_server = getattr(settings, 'ldap_server', 'ldap://localhost:389')
            ldap_base_dn = getattr(settings, 'ldap_base_dn', 'dc=example,dc=com')
            ldap_user_dn_template = getattr(settings, 'ldap_user_dn_template', 'uid={username},ou=users,{base_dn}')
            
            # Format user DN
            user_dn = ldap_user_dn_template.format(username=username, base_dn=ldap_base_dn)
            
            # Create LDAP connection
            server = ldap3.Server(ldap_server)
            conn = ldap3.Connection(server, user=user_dn, password=password)
            
            # Attempt to bind (authenticate)
            if not conn.bind():
                return False, None, "Invalid LDAP credentials"
            
            # Search for user attributes
            search_filter = f"(uid={username})"
            conn.search(
                search_base=f"ou=users,{ldap_base_dn}",
                search_filter=search_filter,
                attributes=['uid', 'mail', 'cn', 'displayName', 'memberOf']
            )
            
            if not conn.entries:
                return False, None, "User not found in LDAP"
            
            ldap_user = conn.entries[0]
            
            # Determine role from LDAP groups (customize as needed)
            role = AuthService._determine_role_from_ldap(ldap_user)
            
            # Get or create user in local database
            local_user = UserService.get_user_by_username(username)
            
            if not local_user:
                # Create user if doesn't exist
                email = str(ldap_user.mail) if ldap_user.mail else f"{username}@company.com"
                full_name = str(ldap_user.cn) if ldap_user.cn else username
                
                local_user = UserService.create_user(
                    username=username,
                    email=email,
                    password="",  # No password stored for LDAP users
                    role=role,
                    full_name=full_name
                )
                local_user["id"] = str(local_user["_id"])
            else:
                # Update user role if changed in LDAP
                if local_user.get("role") != role:
                    UserService.update_user(str(local_user["_id"]), {"role": role})
                    local_user["role"] = role
                
                # Update last login
                UserService.update_last_login(str(local_user["_id"]))
                local_user["id"] = str(local_user["_id"])
            
            # Check if user is active
            if not local_user.get("is_active", False):
                return False, None, "User account is disabled"
            
            conn.unbind()
            
            return True, local_user, None
            
        except Exception as e:
            return False, None, f"LDAP authentication error: {str(e)}"
    
    @staticmethod
    def _determine_role_from_ldap(ldap_user) -> str:
        """Determine user role based on LDAP group memberships"""
        # This is a sample implementation - customize based on your LDAP structure
        groups = []
        if hasattr(ldap_user, 'memberOf') and ldap_user.memberOf:
            groups = [str(group).lower() for group in ldap_user.memberOf]
        
        # Check for admin groups
        admin_groups = ['cn=admins', 'cn=administrators', 'cn=dashboard-admins']
        if any(admin_group in group for group in groups for admin_group in admin_groups):
            return "admin"
        
        # Check for leader groups
        leader_groups = ['cn=leaders', 'cn=managers', 'cn=dashboard-leaders']
        if any(leader_group in group for group in groups for leader_group in leader_groups):
            return "leader"
        
        # Default to member
        return "member"
    
    @staticmethod
    def create_login_response(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a standardized login response with JWT token"""
        # Create JWT token
        access_token = SecurityUtils.create_user_token(
            user_id=user_data["id"],
            username=user_data["username"],
            role=user_data["role"],
            email=user_data.get("email", "")
        )
        
        # Return response
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_data["id"],
                "username": user_data["username"],
                "email": user_data.get("email", ""),
                "full_name": user_data.get("full_name", ""),
                "role": user_data["role"],
                "is_active": user_data.get("is_active", True),
                "created_at": user_data.get("created_at"),
                "last_login": user_data.get("last_login")
            }
        }
    
    @staticmethod
    def validate_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Validate a JWT token and return user data"""
        try:
            user_data = SecurityUtils.extract_user_from_token(token)
            if not user_data:
                return False, None, "Invalid token"
            
            # Get current user data from database
            user = UserService.get_user_by_id(user_data["id"])
            if not user:
                return False, None, "User not found"
            
            if not user.get("is_active", False):
                return False, None, "User account is disabled"
            
            return True, user, None
            
        except Exception as e:
            return False, None, f"Token validation error: {str(e)}"
    
    @staticmethod
    def refresh_user_token(token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Refresh a JWT token"""
        try:
            # Validate current token
            success, user_data, error = AuthService.validate_token(token)
            if not success:
                return False, None, error
            
            # Create new token
            new_token = SecurityUtils.create_user_token(
                user_id=user_data["id"],
                username=user_data["username"],
                role=user_data["role"],
                email=user_data.get("email", "")
            )
            
            return True, new_token, None
            
        except Exception as e:
            return False, None, f"Token refresh error: {str(e)}"