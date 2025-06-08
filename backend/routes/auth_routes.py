from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from datetime import timedelta, datetime
import structlog
from models import (
    UserCreate, UserResponse, LoginRequest, Token, RefreshTokenRequest,
    User, SuccessResponse, ErrorResponse
)
from auth import (
    auth_manager, get_current_user, increment_login_attempts, 
    reset_login_attempts, create_user_session
)
from database import get_database
from rate_limiter import rate_limit_decorator, check_ip_rate_limits
from slowapi.util import get_remote_address
from config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, request: Request, db = Depends(get_database)):
    """Register a new user"""
    
    # Check IP rate limits for registration
    ip_address = get_remote_address(request)
    if not await check_ip_rate_limits(ip_address, "registration"):
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts from this IP",
            headers={"Retry-After": "3600"}
        )
    
    # Check if user already exists
    existing_user = await db.users.find_one({
        "$or": [
            {"email": user_data.email},
            {"username": user_data.username}
        ]
    })
    
    if existing_user:
        if existing_user["email"] == user_data.email:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
    
    # Create new user
    hashed_password = auth_manager.hash_password(user_data.password)
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        display_name=user_data.display_name or user_data.username,
        is_active=True,
        is_verified=False  # Email verification required
    )
    
    # Insert user into database
    result = await db.users.insert_one(user.model_dump())
    user.id = str(result.inserted_id)
    
    logger.info(f"New user registered: {user.email}")
    
    return UserResponse(**user.model_dump())

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, request: Request, db = Depends(get_database)):
    """Authenticate user and return JWT tokens"""
    
    # Check IP rate limits for authentication
    ip_address = get_remote_address(request)
    if not await check_ip_rate_limits(ip_address, "auth"):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts from this IP",
            headers={"Retry-After": "60"}
        )
    
    # Find user by email
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    user = User(**user_doc)
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=423,
            detail="Account temporarily locked due to too many failed attempts"
        )
    
    # Verify password
    if not auth_manager.verify_password(login_data.password, user.hashed_password):
        # Increment failed attempts
        await increment_login_attempts(user.id, db)
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Account is deactivated"
        )
    
    # Reset failed login attempts on successful login
    await reset_login_attempts(user.id, db)
    
    # Create tokens
    access_token = auth_manager.create_access_token(data={"sub": user.id})
    refresh_token = auth_manager.create_refresh_token(data={"sub": user.id})
    
    # Store session in database
    await create_user_session(user.id, access_token, db)
    
    logger.info(f"User logged in: {user.email}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_hours * 3600,
        user=UserResponse(**user.model_dump())
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest, db = Depends(get_database)):
    """Refresh access token using refresh token"""
    
    try:
        payload = auth_manager.verify_token(refresh_data.refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if not user_id or token_type != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )
    
    # Get user from database
    user_doc = await db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    
    user = User(**user_doc)
    
    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Account is deactivated"
        )
    
    # Create new tokens
    access_token = auth_manager.create_access_token(data={"sub": user.id})
    new_refresh_token = auth_manager.create_refresh_token(data={"sub": user.id})
    
    # Store new session
    await create_user_session(user.id, access_token, db)
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_hours * 3600,
        user=UserResponse(**user.model_dump())
    )

@router.post("/logout", response_model=SuccessResponse)
async def logout(current_user: User = Depends(get_current_user), db = Depends(get_database)):
    """Logout user and invalidate token"""
    
    # In a more sophisticated implementation, you would maintain a blacklist of tokens
    # For now, we'll just return success
    
    logger.info(f"User logged out: {current_user.email}")
    
    return SuccessResponse(
        message="Successfully logged out"
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(**current_user.model_dump())

@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Change user password"""
    
    # Verify current password
    if not auth_manager.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 8 characters long"
        )
    
    # Hash new password
    new_hashed_password = auth_manager.hash_password(new_password)
    
    # Update password in database
    await db.users.update_one(
        {"_id": current_user.id},
        {"$set": {"hashed_password": new_hashed_password}}
    )
    
    logger.info(f"Password changed for user: {current_user.email}")
    
    return SuccessResponse(
        message="Password changed successfully"
    )