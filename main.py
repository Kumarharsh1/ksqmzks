import os
import uuid
import logging
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import pdfplumber

from routes import test
from services.chat_manager import ChatManager
from utils.prompts import ASSISTANT_PROMPTS

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App
app = FastAPI(title="Multi-AI ChatBot", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    logger.warning("GEMINI_API_KEY not set. Gemini features will be disabled.")
    model = None

# Chat manager
chat_manager = ChatManager()

# Include modular routes
app.include_router(test.router)

@app.get("/")
async def root():
    return {"message": "Multi-AI ChatBot API", "status": "online"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}

@app.post("/api/chat/{assistant_type}")
async def chat_with_assistant(assistant_type: str, message: dict):
    if model is None:
        raise HTTPException(status_code=503, detail="Gemini model not available. API key missing.")

    try:
        session_id = message.get("session_id", str(uuid.uuid4()))
        user_message = message.get("message", "")
        file_content = message.get("file_content", "")

        if assistant_type not in ASSISTANT_PROMPTS:
            raise HTTPException(status_code=400, detail="Invalid assistant type")

        full_message = f"Document content: {file_content}\n\nUser question: {user_message}" if file_content else user_message
        prompt = f"{ASSISTANT_PROMPTS[assistant_type]}\n\nUser: {full_message}"

        logger.info(f"Generating response for {assistant_type} assistant")
        response = model.generate_content(prompt)

        return {
            "session_id": session_id,
            "assistant_type": assistant_type,
            "response": response.text,
            "timestamp": datetime.utcnow().isoformat()
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
            try:
                text_content = contents.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(400, "File encoding not supported")

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