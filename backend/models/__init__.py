"""
Database models for the Hotel AI Front Desk Assistant.
"""

from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from pydantic import BaseModel
import os

Base = declarative_base()


class RoomType(str, Enum):
    """Room type enumeration."""
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"
    PRESIDENTIAL = "presidential"


class BookingStatus(str, Enum):
    """Booking status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


# SQLAlchemy Models
class Guest(Base):
    """Guest database model."""
    __tablename__ = "guests"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = relationship("Booking", back_populates="guest")
    conversations = relationship("Conversation", back_populates="guest")


class Room(Base):
    """Room database model."""
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(10), unique=True, nullable=False, index=True)
    room_type = Column(String(20), nullable=False)
    price_per_night = Column(Float, nullable=False)
    max_occupancy = Column(Integer, default=2)
    amenities = Column(Text)  # JSON string of amenities
    is_available = Column(Boolean, default=True)
    
    # Relationships
    bookings = relationship("Booking", back_populates="room")


class Booking(Base):
    """Booking database model."""
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    status = Column(String(20), default=BookingStatus.PENDING)
    total_amount = Column(Float)
    special_requests = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    guest = relationship("Guest", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")


class Conversation(Base):
    """Conversation history database model."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=True)
    session_id = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    intent = Column(String(50))  # e.g., "booking", "checkin", "info"
    is_voice = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    guest = relationship("Guest", back_populates="conversations")


# Pydantic Models for API
class GuestBase(BaseModel):
    """Base guest model for API requests."""
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None


class GuestCreate(GuestBase):
    """Guest creation model."""
    pass


class GuestResponse(GuestBase):
    """Guest response model."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoomBase(BaseModel):
    """Base room model for API requests."""
    room_number: str
    room_type: RoomType
    price_per_night: float
    max_occupancy: int = 2
    amenities: Optional[str] = None


class RoomResponse(RoomBase):
    """Room response model."""
    id: int
    is_available: bool
    
    class Config:
        from_attributes = True


class BookingBase(BaseModel):
    """Base booking model for API requests."""
    check_in_date: date
    check_out_date: date
    special_requests: Optional[str] = None


class BookingCreate(BookingBase):
    """Booking creation model."""
    guest_id: int
    room_id: int


class BookingResponse(BookingBase):
    """Booking response model."""
    id: int
    guest_id: int
    room_id: int
    status: BookingStatus
    total_amount: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Conversation creation model."""
    guest_id: Optional[int] = None
    session_id: str
    message: str
    is_voice: bool = False


class ConversationResponse(BaseModel):
    """Conversation response model."""
    id: int
    session_id: str
    message: str
    response: str
    intent: Optional[str]
    is_voice: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: str
    guest_id: Optional[int] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    intent: Optional[str] = None
    session_id: str
    timestamp: datetime
