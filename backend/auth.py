from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import structlog
from models import User, UserRole
from database import get_database
from config import settings

logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer()

class AuthManager:
    def __init__(self):
        self.pwd_context = pwd_context
        
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_expiration_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError as e:
            logger.error(f"JWT Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

auth_manager = AuthManager()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_database)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    
    try:
        payload = auth_manager.verify_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_doc = await db.users.find_one({"_id": user_id})
    if user_doc is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    user = User(**user_doc)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
        )
    
    # Check if user is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to too many failed login attempts",
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_role: UserRole):
    """Decorator to require specific user role"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        role_hierarchy = {
            UserRole.USER: 0,
            UserRole.PLUS: 1,
            UserRole.PRO: 2,
            UserRole.ADMIN: 3
        }
        
        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Convenience functions for role checking
require_plus = require_role(UserRole.PLUS)
require_pro = require_role(UserRole.PRO)
require_admin = require_role(UserRole.ADMIN)

async def increment_login_attempts(user_id: str, db):
    """Increment failed login attempts and lock account if necessary"""
    user_doc = await db.users.find_one({"_id": user_id})
    if not user_doc:
        return
    
    user = User(**user_doc)
    failed_attempts = user.failed_login_attempts + 1
    
    update_data = {"failed_login_attempts": failed_attempts}
    
    # Lock account if too many failed attempts
    if failed_attempts >= settings.max_login_attempts:
        lockout_until = datetime.utcnow() + timedelta(minutes=settings.lockout_duration_minutes)
        update_data["locked_until"] = lockout_until
        logger.warning(f"Account locked for user {user_id} until {lockout_until}")
    
    await db.users.update_one(
        {"_id": user_id},
        {"$set": update_data}
    )

async def reset_login_attempts(user_id: str, db):
    """Reset failed login attempts on successful login"""
    await db.users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "failed_login_attempts": 0,
                "last_login": datetime.utcnow()
            },
            "$unset": {"locked_until": ""}
        }
    )

async def create_user_session(user_id: str, token: str, db):
    """Create user session record"""
    session_data = {
        "_id": token,
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours),
        "active": True
    }
    
    await db.sessions.insert_one(session_data)

async def invalidate_user_session(token: str, db):
    """Invalidate user session"""
    await db.sessions.update_one(
        {"_id": token},
        {"$set": {"active": False}}
    )

async def cleanup_expired_sessions(db):
    """Cleanup expired sessions"""
    await db.sessions.delete_many({
        "expires_at": {"$lt": datetime.utcnow()}
    })