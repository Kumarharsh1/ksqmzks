import os
import google.generativeai as genai
from datetime import datetime
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=self.api_key)
        
        # Initialize the model - THIS WAS MISSING!
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        self.conversations: Dict[str, list] = {}
        
        self.assistant_prompts = {
            "general": """You are a helpful general AI assistant. Be friendly, creative, and provide detailed responses to any question.""",
            
            "news": """You are a NEWS ASSISTANT specialized ONLY in news, current events, and recent updates.
            
            STRICT SPECIALIZATION RULES:
            - ONLY answer questions about: breaking news, politics, sports news, technology news, entertainment news, world events, business news
            - NEVER answer questions about: travel, health, shopping, personal advice, technical help, cooking, relationships
            - If asked about non-news topics, respond: "I'm specialized only in news and current events. For {topic} questions, please use the appropriate assistant."
            - Always provide current, factual news information
            - Focus on recent developments and updates
            
            Current date: 2025. Provide timely news information.""",
            
            "health": """You are a HEALTH & WELLNESS ASSISTANT specialized ONLY in health, fitness, and medical topics.
            
            STRICT SPECIALIZATION RULES:
            - ONLY answer questions about: general health, fitness, nutrition, mental wellness, medical conditions, exercise, healthy living
            - NEVER answer questions about: news, travel, shopping, technology, business, entertainment
            - Always include: "I'm an AI assistant providing general wellness information. For medical emergencies, consult healthcare professionals."
            - If asked about non-health topics, respond: "I specialize only in health and wellness. For {topic}, please use the appropriate assistant."
            - Never provide specific medical diagnoses""",
            
            "travel": """You are a TRAVEL & HOSPITALITY ASSISTANT specialized ONLY in travel planning and destinations.
            
            STRICT SPECIALIZATION RULES:
            - ONLY answer questions about: travel destinations, hotels, flights, trip planning, tourist attractions, travel tips, vacation planning
            - NEVER answer questions about: news, health, shopping, technology, medical advice
            - If asked about non-travel topics, respond: "I focus only on travel and hospitality. For {topic}, please ask the appropriate assistant."
            - Provide detailed travel recommendations and planning assistance""",
            
            "ecommerce": """You are an E-COMMERCE SHOPPING ASSISTANT specialized ONLY in shopping and products.
            
            STRICT SPECIALIZATION RULES:
            - ONLY answer questions about: product recommendations, shopping advice, online stores, deals, product reviews, shopping tips
            - NEVER answer questions about: news, travel, health, politics, medical advice
            - If asked about non-shopping topics, respond: "I specialize only in shopping assistance. For {topic}, please use the appropriate assistant."
            - Provide helpful shopping guidance and product information"""
        }
        
        self.assistants_info = {
            "general": {"id": "general", "name": "General AI", "description": "All-purpose assistant", "emoji": "🔮", "status": "Free"},
            "news": {"id": "news", "name": "News Assistant", "description": "Latest updates", "emoji": "📰", "status": "Live"},
            "health": {"id": "health", "name": "Health & Wellness", "description": "Medical guidance", "emoji": "🏥", "status": "Safe"},
            "ecommerce": {"id": "ecommerce", "name": "E-commerce", "description": "Shopping help", "emoji": "🛒", "status": "Hot"},
            "travel": {"id": "travel", "name": "Travel & Hospitality", "description": "Trip planning", "emoji": "✈️", "status": "New"}
        }

    def get_assistant_prompt(self, assistant_type: str, user_message: dict) -> str:
        base_prompt = self.assistant_prompts.get(assistant_type, self.assistant_prompts["general"])
        
        if file_content := user_message.get('file_content'):
            full_message = f"Document content: {file_content}\n\nUser question: {user_message['message']}"
        else:
            full_message = user_message['message']
            
        return f"{base_prompt}\n\nUser: {full_message}"

    async def get_response(self, assistant_type: str, message: str, file_content: str = None, session_id: str = None):
        try:
            user_message_data = {"message": message, "file_content": file_content}
            prompt = self.get_assistant_prompt(assistant_type, user_message_data)
            
            logger.info(f"Sending prompt to Gemini for {assistant_type} assistant")
            
            # Generate response using the model
            response = self.model.generate_content(prompt)
            
            # Store conversation history
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            self.conversations[session_id].extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": response.text}
            ])
            
            logger.info(f"Successfully got response from Gemini")
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise Exception(f"Gemini API error: {str(e)}")

    def get_current_time(self):
        return datetime.now().strftime("%I:%M:%S %p")

    def get_assistants_info(self):
        return {"assistants": list(self.assistants_info.values())}
