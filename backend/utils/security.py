"""
Security utilities for JWT token management and password handling
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SecurityUtils:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.jwt_secret_key, 
            algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.jwt_secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def create_user_token(user_id: str, username: str, role: str, email: str = "") -> str:
        """Create a JWT token for a user with their information"""
        token_data = {
            "sub": user_id,  # Subject (user ID)
            "username": username,
            "role": role,
            "email": email,
            "type": "access"
        }
        return SecurityUtils.create_access_token(token_data)
    
    @staticmethod
    def extract_user_from_token(token: str) -> Optional[Dict[str, Any]]:
        """Extract user information from a JWT token"""
        payload = SecurityUtils.verify_token(token)
        if not payload:
            return None
        
        return {
            "id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "email": payload.get("email", "")
        }
    
    @staticmethod
    def is_token_expired(token: str) -> bool:
        """Check if a token is expired"""
        payload = SecurityUtils.verify_token(token)
        if not payload:
            return True
        
        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            return True
        
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        return datetime.utcnow() > exp_datetime
    
    @staticmethod
    def refresh_token(token: str) -> Optional[str]:
        """Create a new token based on an existing valid token"""
        user_data = SecurityUtils.extract_user_from_token(token)
        if not user_data:
            return None
        
        return SecurityUtils.create_user_token(
            user_data["id"],
            user_data["username"],
            user_data["role"],
            user_data["email"]
        )