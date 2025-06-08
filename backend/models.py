from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid

# Enums
class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class UserRole(str, Enum):
    USER = "user"
    PLUS = "plus"
    PRO = "pro"
    ADMIN = "admin"

class FileType(str, Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"

class ModelName(str, Enum):
    ALPHA_ORIGIN = "alpha-origin"
    ALPHA_PRIME = "alpha-prime"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"

# Base Models
class BaseDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# User Models
class User(BaseDocument):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    hashed_password: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    usage_stats: Dict[str, Any] = Field(default_factory=dict)

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = None

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

# Authentication Models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Chat Models
class Chat(BaseDocument):
    user_id: str
    title: str = "New Chat"
    model: ModelName = ModelName.ALPHA_ORIGIN
    system_prompt: Optional[str] = None
    pinned: bool = False
    archived: bool = False
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"
    model: Optional[ModelName] = ModelName.ALPHA_ORIGIN
    system_prompt: Optional[str] = None

class ChatUpdate(BaseModel):
    title: Optional[str] = None
    pinned: Optional[bool] = None
    archived: Optional[bool] = None
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    id: str
    title: str
    model: ModelName
    pinned: bool
    archived: bool
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None

# Message Models
class MessageAttachment(BaseModel):
    id: str
    filename: str
    file_type: FileType
    file_size: int
    url: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Message(BaseDocument):
    chat_id: str
    user_id: str
    type: MessageType
    content: str
    model: Optional[ModelName] = None
    attachments: List[MessageAttachment] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parent_message_id: Optional[str] = None
    edited: bool = False
    edit_history: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None

class MessageCreate(BaseModel):
    content: str
    attachments: List[str] = Field(default_factory=list)  # File IDs
    parent_message_id: Optional[str] = None

class MessageUpdate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: str
    type: MessageType
    content: str
    model: Optional[ModelName] = None
    attachments: List[MessageAttachment] = Field(default_factory=list)
    created_at: datetime
    edited: bool = False
    tokens_used: Optional[int] = None

# File Models
class FileUpload(BaseDocument):
    user_id: str
    chat_id: Optional[str] = None
    filename: str
    original_filename: str
    file_type: FileType
    mime_type: str
    file_size: int
    file_hash: str
    storage_path: str
    url: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processed: bool = False

class FileResponse(BaseModel):
    id: str
    filename: str
    file_type: FileType
    file_size: int
    url: str
    created_at: datetime

# Tool Models
class Tool(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)

class ToolResponse(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool

# Settings Models
class UserSettings(BaseModel):
    theme: str = "dark"
    language: str = "en"
    notifications: Dict[str, bool] = Field(default_factory=lambda: {
        "email_notifications": True,
        "push_notifications": True,
        "marketing_emails": False
    })
    privacy: Dict[str, bool] = Field(default_factory=lambda: {
        "data_retention": True,
        "analytics": True,
        "improve_model": False
    })
    ai_settings: Dict[str, Any] = Field(default_factory=lambda: {
        "default_model": "alpha-origin",
        "temperature": 0.7,
        "max_tokens": 2048,
        "system_prompt": ""
    })

# API Response Models
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

# Streaming Models
class StreamingMessage(BaseModel):
    type: str  # "start", "chunk", "end", "error"
    content: Optional[str] = None
    message_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Search Models
class SearchRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None
    limit: int = Field(default=20, le=100)
    offset: int = Field(default=0, ge=0)

class SearchResponse(BaseModel):
    results: List[MessageResponse]
    total: int
    query: str

# Analytics Models
class UsageStats(BaseModel):
    total_messages: int
    total_tokens: int
    total_chats: int
    avg_response_time: float
    model_usage: Dict[str, int]
    daily_usage: List[Dict[str, Any]]

# Webhook Models
class WebhookEvent(BaseModel):
    event_type: str
    timestamp: datetime
    user_id: str
    data: Dict[str, Any]

# Rate Limiting Models
class RateLimit(BaseModel):
    key: str
    count: int
    window: str
    expires_at: datetime

# Export Models
class ExportRequest(BaseModel):
    format: str = Field(..., pattern="^(json|csv|markdown|pdf)$")
    chat_ids: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class ExportResponse(BaseModel):
    download_url: str
    expires_at: datetime
    file_size: int