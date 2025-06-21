"""
Database configuration and session management.
"""

import os
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

from models import Base

load_dotenv()

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hotel_assistant.db")

# Create sync engine for development
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def init_db():
    """Initialize database and create tables."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
      # Add some sample data
    from . import Room, RoomType
    
    db = SessionLocal()
    try:
        # Check if rooms already exist
        existing_rooms = db.query(Room).first()
        if not existing_rooms:
            # Add sample rooms
            sample_rooms = [
                Room(
                    room_number="101",
                    room_type=RoomType.STANDARD,
                    price_per_night=120.00,
                    max_occupancy=2,
                    amenities='["WiFi", "TV", "Air Conditioning", "Mini Fridge"]'
                ),
                Room(
                    room_number="102",
                    room_type=RoomType.STANDARD,
                    price_per_night=120.00,
                    max_occupancy=2,
                    amenities='["WiFi", "TV", "Air Conditioning", "Mini Fridge"]'
                ),
                Room(
                    room_number="201",
                    room_type=RoomType.DELUXE,
                    price_per_night=180.00,
                    max_occupancy=3,
                    amenities='["WiFi", "TV", "Air Conditioning", "Mini Fridge", "Balcony", "Safe"]'
                ),
                Room(
                    room_number="301",
                    room_type=RoomType.SUITE,
                    price_per_night=350.00,
                    max_occupancy=4,
                    amenities='["WiFi", "TV", "Air Conditioning", "Mini Fridge", "Balcony", "Safe", "Kitchenette", "Living Area"]'
                ),
                Room(
                    room_number="401",
                    room_type=RoomType.PRESIDENTIAL,
                    price_per_night=750.00,
                    max_occupancy=6,
                    amenities='["WiFi", "TV", "Air Conditioning", "Mini Fridge", "Balcony", "Safe", "Full Kitchen", "Living Area", "Dining Area", "Jacuzzi"]'
                )
            ]
            
            for room in sample_rooms:
                db.add(room)
            
            db.commit()
            print("Sample rooms added to database")
    
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


def get_db_session() -> Session:
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
