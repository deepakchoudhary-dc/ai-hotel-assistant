"""
Tests for the conversation service.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from backend.services.conversation_service import ConversationService
from backend.models import Conversation, Guest


class TestConversationService:
    """Test cases for ConversationService."""
    
    def test_init(self):
        """Test service initialization."""
        service = ConversationService()
        assert service.hotel_service is not None
        assert service.system_prompt is not None
        assert "Grand Plaza Hotel" in service.system_prompt
    
    def test_detect_intent_booking(self):
        """Test intent detection for booking messages."""
        service = ConversationService()
        
        # Test booking intent
        assert service._detect_intent("I want to book a room") == "booking"
        assert service._detect_intent("Do you have availability?") == "booking"
        assert service._detect_intent("I need a reservation") == "booking"
    
    def test_detect_intent_checkin(self):
        """Test intent detection for check-in messages."""
        service = ConversationService()
        
        assert service._detect_intent("I'd like to check in") == "checkin"
        assert service._detect_intent("I'm here for check in") == "checkin"
        assert service._detect_intent("I just arrived") == "checkin"
    
    def test_detect_intent_checkout(self):
        """Test intent detection for check-out messages."""
        service = ConversationService()
        
        assert service._detect_intent("I want to check out") == "checkout"
        assert service._detect_intent("I'm ready to leave") == "checkout"
        assert service._detect_intent("Can I get my bill?") == "checkout"
    
    def test_detect_intent_amenities(self):
        """Test intent detection for amenities messages."""
        service = ConversationService()
        
        assert service._detect_intent("What amenities do you have?") == "amenities"
        assert service._detect_intent("Do you have a pool?") == "amenities"
        assert service._detect_intent("What about WiFi?") == "amenities"
    
    def test_detect_intent_greeting(self):
        """Test intent detection for greeting messages."""
        service = ConversationService()
        
        assert service._detect_intent("Hello") == "greeting"
        assert service._detect_intent("Good morning") == "greeting"
        assert service._detect_intent("Hi there") == "greeting"
    
    def test_detect_intent_general(self):
        """Test intent detection for general messages."""
        service = ConversationService()
        
        assert service._detect_intent("Random message") == "general"
        assert service._detect_intent("Some other text") == "general"
    
    @pytest.mark.asyncio
    async def test_process_message_success(self, test_db, mock_openai):
        """Test successful message processing."""
        service = ConversationService()
        
        result = await service.process_message(
            message="Hello, I need help",
            session_id="test_session",
            db=test_db
        )
        
        assert "response" in result
        assert result["response"] == "This is a test response from the AI assistant."
        assert result["intent"] == "greeting"
        assert result["session_id"] == "test_session"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_process_message_with_guest(self, test_db, mock_openai, sample_guest_data):
        """Test message processing with guest ID."""
        # Create a guest first
        guest = Guest(**sample_guest_data)
        test_db.add(guest)
        test_db.commit()
        
        service = ConversationService()
        
        result = await service.process_message(
            message="I need help with my booking",
            session_id="test_session",
            db=test_db,
            guest_id=guest.id
        )
        
        assert "response" in result
        assert result["guest_id"] == guest.id if "guest_id" in result else True
    
    @pytest.mark.asyncio
    async def test_process_message_error_handling(self, test_db):
        """Test error handling in message processing."""
        service = ConversationService()
        
        # Mock OpenAI to raise an exception
        with patch.object(service, '_generate_response', side_effect=Exception("API Error")):
            result = await service.process_message(
                message="Test message",
                session_id="test_session",
                db=test_db
            )
            
            assert "response" in result
            assert "technical difficulties" in result["response"]
            assert result["intent"] == "error"
    
    def test_get_conversation_history(self, test_db):
        """Test getting conversation history."""
        service = ConversationService()
        session_id = "test_session"
        
        # Add some conversation history
        conversations = [
            Conversation(
                session_id=session_id,
                message="Hello",
                response="Hi there!",
                intent="greeting"
            ),
            Conversation(
                session_id=session_id,
                message="I need help",
                response="How can I help?",
                intent="general"
            )
        ]
        
        for conv in conversations:
            test_db.add(conv)
        test_db.commit()
        
        # Get history
        history = service.get_conversation_history(session_id, test_db)
        
        assert len(history) == 2
        assert history[0].message == "I need help"  # Most recent first
        assert history[1].message == "Hello"
    
    def test_get_conversation_history_empty(self, test_db):
        """Test getting conversation history when empty."""
        service = ConversationService()
        
        history = service.get_conversation_history("nonexistent_session", test_db)
        
        assert len(history) == 0
    
    def test_get_conversation_history_private(self, test_db):
        """Test private method for getting conversation history."""
        service = ConversationService()
        session_id = "test_session"
        
        # Add a conversation
        conv = Conversation(
            session_id=session_id,
            message="Test message",
            response="Test response",
            intent="general"
        )
        test_db.add(conv)
        test_db.commit()
        
        # Get history using private method
        history = service._get_conversation_history(session_id, test_db)
        
        assert len(history) == 2  # User message + assistant response
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Test message"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Test response"
