"""
User Service - Database operations for users collection
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from passlib.context import CryptContext
from .database import db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_user(username: str, email: str, password: str, role: str = "member", 
                   full_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user"""
        user_data = {
            "username": username,
            "email": email,
            "password_hash": UserService.hash_password(password),
            "role": role,
            "full_name": full_name,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        try:
            result = db.users.insert_one(user_data)
            user_data["_id"] = result.inserted_id
            # Remove password hash from return
            del user_data["password_hash"]
            return user_data
        except DuplicateKeyError as e:
            if "username" in str(e):
                raise ValueError("Username already exists")
            elif "email" in str(e):
                raise ValueError("Email already exists")
            else:
                raise ValueError("User already exists")
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
                del user["_id"]
                # Remove password hash
                if "password_hash" in user:
                    del user["password_hash"]
            return user
        except Exception:
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Get user by username (for authentication)"""
        return db.users.find_one({"username": username})
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        user = db.users.find_one({"email": email})
        if user:
            user["id"] = str(user["_id"])
            del user["_id"]
            # Remove password hash
            if "password_hash" in user:
                del user["password_hash"]
        return user
    
    @staticmethod
    def get_all_users(skip: int = 0, limit: int = 100, 
                     role_filter: Optional[str] = None,
                     status_filter: Optional[str] = None,
                     search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all users with filtering"""
        query = {}
        
        # Apply filters
        if role_filter:
            query["role"] = role_filter
        if status_filter:
            if status_filter == "active":
                query["is_active"] = True
            elif status_filter == "inactive":
                query["is_active"] = False
        if search:
            query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"full_name": {"$regex": search, "$options": "i"}}
            ]
        
        users = list(db.users.find(query)
                    .sort("created_at", -1)
                    .skip(skip)
                    .limit(limit))
        
        # Format users
        for user in users:
            user["id"] = str(user["_id"])
            del user["_id"]
            # Remove password hash
            if "password_hash" in user:
                del user["password_hash"]
        
        return users
    
    @staticmethod
    def update_user(user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user"""
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Hash password if provided
        if "password" in update_data:
            update_data["password_hash"] = UserService.hash_password(update_data["password"])
            del update_data["password"]
        
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    @staticmethod
    def delete_user(user_id: str) -> bool:
        """Delete user"""
        try:
            result = db.users.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    @staticmethod
    def update_last_login(user_id: str):
        """Update user's last login time"""
        try:
            db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        except Exception:
            pass
    
    @staticmethod
    def can_user_access_role(user_role: str, required_role: str) -> bool:
        """Check if user role can access required role"""
        role_hierarchy = {"admin": 1, "leader": 2, "member": 3}
        user_level = role_hierarchy.get(user_role, 999)
        required_level = role_hierarchy.get(required_role, 1)
        return user_level <= required_level
    
    @staticmethod
    def can_user_modify_target(user_role: str, target_role: str) -> bool:
        """Check if user can modify target user based on roles"""
        if user_role == "admin":
            return True
        elif user_role == "leader":
            return target_role in ["member"]
        else:
            return False

# Initialize default admin user
def create_default_admin():
    """Create default admin user if none exists"""
    admin = db.users.find_one({"role": "admin"})
    if not admin:
        try:
            UserService.create_user(
                username="admin",
                email="admin@dashboard.local",
                password="admin123",
                role="admin",
                full_name="System Administrator"
            )
            print("✅ Default admin user created: admin/admin123")
        except ValueError:
            print("ℹ️ Admin user already exists")