"""
Conversation service for handling AI-powered hotel conversations.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from models import Conversation, Guest, ConversationCreate, ConversationResponse
from services.hotel_service import HotelService

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for handling AI conversations with hotel guests."""
    
    def __init__(self):
        """Initialize the conversation service."""
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "qwen3:1.7b"  # Using your available model
        self.hotel_service = HotelService()
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt for the AI assistant."""
        hotel_name = os.getenv("HOTEL_NAME", "Grand Plaza Hotel")
        hotel_address = os.getenv("HOTEL_ADDRESS", "123 Main Street, City, State")
        hotel_phone = os.getenv("HOTEL_PHONE", "+1-555-123-4567")
        wifi_password = os.getenv("WIFI_PASSWORD", "GrandPlaza2024")
        
        return f"""You are a professional and friendly AI front desk assistant at {hotel_name}.

Hotel Information:
- Name: {hotel_name}
- Address: {hotel_address}
- Phone: {hotel_phone}
- WiFi Password: {wifi_password}

Your responsibilities include:
1. Greeting guests warmly and professionally
2. Helping with room bookings and availability checks
3. Assisting with check-in and check-out procedures
4. Providing information about hotel amenities and services
5. Answering common questions about the hotel
6. Helping with local recommendations and directions
7. Handling guest requests and complaints

Hotel Amenities:
- 24/7 front desk service
- Complimentary WiFi throughout the hotel
- Fitness center (open 5 AM - 11 PM)
- Swimming pool (open 6 AM - 10 PM)
- Restaurant "The Plaza Grill" (breakfast 6-10 AM, lunch 11 AM-3 PM, dinner 5-10 PM)
- Room service (available 24/7)
- Business center
- Concierge services
- Valet parking ($25/night)
- Pet-friendly (additional $50/night pet fee)

Room Types Available:
- Standard Room: $120/night (2 guests max)
- Deluxe Room: $180/night (3 guests max)
- Suite: $350/night (4 guests max)
- Presidential Suite: $750/night (6 guests max)

Check-in: 3:00 PM
Check-out: 11:00 AM
Late check-out available until 2:00 PM ($50 fee)

Important Guidelines:
- Always be polite, professional, and helpful
- If you cannot handle a request, offer to connect them with a human staff member
- For booking requests, gather: dates, number of guests, room preference, special requests
- For complaints, apologize sincerely and offer solutions
- Provide specific times, prices, and details when available
- Ask clarifying questions when needed
- Keep responses concise but complete

Current date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

    async def process_message(
        self, 
        message: str, 
        session_id: str, 
        db: Session,
        guest_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process a conversation message and generate AI response.
        
        Args:
            message: User's message
            session_id: Conversation session ID
            db: Database session
            guest_id: Optional guest ID
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Get conversation history for context
            conversation_history = self._get_conversation_history(session_id, db)
            
            # Detect intent from the message
            intent = self._detect_intent(message)
            
            # Generate AI response
            ai_response = await self._generate_response(
                message, 
                conversation_history,
                intent
            )
            
            # Save conversation to database
            conversation = Conversation(
                guest_id=guest_id,
                session_id=session_id,
                message=message,
                response=ai_response,
                intent=intent,
                is_voice=False
            )
            
            db.add(conversation)
            db.commit()
            
            return {
                "response": ai_response,
                "intent": intent,
                "session_id": session_id,
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please speak with our front desk staff for immediate assistance.",
                "intent": "error",
                "session_id": session_id,
                "timestamp": datetime.utcnow()
            }
    
    def _get_conversation_history(self, session_id: str, db: Session) -> List[Dict[str, str]]:
        """Get recent conversation history for context."""
        try:
            conversations = db.query(Conversation).filter(
                Conversation.session_id == session_id
            ).order_by(Conversation.created_at.desc()).limit(10).all()
            
            history = []
            for conv in reversed(conversations):
                history.extend([
                    {"role": "user", "content": conv.message},
                    {"role": "assistant", "content": conv.response}
                ])
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    def _detect_intent(self, message: str) -> str:
        """Detect the intent of the user's message."""
        message_lower = message.lower()
        
        # Define intent keywords
        intent_keywords = {
            "booking": ["book", "reserve", "reservation", "room", "availability", "stay"],
            "checkin": ["check in", "checking in", "arrival", "arrived"],
            "checkout": ["check out", "checking out", "departure", "leaving", "bill"],
            "amenities": ["pool", "gym", "restaurant", "wifi", "parking", "room service"],
            "directions": ["where", "how to get", "location", "address", "directions"],
            "complaint": ["problem", "issue", "complain", "not working", "broken", "dirty"],
            "info": ["hours", "time", "when", "what time", "schedule"],
            "greeting": ["hello", "hi", "good morning", "good afternoon", "good evening"]
        }
        
        for intent, keywords in intent_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        return "general"
    
    async def _generate_response(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        intent: str
    ) -> str:
        """Generate AI response using local Ollama model."""
        try:
            # Build the prompt with system context and conversation history
            prompt = f"{self.system_prompt}\n\n"
            
            # Add conversation history
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                if msg["role"] == "user":
                    prompt += f"Guest: {msg['content']}\n"
                else:
                    prompt += f"Assistant: {msg['content']}\n"
            
            prompt += f"Guest: {message}\nAssistant:"
            
            # Call Ollama API
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=30            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()
                
                # Filter out thinking process from the response
                clean_response = self._filter_thinking_process(ai_response)
                
                # If response is too short or empty, use fallback
                if len(clean_response) < 10:
                    return self._get_fallback_response(message, intent)
                
                return clean_response
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return self._get_fallback_response(message, intent)
            
        except Exception as e:
            logger.error(f"Error generating AI response with Ollama: {str(e)}")
            return self._get_fallback_response(message, intent)
    
    def _filter_thinking_process(self, response: str) -> str:
        """
        Filter out thinking process from AI response.
        Removes content between <think> and </think> tags.
        """
        import re
        
        # Remove thinking process tags and their content
        # This regex matches <think>...</think> (including multiline)
        cleaned_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # Also handle alternative thinking formats
        cleaned_response = re.sub(r'<thinking>.*?</thinking>', '', cleaned_response, flags=re.DOTALL)
        
        # Clean up extra whitespace
        cleaned_response = re.sub(r'\n\s*\n', '\n', cleaned_response.strip())
        
        return cleaned_response.strip()
    
    def _get_fallback_response(self, message: str, intent: str) -> str:
        """Generate fallback responses based on intent when OpenAI is not available."""
        message_lower = message.lower()
        
        if intent == "greeting":
            return "Hello! Welcome to Grand Plaza Hotel. I'm your AI assistant. How may I help you today?"
        
        elif intent == "checkin":
            return "I'd be happy to help you check in! Our check-in time is 3:00 PM. May I have your reservation confirmation number or the name the reservation is under?"
        
        elif intent == "checkout":
            return "I can assist you with check-out. Our standard check-out time is 11:00 AM. Late check-out is available until 2:00 PM for an additional $50 fee. Would you like me to process your check-out or extend your stay?"
        
        elif intent == "booking":
            return "I'd be happy to help you with a room reservation! Could you please tell me your preferred dates, number of guests, and room type preference? We have Standard rooms ($120/night), Deluxe rooms ($180/night), Suites ($350/night), and Presidential Suites ($750/night)."
        
        elif intent == "amenities":
            if "pool" in message_lower:
                return "Our swimming pool is open daily from 6:00 AM to 10:00 PM. It's located on the 3rd floor with a beautiful city view!"
            elif "gym" in message_lower or "fitness" in message_lower:
                return "Our fitness center is open 24/7 and features modern equipment including cardio machines, free weights, and strength training equipment."
            elif "wifi" in message_lower:
                return "We offer complimentary WiFi throughout the hotel. The network name is 'GrandPlaza-Guest' and the password is 'GrandPlaza2024'."
            elif "restaurant" in message_lower:
                return "Our restaurant 'The Plaza Grill' serves breakfast (6-10 AM), lunch (11 AM-3 PM), and dinner (5-10 PM). We also offer 24/7 room service!"
            elif "parking" in message_lower:
                return "We offer valet parking for $25 per night. Our parking garage is secure and climate-controlled."
            else:
                return "We offer many amenities including a pool (6 AM-10 PM), 24/7 fitness center, restaurant, complimentary WiFi, room service, business center, concierge services, and valet parking. What specific amenity would you like to know about?"
        
        elif intent == "info":
            if "hour" in message_lower or "time" in message_lower:
                return "Here are our key hours: Check-in: 3:00 PM, Check-out: 11:00 AM, Pool: 6 AM-10 PM, Fitness Center: 24/7, Restaurant: Breakfast 6-10 AM, Lunch 11 AM-3 PM, Dinner 5-10 PM. What specific hours did you need?"
            else:
                return "I'm here to provide information about our hotel services, amenities, and policies. What would you like to know about?"
        
        elif intent == "complaint":
            return "I sincerely apologize for any inconvenience you're experiencing. I want to make sure we resolve this immediately. Could you please provide more details about the issue? I'll also notify our management team right away."
        
        elif intent == "directions":
            return "Grand Plaza Hotel is located at 123 Main Street, City, State 12345. We're in the heart of downtown, within walking distance of major attractions. Would you like specific directions from a particular location?"
        
        else:
            return f"Thank you for contacting Grand Plaza Hotel! I'm here to help with reservations, check-in/check-out, amenities information, and general inquiries. How may I assist you today? If you need immediate assistance, please feel free to call our front desk at +1-555-123-4567."
    
    def get_conversation_history(
        self, 
        session_id: str, 
        db: Session,
        limit: int = 50
    ) -> List[ConversationResponse]:
        """Get conversation history for a session."""
        try:
            conversations = db.query(Conversation).filter(
                Conversation.session_id == session_id
            ).order_by(Conversation.created_at.desc()).limit(limit).all()
            
            return [ConversationResponse.from_orm(conv) for conv in conversations]
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
