from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import structlog
from websocket_manager import manager, authenticate_websocket, streaming_manager
from ai_service import ai_service
from models import Message, ModelName
from database import get_database
import json
import uuid

logger = structlog.get_logger()

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token")
):
    """WebSocket endpoint for real-time communication"""
    
    # Authenticate user
    user_id = await authenticate_websocket(websocket, token)
    if not user_id:
        return
    
    # Connect user
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            message_type = message.get("type")
            
            if message_type == "ping":
                # Respond to ping
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": message.get("timestamp")},
                    websocket
                )
            
            elif message_type == "typing":
                # Handle typing indicators
                chat_id = message.get("chat_id")
                is_typing = message.get("is_typing", False)
                
                # Broadcast typing status to other clients of the same user
                await manager.send_typing_indicator(user_id, chat_id, is_typing)
            
            elif message_type == "stream_request":
                # Handle streaming AI response request
                await handle_stream_request(websocket, user_id, message)
            
            else:
                logger.warning(f"Unknown WebSocket message type: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        manager.disconnect(websocket)

async def handle_stream_request(websocket: WebSocket, user_id: str, message: dict):
    """Handle streaming AI response request"""
    try:
        chat_id = message.get("chat_id")
        prompt = message.get("prompt")
        model_name = message.get("model", "alpha-origin")
        
        if not chat_id or not prompt:
            await manager.send_personal_message(
                {"type": "error", "message": "Missing chat_id or prompt"},
                websocket
            )
            return
        
        # Verify user owns the chat
        db = get_database()
        chat_doc = await db.chats.find_one({
            "_id": chat_id,
            "user_id": user_id
        })
        
        if not chat_doc:
            await manager.send_personal_message(
                {"type": "error", "message": "Chat not found"},
                websocket
            )
            return
        
        # Get chat history
        chat_messages = []
        async for msg_doc in db.messages.find({"chat_id": chat_id}).sort("created_at", 1):
            chat_messages.append(Message(**msg_doc))
        
        # Add the new user message to context
        user_message = Message(
            chat_id=chat_id,
            user_id=user_id,
            type="user",
            content=prompt
        )
        chat_messages.append(user_message)
        
        # Generate message ID for streaming
        message_id = str(uuid.uuid4())
        
        # Start streaming response
        model = ModelName(model_name) if model_name in ModelName.__members__.values() else ModelName.ALPHA_ORIGIN
        
        stream_generator = ai_service.generate_stream_response(
            messages=chat_messages,
            model=model,
            system_prompt=chat_doc.get("system_prompt")
        )
        
        # Stream the response
        await streaming_manager.stream_ai_response(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            stream_generator=stream_generator
        )
        
    except Exception as e:
        logger.error(f"Error handling stream request: {e}")
        await manager.send_personal_message(
            {"type": "error", "message": str(e)},
            websocket
        )