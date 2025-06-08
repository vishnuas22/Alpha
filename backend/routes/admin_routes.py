from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import structlog
from models import User, UserRole, UserResponse, SuccessResponse, UsageStats
from auth import get_current_user, require_admin
from database import get_database
from datetime import datetime, timedelta

logger = structlog.get_logger()

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search by email or username"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    current_user: User = Depends(require_admin),
    db = Depends(get_database)
):
    """Get all users (admin only)"""
    
    # Build query
    query = {}
    
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}},
            {"display_name": {"$regex": search, "$options": "i"}}
        ]
    
    if role:
        query["role"] = role
    
    # Execute query
    cursor = db.users.find(query).sort("created_at", -1).skip(offset).limit(limit)
    
    users = []
    async for user_doc in cursor:
        users.append(UserResponse(**user_doc))
    
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(require_admin),
    db = Depends(get_database)
):
    """Get specific user by ID (admin only)"""
    
    user_doc = await db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**user_doc)

@router.put("/users/{user_id}/role", response_model=SuccessResponse)
async def update_user_role(
    user_id: str,
    new_role: UserRole,
    current_user: User = Depends(require_admin),
    db = Depends(get_database)
):
    """Update user role (admin only)"""
    
    # Check if user exists
    user_doc = await db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-demotion from admin
    if user_id == current_user.id and new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=400,
            detail="Cannot demote yourself from admin role"
        )
    
    # Update role
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"role": new_role, "updated_at": datetime.utcnow()}}
    )
    
    logger.info(f"User role updated: {user_id} -> {new_role}")
    
    return SuccessResponse(message=f"User role updated to {new_role}")

@router.put("/users/{user_id}/status", response_model=SuccessResponse)
async def update_user_status(
    user_id: str,
    is_active: bool,
    current_user: User = Depends(require_admin),
    db = Depends(get_database)
):
    """Activate/deactivate user (admin only)"""
    
    # Check if user exists
    user_doc = await db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-deactivation
    if user_id == current_user.id and not is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own account"
        )
    
    # Update status
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"is_active": is_active, "updated_at": datetime.utcnow()}}
    )
    
    status = "activated" if is_active else "deactivated"
    logger.info(f"User {status}: {user_id}")
    
    return SuccessResponse(message=f"User {status} successfully")

@router.get("/stats", response_model=UsageStats)
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db = Depends(get_database)
):
    """Get system usage statistics (admin only)"""
    
    # Get basic counts
    total_users = await db.users.count_documents({})
    total_chats = await db.chats.count_documents({})
    total_messages = await db.messages.count_documents({})
    
    # Get token usage (approximate)
    pipeline = [
        {"$group": {"_id": None, "total_tokens": {"$sum": "$tokens_used"}}}
    ]
    token_result = await db.messages.aggregate(pipeline).to_list(1)
    total_tokens = token_result[0]["total_tokens"] if token_result else 0
    
    # Get model usage
    model_pipeline = [
        {"$group": {"_id": "$model", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    model_usage = {}
    async for result in db.messages.aggregate(model_pipeline):
        if result["_id"]:
            model_usage[result["_id"]] = result["count"]
    
    # Get daily usage for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_pipeline = [
        {"$match": {"created_at": {"$gte": thirty_days_ago}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$created_at"
                    }
                },
                "messages": {"$sum": 1},
                "tokens": {"$sum": "$tokens_used"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    daily_usage = []
    async for result in db.messages.aggregate(daily_pipeline):
        daily_usage.append({
            "date": result["_id"],
            "messages": result["messages"],
            "tokens": result["tokens"] or 0
        })
    
    # Calculate average response time
    response_time_pipeline = [
        {"$match": {"processing_time": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": None, "avg_time": {"$avg": "$processing_time"}}}
    ]
    avg_time_result = await db.messages.aggregate(response_time_pipeline).to_list(1)
    avg_response_time = avg_time_result[0]["avg_time"] if avg_time_result else 0
    
    return UsageStats(
        total_messages=total_messages,
        total_tokens=total_tokens,
        total_chats=total_chats,
        avg_response_time=avg_response_time,
        model_usage=model_usage,
        daily_usage=daily_usage
    )

@router.delete("/users/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db = Depends(get_database)
):
    """Delete user and all associated data (admin only)"""
    
    # Check if user exists
    user_doc = await db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )
    
    # Delete user data
    await db.messages.delete_many({"user_id": user_id})
    await db.chats.delete_many({"user_id": user_id})
    await db.files.delete_many({"user_id": user_id})
    await db.sessions.delete_many({"user_id": user_id})
    
    # Delete user
    await db.users.delete_one({"_id": user_id})
    
    logger.info(f"User deleted: {user_id}")
    
    return SuccessResponse(message="User and all associated data deleted successfully")