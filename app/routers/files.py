from fastapi import APIRouter, UploadFile, File, HTTPException
import aiofiles
import pdfplumber
import os
from app.utils.file_processor import FileProcessor

router = APIRouter(prefix="/api/files", tags=["files"])
file_processor = FileProcessor()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.txt')):
            raise HTTPException(400, "Only PDF and TXT files allowed")
        
        # Process file content
        content = await file_processor.process_file(file)
        
        return {
            "filename": file.filename,
            "content": content[:5000],  # Limit content length
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"File processing error: {str(e)}")