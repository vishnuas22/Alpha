import json
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import structlog
from models import User
from auth import auth_manager
from datetime import datetime

logger = structlog.get_logger()

class ConnectionManager:
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store user info for each connection
        self.connection_users: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Add connection to user's set
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Map connection to user
        self.connection_users[websocket] = user_id
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "user_id": user_id
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        user_id = self.connection_users.get(websocket)
        if user_id:
            # Remove from user's connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove user mapping
            del self.connection_users[websocket]
            
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, data: dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            self.disconnect(websocket)
    
    async def send_to_user(self, user_id: str, data: dict):
        """Send message to all connections for a user"""
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id].copy():
                try:
                    await websocket.send_text(json.dumps(data))
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws)
    
    async def send_chat_message(self, user_id: str, chat_id: str, message_data: dict):
        """Send chat message to user"""
        await self.send_to_user(user_id, {
            "type": "chat_message",
            "chat_id": chat_id,
            "data": message_data
        })
    
    async def send_typing_indicator(self, user_id: str, chat_id: str, is_typing: bool):
        """Send typing indicator"""
        await self.send_to_user(user_id, {
            "type": "typing",
            "chat_id": chat_id,
            "is_typing": is_typing
        })
    
    async def send_chat_update(self, user_id: str, chat_id: str, update_data: dict):
        """Send chat update (title change, etc.)"""
        await self.send_to_user(user_id, {
            "type": "chat_update",
            "chat_id": chat_id,
            "data": update_data
        })
    
    async def send_notification(self, user_id: str, notification: dict):
        """Send notification to user"""
        await self.send_to_user(user_id, {
            "type": "notification",
            "data": notification
        })
    
    async def broadcast_system_message(self, message: str):
        """Broadcast system message to all connected users"""
        data = {
            "type": "system",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for user_id in self.active_connections:
            await self.send_to_user(user_id, data)
    
    def get_connected_users(self) -> List[str]:
        """Get list of connected user IDs"""
        return list(self.active_connections.keys())
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if user has active connections"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

# Global connection manager
manager = ConnectionManager()

class StreamingResponseManager:
    """Manage streaming AI responses over WebSocket"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
    
    async def stream_ai_response(
        self, 
        user_id: str, 
        chat_id: str, 
        message_id: str,
        stream_generator
    ):
        """Stream AI response chunks to user"""
        full_content = ""
        
        try:
            # Send stream start
            await self.manager.send_to_user(user_id, {
                "type": "stream_start",
                "chat_id": chat_id,
                "message_id": message_id
            })
            
            # Stream chunks
            async for chunk in stream_generator:
                chunk_data = {
                    "type": "stream_chunk", 
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "chunk": chunk
                }
                
                await self.manager.send_to_user(user_id, chunk_data)
                
                # Accumulate content
                if chunk.get("content"):
                    full_content += chunk["content"]
            
            # Send stream end
            await self.manager.send_to_user(user_id, {
                "type": "stream_end",
                "chat_id": chat_id, 
                "message_id": message_id,
                "full_content": full_content
            })
            
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            # Send error to user
            await self.manager.send_to_user(user_id, {
                "type": "stream_error",
                "chat_id": chat_id,
                "message_id": message_id,
                "error": str(e)
            })

# Global streaming manager
streaming_manager = StreamingResponseManager(manager)

async def authenticate_websocket(websocket: WebSocket, token: str) -> str:
    """Authenticate WebSocket connection and return user ID"""
    try:
        # Verify JWT token
        payload = auth_manager.verify_token(token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if not user_id or token_type != "access":
            await websocket.close(code=4001, reason="Invalid token")
            return None
        
        return user_id
        
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return None