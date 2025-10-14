from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    file_content: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    assistant_type: str
    response: str
    timestamp: str

class AssistantInfo(BaseModel):
    id: str
    name: str
    description: str
    emoji: str
    status: str