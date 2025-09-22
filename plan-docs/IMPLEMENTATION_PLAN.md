# Clean Backend Implementation Plan

## Project Overview
This document outlines the complete implementation plan for rebuilding the backend with minimal dependencies while maintaining full functionality.

## Current Status
✅ **Frontend**: Complete and working
- Single-page application with HTMX + Alpine.js
- 5 clean HTML files with full CRUD operations
- All UI functionality implemented and tested

✅ **Basic Backend**: Minimal FastAPI server (70 lines)
- Static file serving
- Route handling
- Health check endpoint

## Implementation Phases

### Phase 1: Core Infrastructure (Day 1)
**Goal**: Set up the foundation with minimal dependencies

#### 1.1 Dependencies Setup
Create `requirements.txt`:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
beanie==1.23.6
motor==3.3.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
slowapi==0.1.9
loguru==0.7.2
```

#### 1.2 Project Structure
```
backend/
├── main.py                    # Entry point (existing)
├── requirements.txt           # Dependencies
├── models/
│   ├── __init__.py
│   ├── user.py               # User document model
│   ├── function.py           # Function document model
│   └── request.py            # Request document model
├── api/
│   ├── __init__.py
│   ├── auth.py               # Authentication endpoints
│   ├── users.py              # User management endpoints
│   ├── functions.py          # Function management endpoints
│   └── requests.py           # Request management endpoints
├── services/
│   ├── __init__.py
│   ├── auth_service.py       # Authentication logic
│   └── database.py           # MongoDB connection
└── utils/
    ├── __init__.py
    ├── security.py           # JWT and password utilities
    └── dependencies.py       # Common dependencies
```

#### 1.3 Configuration Management
Create `config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "clean_dashboard"
    jwt_secret_key: str = "your-secret-key-change-this"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Phase 2: Database Layer (Day 2)
**Goal**: Implement MongoDB models and connections

#### 2.1 Database Connection
```python
# services/database.py
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from models.user import User
from models.function import Function
from models.request import Request
from config import settings

async def init_database():
    client = AsyncIOMotorClient(settings.mongodb_url)
    await init_beanie(
        database=client[settings.database_name],
        document_models=[User, Function, Request]
    )
```

#### 2.2 Model Implementation
- Copy and adapt models from MONGODB_DOCUMENTATION.md
- Implement all methods and class methods
- Add proper indexes and validation

#### 2.3 Database Initialization
- Create default admin user
- Add sample function for testing
- Database migration script if needed

### Phase 3: Authentication System (Day 3)
**Goal**: Implement JWT-based authentication

#### 3.1 Security Utilities
```python
# utils/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
```

#### 3.2 Authentication Service
- User authentication logic
- Token creation and validation
- Password verification

#### 3.3 Dependencies
```python
# utils/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from models.user import User
from config import settings

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await User.get(user_id)
    if user is None:
        raise credentials_exception
    return user
```

### Phase 4: API Implementation (Day 4-5)
**Goal**: Implement all CRUD endpoints

#### 4.1 Authentication Endpoints (`api/auth.py`)
- POST `/api/v1/auth/login`
- POST `/api/v1/auth/refresh`
- GET `/api/v1/auth/me`
- POST `/api/v1/auth/logout`
- POST `/api/v1/auth/validate`

#### 4.2 User Management Endpoints (`api/users.py`)
- GET `/api/v1/users` (list all)
- GET `/api/v1/users/{user_id}` (get one)
- POST `/api/v1/users` (create)
- PUT `/api/v1/users/{user_id}` (update)
- DELETE `/api/v1/users/{user_id}` (delete)

#### 4.3 Function Management Endpoints (`api/functions.py`)
- GET `/api/v1/functions` (list accessible)
- GET `/api/v1/functions/{function_id}` (get one)
- POST `/api/v1/functions` (create - admin only)
- PUT `/api/v1/functions/{function_id}` (update - admin only)
- DELETE `/api/v1/functions/{function_id}` (delete - admin only)
- POST `/api/v1/functions/{function_id}/execute` (create request)

#### 4.4 Request Management Endpoints (`api/requests.py`)
- GET `/api/v1/requests` (list based on role)
- GET `/api/v1/requests/{request_id}` (get one)
- POST `/api/v1/requests/{request_id}/approve` (approve)
- POST `/api/v1/requests/{request_id}/reject` (reject)
- DELETE `/api/v1/requests/{request_id}` (cancel)

### Phase 5: Security & Production Features (Day 6)
**Goal**: Add security, rate limiting, and production readiness

#### 5.1 Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    pass
```

#### 5.2 Error Handling
- Custom exception handlers
- Consistent error response format
- Proper HTTP status codes

#### 5.3 Logging
```python
from loguru import logger

logger.add("logs/app.log", rotation="1 day", retention="30 days", level="INFO")
```

#### 5.4 Environment Configuration
Create `.env` file:
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=clean_dashboard
JWT_SECRET_KEY=your-very-secure-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Phase 6: Integration & Testing (Day 7)
**Goal**: Integrate with frontend and test all functionality

#### 6.1 Frontend Integration
- Update main.py to include API routes
- Test all frontend pages with real API calls
- Ensure CORS is properly configured

#### 6.2 Manual Testing Checklist
- [ ] User registration and login
- [ ] Role-based access control
- [ ] Function CRUD operations
- [ ] Request creation and approval workflow
- [ ] User management
- [ ] Token refresh and logout

#### 6.3 Error Scenarios
- [ ] Invalid credentials
- [ ] Expired tokens
- [ ] Rate limiting
- [ ] Permission denied
- [ ] Resource not found

## Implementation Details

### File Creation Order
1. `requirements.txt` and install dependencies
2. `config.py` - Configuration management
3. `services/database.py` - Database connection
4. `models/` - All three model files
5. `utils/security.py` - Security utilities
6. `utils/dependencies.py` - Common dependencies
7. `services/auth_service.py` - Authentication service
8. `api/auth.py` - Authentication endpoints
9. `api/users.py` - User management endpoints
10. `api/functions.py` - Function management endpoints
11. `api/requests.py` - Request management endpoints
12. Update `main.py` - Include API routes
13. `.env` - Environment configuration

### Key Implementation Notes

#### MongoDB Integration
- Use Beanie ODM for clean async operations
- Implement proper indexes for performance
- Handle connection errors gracefully

#### Security Best Practices
- Hash all passwords with bcrypt
- Use secure JWT tokens with proper expiration
- Implement rate limiting on sensitive endpoints
- Validate all input data with Pydantic

#### Role-Based Access Control
```python
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def require_leader_or_admin(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "leader"]:
        raise HTTPException(status_code=403, detail="Leader or admin access required")
    return current_user
```

#### Function Execution Flow
1. User submits function execution → Creates request with "pending" status
2. Admin/Leader reviews request → Approves or rejects
3. If approved → Function executes automatically (future enhancement)
4. Result stored in request → Status becomes "completed" or "failed"

### Migration from Current Backend

#### What to Copy
- Model structures (adapt to Beanie)
- Business logic patterns
- Role hierarchy definitions
- Authentication flow concepts

#### What to Simplify
- Remove complex middleware
- Eliminate LDAP integration initially
- Remove audit logging (add later if needed)
- Simplify rate limiting
- Remove cache layers

#### What to Add Fresh
- Clean FastAPI structure
- Modern async/await patterns
- Simplified configuration
- Streamlined error handling

## Success Criteria

### Functional Requirements
✅ All frontend pages work with real data  
✅ User authentication and authorization  
✅ Complete CRUD operations for all entities  
✅ Role-based access control  
✅ Request approval workflow  

### Technical Requirements
✅ Clean, readable code structure  
✅ Minimal dependencies  
✅ Proper error handling  
✅ Security best practices  
✅ Rate limiting protection  

### Performance Requirements
✅ Fast response times (<200ms for most endpoints)  
✅ Efficient database queries  
✅ Proper async implementation  

This plan provides a clear roadmap for implementing a production-ready backend while maintaining the clean, minimal approach established with the frontend.