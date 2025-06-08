from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import structlog
from models import (
    Chat, ChatCreate, ChatUpdate, ChatResponse,
    Message, MessageCreate, MessageResponse, MessageType,
    User, SuccessResponse, PaginatedResponse, ModelName
)
from auth import get_current_user
from database import get_database
from ai_service import ai_service
from websocket_manager import manager as ws_manager
from rate_limiter import rate_limit_decorator
from datetime import datetime
import uuid

logger = structlog.get_logger()

router = APIRouter(prefix="/chats", tags=["Chats"])

@router.post("", response_model=ChatResponse)
@rate_limit_decorator("chat")
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Create a new chat"""
    
    chat = Chat(
        user_id=current_user.id,
        title=chat_data.title or "New Chat",
        model=chat_data.model or ModelName.ALPHA_ORIGIN,
        system_prompt=chat_data.system_prompt
    )
    
    # Insert into database
    result = await db.chats.insert_one(chat.model_dump())
    chat.id = str(result.inserted_id)
    
    logger.info(f"Chat created: {chat.id} for user {current_user.id}")
    
    # Send update to connected clients
    await ws_manager.send_chat_update(
        current_user.id,
        chat.id,
        {"action": "created", "chat": chat.model_dump()}
    )
    
    return ChatResponse(**chat.model_dump())

@router.get("", response_model=List[ChatResponse])
async def get_user_chats(
    archived: Optional[bool] = Query(None, description="Filter by archived status"),
    pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    limit: int = Query(50, le=100, description="Number of chats to return"),
    offset: int = Query(0, ge=0, description="Number of chats to skip"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get user's chats with optional filtering"""
    
    # Build query
    query = {"user_id": current_user.id}
    
    if archived is not None:
        query["archived"] = archived
    
    if pinned is not None:
        query["pinned"] = pinned
    
    # Execute query with pagination
    cursor = db.chats.find(query).sort("updated_at", -1).skip(offset).limit(limit)
    
    chats = []
    async for chat_doc in cursor:
        chats.append(ChatResponse(**chat_doc))
    
    return chats

@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get specific chat"""
    
    chat_doc = await db.chats.find_one({
        "_id": chat_id,
        "user_id": current_user.id
    })
    
    if not chat_doc:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return ChatResponse(**chat_doc)

@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: str,
    update_data: ChatUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update chat details"""
    
    # Check if chat exists and belongs to user
    chat_doc = await db.chats.find_one({
        "_id": chat_id,
        "user_id": current_user.id
    })
    
    if not chat_doc:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Prepare update data
    update_fields = {
        "updated_at": datetime.utcnow()
    }
    
    if update_data.title is not None:
        update_fields["title"] = update_data.title
    
    if update_data.pinned is not None:
        update_fields["pinned"] = update_data.pinned
    
    if update_data.archived is not None:
        update_fields["archived"] = update_data.archived
    
    if update_data.system_prompt is not None:
        update_fields["system_prompt"] = update_data.system_prompt
    
    # Update chat
    await db.chats.update_one(
        {"_id": chat_id},
        {"$set": update_fields}
    )
    
    # Get updated chat
    updated_chat_doc = await db.chats.find_one({"_id": chat_id})
    updated_chat = ChatResponse(**updated_chat_doc)
    
    # Send update to connected clients
    await ws_manager.send_chat_update(
        current_user.id,
        chat_id,
        {"action": "updated", "chat": updated_chat.model_dump()}
    )
    
    logger.info(f"Chat updated: {chat_id}")
    
    return updated_chat

@router.delete("/{chat_id}", response_model=SuccessResponse)
async def delete_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Delete chat and all its messages"""
    
    # Check if chat exists and belongs to user
    chat_doc = await db.chats.find_one({
        "_id": chat_id,
        "user_id": current_user.id
    })
    
    if not chat_doc:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Delete all messages in the chat
    await db.messages.delete_many({"chat_id": chat_id})
    
    # Delete the chat
    await db.chats.delete_one({"_id": chat_id})
    
    # Send update to connected clients
    await ws_manager.send_chat_update(
        current_user.id,
        chat_id,
        {"action": "deleted", "chat_id": chat_id}
    )
    
    logger.info(f"Chat deleted: {chat_id}")
    
    return SuccessResponse(message="Chat deleted successfully")

@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(
    chat_id: str,
    limit: int = Query(50, le=100, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get messages for a specific chat"""
    
    # Verify chat belongs to user
    chat_doc = await db.chats.find_one({
        "_id": chat_id,
        "user_id": current_user.id
    })
    
    if not chat_doc:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get messages
    cursor = db.messages.find({
        "chat_id": chat_id
    }).sort("created_at", 1).skip(offset).limit(limit)
    
    messages = []
    async for message_doc in cursor:
        messages.append(MessageResponse(**message_doc))
    
    return messages

@router.post("/{chat_id}/messages", response_model=MessageResponse)
@rate_limit_decorator("chat")
async def send_message(
    chat_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Send a message in a chat and get AI response"""
    
    # Verify chat belongs to user
    chat_doc = await db.chats.find_one({
        "_id": chat_id,
        "user_id": current_user.id
    })
    
    if not chat_doc:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat = Chat(**chat_doc)
    
    # Create user message
    user_message = Message(
        chat_id=chat_id,
        user_id=current_user.id,
        type=MessageType.USER,
        content=message_data.content,
        parent_message_id=message_data.parent_message_id
    )
    
    # Insert user message
    result = await db.messages.insert_one(user_message.model_dump())
    user_message.id = str(result.inserted_id)
    
    # Send user message to connected clients
    await ws_manager.send_chat_message(
        current_user.id,
        chat_id,
        {
            "type": "user_message",
            "message": MessageResponse(**user_message.model_dump()).model_dump()
        }
    )
    
    # Get chat history for AI context
    chat_messages = []
    async for msg_doc in db.messages.find({"chat_id": chat_id}).sort("created_at", 1):
        chat_messages.append(Message(**msg_doc))
    
    # Generate AI response
    try:
        # Send typing indicator
        await ws_manager.send_typing_indicator(current_user.id, chat_id, True)
        
        # Generate AI response
        ai_response = await ai_service.generate_response(
            messages=chat_messages,
            model=chat.model,
            system_prompt=chat.system_prompt
        )
        
        # Create AI message
        ai_message = Message(
            chat_id=chat_id,
            user_id=current_user.id,
            type=MessageType.ASSISTANT,
            content=ai_response["content"],
            model=chat.model,
            tokens_used=ai_response.get("tokens_used", 0),
            parent_message_id=user_message.id
        )
        
        # Insert AI message
        result = await db.messages.insert_one(ai_message.model_dump())
        ai_message.id = str(result.inserted_id)
        
        # Update chat
        await db.chats.update_one(
            {"_id": chat_id},
            {
                "$set": {
                    "updated_at": datetime.utcnow(),
                    "last_message_at": datetime.utcnow()
                },
                "$inc": {"message_count": 2}  # User + AI message
            }
        )
        
        # Auto-generate title if this is the first message
        if chat.title == "New Chat" and len(chat_messages) <= 2:
            try:
                new_title = await ai_service.generate_title(message_data.content)
                await db.chats.update_one(
                    {"_id": chat_id},
                    {"$set": {"title": new_title}}
                )
                
                # Send title update
                await ws_manager.send_chat_update(
                    current_user.id,
                    chat_id,
                    {"action": "title_updated", "title": new_title}
                )
            except Exception as e:
                logger.error(f"Error generating title: {e}")
        
        # Send AI message to connected clients
        await ws_manager.send_chat_message(
            current_user.id,
            chat_id,
            {
                "type": "ai_message",
                "message": MessageResponse(**ai_message.model_dump()).model_dump()
            }
        )
        
        # Stop typing indicator
        await ws_manager.send_typing_indicator(current_user.id, chat_id, False)
        
        logger.info(f"Message sent in chat {chat_id}: {len(message_data.content)} chars")
        
        return MessageResponse(**ai_message.model_dump())
        
    except Exception as e:
        # Stop typing indicator on error
        await ws_manager.send_typing_indicator(current_user.id, chat_id, False)
        
        logger.error(f"Error generating AI response: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error generating AI response. Please try again."
        )