from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from fastapi.responses import FileResponse
from typing import List, Optional
import structlog
from models import User, FileResponse as FileResponseModel, FileType, SuccessResponse
from auth import get_current_user
from file_service import file_service
from rate_limiter import rate_limit_decorator
import mimetypes
import os

logger = structlog.get_logger()

router = APIRouter(prefix="/files", tags=["Files"])

@router.post("/upload", response_model=FileResponseModel)
@rate_limit_decorator("file_upload")
async def upload_file(
    file: UploadFile = File(...),
    chat_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Upload a file"""
    
    try:
        uploaded_file = await file_service.upload_file(
            file=file,
            user_id=current_user.id,
            chat_id=chat_id
        )
        
        return FileResponseModel(
            id=uploaded_file.id,
            filename=uploaded_file.filename,
            file_type=uploaded_file.file_type,
            file_size=uploaded_file.file_size,
            url=uploaded_file.url,
            created_at=uploaded_file.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

@router.get("/", response_model=List[FileResponseModel])
async def get_user_files(
    file_type: Optional[FileType] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get user's uploaded files"""
    
    files = await file_service.get_user_files(
        user_id=current_user.id,
        file_type=file_type,
        limit=limit,
        offset=offset
    )
    
    return [
        FileResponseModel(
            id=f.id,
            filename=f.filename,
            file_type=f.file_type,
            file_size=f.file_size,
            url=f.url,
            created_at=f.created_at
        )
        for f in files
    ]

@router.get("/{file_id}", response_model=FileResponseModel)
async def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get file information"""
    
    file_record = await file_service.get_file(file_id, current_user.id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponseModel(
        id=file_record.id,
        filename=file_record.filename,
        file_type=file_record.file_type,
        file_size=file_record.file_size,
        url=file_record.url,
        created_at=file_record.created_at
    )

@router.get("/{filename}/download")
async def download_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download a file"""
    
    # Find file by filename (this is a simplified approach)
    # In production, you might want to use file IDs for security
    files = await file_service.get_user_files(current_user.id, limit=1000)
    file_record = None
    
    for f in files:
        if f.filename == filename:
            file_record = f
            break
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file_record.storage_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(file_record.storage_path)
    if not content_type:
        content_type = "application/octet-stream"
    
    return FileResponse(
        path=file_record.storage_path,
        filename=file_record.original_filename,
        media_type=content_type
    )

@router.delete("/{file_id}", response_model=SuccessResponse)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a file"""
    
    success = await file_service.delete_file(file_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    return SuccessResponse(message="File deleted successfully")