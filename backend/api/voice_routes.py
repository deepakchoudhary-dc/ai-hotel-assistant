"""
Voice API routes for handling speech-to-text and text-to-speech operations.
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
import uuid

from models.database import get_db_session
from services.voice_service import VoiceService
from services.conversation_service import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter()
voice_service = VoiceService()
conversation_service = ConversationService()


@router.post("/voice")
async def process_voice_message(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    guest_id: Optional[int] = Form(None),
    db: Session = Depends(get_db_session)
):
    """
    Process a voice message end-to-end.
    
    Args:
        audio: Audio file upload
        session_id: Optional session ID
        guest_id: Optional guest ID
        db: Database session
        
    Returns:
        JSON response with transcription, response text, and audio
    """
    try:
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Read audio file
        audio_data = await audio.read()
        
        # Process voice message
        result = await voice_service.process_voice_message(
            audio_file=audio_data,
            conversation_service=conversation_service,
            session_id=session_id,
            db_session=db,
            guest_id=guest_id        )
        
        if "error" in result:
            # Return error response instead of raising exception
            return {
                "transcription": "Voice processing unavailable",
                "response_text": "Voice recognition requires FFmpeg to be installed. Please type your message instead, or install FFmpeg for voice features.",
                "intent": "error",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "has_audio": False
            }
        
        # Handle specific ffmpeg error
        if result.get("transcription") == "FFmpeg required for voice processing":
            return {
                "transcription": "Voice processing unavailable",
                "response_text": "Voice recognition requires FFmpeg to be installed. Please type your message instead, or install FFmpeg for voice features.",
                "intent": "error", 
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "has_audio": False
            }
        
        # Prepare response
        response_data = {
            "transcription": result["transcription"],
            "response_text": result["response_text"],
            "intent": result.get("intent"),
            "session_id": result["session_id"],
            "timestamp": result["timestamp"],
            "has_audio": result["response_audio"] is not None
        }
        
        # If audio response is available, encode it as base64
        if result["response_audio"]:
            import base64
            response_data["response_audio"] = base64.b64encode(result["response_audio"]).decode()
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing voice message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/speech-to-text")
async def speech_to_text(
    audio: UploadFile = File(...)
):
    """
    Convert speech to text.
    
    Args:
        audio: Audio file upload
        
    Returns:
        Transcribed text
    """
    try:
        if not voice_service.is_stt_available():
            raise HTTPException(status_code=503, detail="Speech-to-text service unavailable")
        
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Read audio file
        audio_data = await audio.read()
        
        # Convert to text
        transcription = await voice_service.speech_to_text(audio_data)
        
        if not transcription:
            raise HTTPException(status_code=500, detail="Failed to transcribe audio")
        
        return {"transcription": transcription}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in speech-to-text: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/text-to-speech")
async def text_to_speech(
    text: str = Form(...)
):
    """
    Convert text to speech.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Audio file response
    """
    try:
        if not voice_service.is_tts_available():
            raise HTTPException(status_code=503, detail="Text-to-speech service unavailable")
        
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Convert to speech
        audio_data = await voice_service.text_to_speech(text)
        
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to generate speech")
        
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=response.mp3"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in text-to-speech: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/voice/capabilities")
async def get_voice_capabilities():
    """
    Get available voice capabilities.
    
    Returns:
        Available voice services
    """
    return {
        "speech_to_text": voice_service.is_stt_available(),
        "text_to_speech": voice_service.is_tts_available()
    }
