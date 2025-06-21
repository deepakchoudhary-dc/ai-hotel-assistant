"""
Chat API routes for handling text-based conversations.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from models import ChatRequest, ChatResponse
from models.database import get_db_session
from services.conversation_service import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter()
conversation_service = ConversationService()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db_session)
) -> ChatResponse:
    """
    Handle text-based chat conversations.
    
    Args:
        request: Chat request containing message and session info
        db: Database session
        
    Returns:
        Chat response with AI-generated reply
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not request.session_id:
            request.session_id = str(uuid.uuid4())
        
        # Process the message through conversation service
        result = await conversation_service.process_message(
            message=request.message,
            session_id=request.session_id,
            db=db,
            guest_id=request.guest_id
        )
        
        return ChatResponse(
            response=result["response"],
            intent=result.get("intent"),
            session_id=result["session_id"],
            timestamp=result["timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db_session)
):
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session ID
        limit: Maximum number of messages to retrieve
        db: Database session
        
    Returns:
        List of conversation messages
    """
    try:
        history = conversation_service.get_conversation_history(
            session_id=session_id,
            db=db,
            limit=limit
        )
        
        return {"history": history}
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
