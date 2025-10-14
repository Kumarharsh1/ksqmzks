import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import pdfplumber
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-AI ChatBot", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model - THIS IS CRITICAL!
model = genai.GenerativeModel('gemini-2.5-flash')

# Assistant Prompts
ASSISTANT_PROMPTS = {
    "general": "You are a helpful general AI assistant. Be friendly and creative in your responses.",
    "news": """You are a News Assistant. ONLY answer questions about current news, latest updates, and recent events. 
    If asked about other topics like travel, health, or shopping, politely decline and suggest using the appropriate specialist assistant.
    Current date: 2025. Provide accurate, timely news information.""",
    "health": """You are a Health & Wellness assistant. ONLY provide general health information, wellness tips, and medical guidance.
    Always include a disclaimer: 'I am an AI assistant. For medical emergencies, consult healthcare professionals.'
    Redirect other topics to the appropriate assistants.""",
    "travel": """You are a Travel & Hospitality assistant. ONLY help with trip planning, destinations, hotels, and travel tips.
    For news, health, or shopping questions, politely redirect to the proper assistants.""",
    "ecommerce": """You are an E-commerce Shopping assistant. ONLY help with product recommendations, shopping advice, and online purchases.
    Redirect other queries to the appropriate specialist assistants."""
}

class ChatManager:
    def __init__(self):
        self.conversations: Dict[str, List] = {}
    
chat_manager = ChatManager()

@app.get("/")
async def root():
    return {"message": "Multi-AI ChatBot API", "status": "online"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}

@app.post("/api/chat/{assistant_type}")
async def chat_with_assistant(assistant_type: str, message: dict):
    try:
        session_id = message.get("session_id", str(uuid.uuid4()))
        user_message = message.get("message", "")
        file_content = message.get("file_content", "")
        
        if assistant_type not in ASSISTANT_PROMPTS:
            raise HTTPException(status_code=400, detail="Invalid assistant type")
        
        # Build conversation context
        full_message = user_message
        if file_content:
            full_message = f"Document content: {file_content}\n\nUser question: {user_message}"
        
        # Get response from Gemini
        prompt = f"{ASSISTANT_PROMPTS[assistant_type]}\n\nUser: {full_message}"
        
        logger.info(f"Generating response for {assistant_type} assistant")
        response = model.generate_content(prompt)
        
        return {
            "session_id": session_id,
            "assistant_type": assistant_type,
            "response": response.text,
            "timestamp": "now"
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(400, "Only PDF and TXT files allowed")
        
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(400, "File too large")
        
        text_content = ""
        if file.filename.endswith('.pdf'):
            with pdfplumber.open(file.file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content += text + "\n"
        else:
            text_content = contents.decode('utf-8')
        
        return {"filename": file.filename, "content": text_content[:5000]}
        
    except Exception as e:
        raise HTTPException(500, f"File error: {str(e)}")

@app.get("/api/assistants")
async def get_assistants():
    return {
        "assistants": [
            {"id": "general", "name": "General AI", "description": "All-purpose assistant", "emoji": "🔮", "status": "Free"},
            {"id": "news", "name": "News Assistant", "description": "Latest updates", "emoji": "📰", "status": "Live"},
            {"id": "health", "name": "Health & Wellness", "description": "Medical guidance", "emoji": "🏥", "status": "Safe"},
            {"id": "ecommerce", "name": "E-commerce", "description": "Shopping help", "emoji": "🛒", "status": "Hot"},
            {"id": "travel", "name": "Travel & Hospitality", "description": "Trip planning", "emoji": "✈️", "status": "New"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7999)
