"""
Test configuration and fixtures for the Hotel AI Assistant.
"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from backend.models import Base
from backend.models.database import get_db_session
from backend.main import app

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test_hotel_assistant.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup
    if os.path.exists("./test_hotel_assistant.db"):
        os.remove("./test_hotel_assistant.db")


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create a new session for the test
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def override_get_db(test_db):
    """Override the get_db dependency for testing."""
    def _override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db_session] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch('backend.services.conversation_service.openai.OpenAI') as mock:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test response from the AI assistant."
        
        mock_client.chat.completions.create.return_value = mock_response
        mock.return_value = mock_client
        
        yield mock_client


@pytest.fixture
def mock_whisper():
    """Mock Whisper for testing."""
    with patch('backend.services.voice_service.whisper') as mock:
        mock_model = Mock()
        mock_model.transcribe.return_value = {"text": "This is a test transcription"}
        mock.load_model.return_value = mock_model
        
        yield mock_model


@pytest.fixture
def mock_elevenlabs():
    """Mock ElevenLabs for testing."""
    with patch('backend.services.voice_service.generate') as mock:
        mock.return_value = b"fake_audio_data"
        yield mock


@pytest.fixture
def sample_guest_data():
    """Sample guest data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567"
    }


@pytest.fixture
def sample_booking_data():
    """Sample booking data for testing."""
    from datetime import date, timedelta
    
    return {
        "guest_id": 1,
        "room_id": 1,
        "check_in_date": date.today() + timedelta(days=1),
        "check_out_date": date.today() + timedelta(days=3),
        "special_requests": "High floor room preferred"
    }
