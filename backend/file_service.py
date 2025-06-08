import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, List
import aiofiles
from PIL import Image
import structlog
from fastapi import UploadFile, HTTPException
from config import settings
from models import FileUpload, FileType
from database import get_database
import uuid
from datetime import datetime, timedelta

logger = structlog.get_logger()

class FileService:
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.upload_dir / "images").mkdir(exist_ok=True)
        (self.upload_dir / "documents").mkdir(exist_ok=True)
        (self.upload_dir / "audio").mkdir(exist_ok=True)
        (self.upload_dir / "video").mkdir(exist_ok=True)
        
        self.allowed_types = settings.allowed_file_types_list
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024  # Convert to bytes
    
    def get_file_type(self, mime_type: str) -> FileType:
        """Determine file type from MIME type"""
        if mime_type.startswith("image/"):
            return FileType.IMAGE
        elif mime_type.startswith("audio/"):
            return FileType.AUDIO
        elif mime_type.startswith("video/"):
            return FileType.VIDEO
        else:
            return FileType.DOCUMENT
    
    def validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check file size
        if hasattr(file, 'size') and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB"
            )
        
        # Check MIME type
        mime_type = file.content_type
        if mime_type not in self.allowed_types:
            raise HTTPException(
                status_code=415,
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_types)}"
            )
    
    async def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def process_image(self, file_path: Path) -> dict:
        """Process image file and extract metadata"""
        try:
            with Image.open(file_path) as img:
                metadata = {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode
                }
                
                # Create thumbnail if image is large
                if img.width > 800 or img.height > 800:
                    thumbnail_path = file_path.parent / f"{file_path.stem}_thumb{file_path.suffix}"
                    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                    img.save(thumbnail_path, optimize=True, quality=85)
                    metadata["thumbnail"] = str(thumbnail_path)
                
                return metadata
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
            return {}
    
    async def upload_file(
        self, 
        file: UploadFile, 
        user_id: str, 
        chat_id: Optional[str] = None
    ) -> FileUpload:
        """Upload and process file"""
        # Validate file
        self.validate_file(file)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Determine file type and subdirectory
        file_type = self.get_file_type(file.content_type)
        subdirs = {
            FileType.IMAGE: "images",
            FileType.DOCUMENT: "documents", 
            FileType.AUDIO: "audio",
            FileType.VIDEO: "video"
        }
        subdir = subdirs[file_type]
        
        # Create file path
        file_path = self.upload_dir / subdir / unique_filename
        
        # Save file
        try:
            async with aiofiles.open(file_path, 'wb') as buffer:
                content = await file.read()
                await buffer.write(content)
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(status_code=500, detail="Error saving file")
        
        # Calculate file hash
        file_hash = await self.calculate_file_hash(file_path)
        
        # Check for duplicates
        db = get_database()
        existing_file = await db.files.find_one({"file_hash": file_hash, "user_id": user_id})
        if existing_file:
            # Remove the newly uploaded file since it's a duplicate
            os.unlink(file_path)
            return FileUpload(**existing_file)
        
        # Process file based on type
        metadata = {}
        if file_type == FileType.IMAGE:
            metadata = await self.process_image(file_path)
        
        # Create file record
        file_record = FileUpload(
            user_id=user_id,
            chat_id=chat_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file_type,
            mime_type=file.content_type,
            file_size=len(content),
            file_hash=file_hash,
            storage_path=str(file_path),
            url=f"/api/files/{unique_filename}",
            metadata=metadata
        )
        
        # Save to database
        await db.files.insert_one(file_record.model_dump())
        
        logger.info(f"File uploaded: {file.filename} -> {unique_filename}")
        return file_record
    
    async def get_file(self, file_id: str, user_id: str) -> Optional[FileUpload]:
        """Get file by ID"""
        db = get_database()
        file_doc = await db.files.find_one({"_id": file_id, "user_id": user_id})
        if file_doc:
            return FileUpload(**file_doc)
        return None
    
    async def get_user_files(
        self, 
        user_id: str, 
        file_type: Optional[FileType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[FileUpload]:
        """Get user's files with pagination"""
        db = get_database()
        
        query = {"user_id": user_id}
        if file_type:
            query["file_type"] = file_type
        
        cursor = db.files.find(query).sort("created_at", -1).skip(offset).limit(limit)
        files = []
        async for file_doc in cursor:
            files.append(FileUpload(**file_doc))
        
        return files
    
    async def delete_file(self, file_id: str, user_id: str) -> bool:
        """Delete file"""
        db = get_database()
        
        # Get file record
        file_doc = await db.files.find_one({"_id": file_id, "user_id": user_id})
        if not file_doc:
            return False
        
        file_record = FileUpload(**file_doc)
        
        # Delete physical file
        try:
            if os.path.exists(file_record.storage_path):
                os.unlink(file_record.storage_path)
            
            # Delete thumbnail if exists
            if "thumbnail" in file_record.metadata:
                thumbnail_path = file_record.metadata["thumbnail"]
                if os.path.exists(thumbnail_path):
                    os.unlink(thumbnail_path)
        except Exception as e:
            logger.error(f"Error deleting physical file: {e}")
        
        # Delete database record
        result = await db.files.delete_one({"_id": file_id, "user_id": user_id})
        
        logger.info(f"File deleted: {file_record.filename}")
        return result.deleted_count > 0
    
    async def cleanup_orphaned_files(self):
        """Cleanup orphaned files that are not referenced in any chat"""
        db = get_database()
        
        # Find files older than 24 hours that are not attached to any message
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        orphaned_files = await db.files.find({
            "created_at": {"$lt": cutoff_time},
            "chat_id": None
        }).to_list(None)
        
        for file_doc in orphaned_files:
            file_record = FileUpload(**file_doc)
            
            # Check if file is referenced in any message
            message_ref = await db.messages.find_one({
                "attachments.id": file_record.id
            })
            
            if not message_ref:
                # Delete orphaned file
                await self.delete_file(file_record.id, file_record.user_id)
                logger.info(f"Cleaned up orphaned file: {file_record.filename}")

# Global file service instance
file_service = FileService()