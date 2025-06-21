"""
Hotel service for managing hotel operations like rooms, bookings, and guest information.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import (
    Room, Guest, Booking, RoomResponse, GuestResponse, BookingResponse,
    GuestCreate, BookingCreate, RoomType, BookingStatus
)

logger = logging.getLogger(__name__)


class HotelService:
    """Service for handling hotel operations."""
    
    def __init__(self):
        """Initialize the hotel service."""
        pass
    
    def get_available_rooms(
        self, 
        db: Session,
        check_in_date: date,
        check_out_date: date,
        room_type: Optional[RoomType] = None,
        max_occupancy: Optional[int] = None
    ) -> List[RoomResponse]:
        """
        Get available rooms for the specified dates.
        
        Args:
            db: Database session
            check_in_date: Check-in date
            check_out_date: Check-out date
            room_type: Optional room type filter
            max_occupancy: Optional occupancy filter
            
        Returns:
            List of available rooms
        """
        try:
            # Base query for rooms
            query = db.query(Room).filter(Room.is_available == True)
            
            # Apply filters
            if room_type:
                query = query.filter(Room.room_type == room_type)
            
            if max_occupancy:
                query = query.filter(Room.max_occupancy >= max_occupancy)
            
            # Get all potentially available rooms
            rooms = query.all()
            
            # Filter out rooms that are booked during the requested period
            available_rooms = []
            for room in rooms:
                if self._is_room_available(db, room.id, check_in_date, check_out_date):
                    available_rooms.append(room)
            
            return [RoomResponse.from_orm(room) for room in available_rooms]
            
        except Exception as e:
            logger.error(f"Error getting available rooms: {str(e)}")
            return []
    
    def _is_room_available(
        self, 
        db: Session, 
        room_id: int, 
        check_in_date: date, 
        check_out_date: date
    ) -> bool:
        """Check if a room is available for the specified dates."""
        try:
            # Check for overlapping bookings
            overlapping_bookings = db.query(Booking).filter(
                and_(
                    Booking.room_id == room_id,
                    Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
                    or_(
                        and_(
                            Booking.check_in_date <= check_in_date,
                            Booking.check_out_date > check_in_date
                        ),
                        and_(
                            Booking.check_in_date < check_out_date,
                            Booking.check_out_date >= check_out_date
                        ),
                        and_(
                            Booking.check_in_date >= check_in_date,
                            Booking.check_out_date <= check_out_date
                        )
                    )
                )
            ).first()
            
            return overlapping_bookings is None
            
        except Exception as e:
            logger.error(f"Error checking room availability: {str(e)}")
            return False
    
    def create_guest(self, db: Session, guest_data: GuestCreate) -> Optional[GuestResponse]:
        """Create a new guest."""
        try:
            # Check if guest already exists by email
            existing_guest = db.query(Guest).filter(Guest.email == guest_data.email).first()
            if existing_guest:
                return GuestResponse.from_orm(existing_guest)
            
            # Create new guest
            guest = Guest(
                first_name=guest_data.first_name,
                last_name=guest_data.last_name,
                email=guest_data.email,
                phone=guest_data.phone
            )
            
            db.add(guest)
            db.commit()
            db.refresh(guest)
            
            return GuestResponse.from_orm(guest)
            
        except Exception as e:
            logger.error(f"Error creating guest: {str(e)}")
            db.rollback()
            return None
    
    def create_booking(
        self, 
        db: Session, 
        booking_data: BookingCreate
    ) -> Optional[BookingResponse]:
        """Create a new booking."""
        try:
            # Validate dates
            if booking_data.check_in_date >= booking_data.check_out_date:
                logger.error("Check-in date must be before check-out date")
                return None
            
            if booking_data.check_in_date < date.today():
                logger.error("Check-in date cannot be in the past")
                return None
            
            # Check if room is available
            if not self._is_room_available(
                db, 
                booking_data.room_id, 
                booking_data.check_in_date, 
                booking_data.check_out_date
            ):
                logger.error("Room is not available for the selected dates")
                return None
            
            # Get room for pricing
            room = db.query(Room).filter(Room.id == booking_data.room_id).first()
            if not room:
                logger.error("Room not found")
                return None
            
            # Calculate total amount
            nights = (booking_data.check_out_date - booking_data.check_in_date).days
            total_amount = room.price_per_night * nights
            
            # Create booking
            booking = Booking(
                guest_id=booking_data.guest_id,
                room_id=booking_data.room_id,
                check_in_date=booking_data.check_in_date,
                check_out_date=booking_data.check_out_date,
                total_amount=total_amount,
                special_requests=booking_data.special_requests,
                status=BookingStatus.CONFIRMED
            )
            
            db.add(booking)
            db.commit()
            db.refresh(booking)
            
            return BookingResponse.from_orm(booking)
            
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            db.rollback()
            return None
    
    def get_guest_bookings(self, db: Session, guest_id: int) -> List[BookingResponse]:
        """Get all bookings for a guest."""
        try:
            bookings = db.query(Booking).filter(
                Booking.guest_id == guest_id
            ).order_by(Booking.created_at.desc()).all()
            
            return [BookingResponse.from_orm(booking) for booking in bookings]
            
        except Exception as e:
            logger.error(f"Error getting guest bookings: {str(e)}")
            return []
    
    def check_in_guest(self, db: Session, booking_id: int) -> bool:
        """Check in a guest."""
        try:
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return False
            
            if booking.status != BookingStatus.CONFIRMED:
                return False
            
            if booking.check_in_date > date.today():
                return False
            
            booking.status = BookingStatus.CHECKED_IN
            booking.updated_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error checking in guest: {str(e)}")
            db.rollback()
            return False
    
    def check_out_guest(self, db: Session, booking_id: int) -> bool:
        """Check out a guest."""
        try:
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return False
            
            if booking.status != BookingStatus.CHECKED_IN:
                return False
            
            booking.status = BookingStatus.CHECKED_OUT
            booking.updated_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error checking out guest: {str(e)}")
            db.rollback()
            return False
    
    def get_room_types_info(self) -> Dict[str, Any]:
        """Get information about available room types."""
        return {
            "room_types": [
                {
                    "type": "standard",
                    "name": "Standard Room",
                    "base_price": 120.00,
                    "max_occupancy": 2,
                    "amenities": ["WiFi", "TV", "Air Conditioning", "Mini Fridge"]
                },
                {
                    "type": "deluxe",
                    "name": "Deluxe Room",
                    "base_price": 180.00,
                    "max_occupancy": 3,
                    "amenities": ["WiFi", "TV", "Air Conditioning", "Mini Fridge", "Balcony", "Safe"]
                },
                {
                    "type": "suite",
                    "name": "Suite",
                    "base_price": 350.00,
                    "max_occupancy": 4,
                    "amenities": ["WiFi", "TV", "Air Conditioning", "Mini Fridge", "Balcony", "Safe", "Kitchenette", "Living Area"]
                },
                {
                    "type": "presidential",
                    "name": "Presidential Suite",
                    "base_price": 750.00,
                    "max_occupancy": 6,
                    "amenities": ["WiFi", "TV", "Air Conditioning", "Mini Fridge", "Balcony", "Safe", "Full Kitchen", "Living Area", "Dining Area", "Jacuzzi"]
                }
            ]
        }
