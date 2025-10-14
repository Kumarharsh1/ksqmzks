from fastapi import APIRouter, HTTPException, BackgroundTasks
import google.generativeai as genai # Changed from google.generativeai
import uuid
import logging
from app.models.schemas import ChatRequest, ChatResponse
from app.utils.gemini_client import GeminiClient

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)

gemini_client = GeminiClient()

@router.post("/{assistant_type}")
async def chat_with_assistant(assistant_type: str, request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Build the message with actual file content
        user_message = request.message
        if request.file_content and request.file_content not in ["", "[Image:", "[PDF Document:"]:
            # Only use file_content if it contains actual extracted text
            if not request.file_content.startswith('['):
                user_message = f"Document content: {request.file_content}\n\nUser question: {request.message}"
        
        response = await gemini_client.get_response(
            assistant_type=assistant_type,
            message=user_message,  # Send the actual content, not placeholders
            session_id=session_id
        )
        
        return ChatResponse(
            session_id=session_id,
            assistant_type=assistant_type,
            response=response,
            timestamp=gemini_client.get_current_time()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/assistants")
async def get_assistants():
    return gemini_client.get_assistants_info()