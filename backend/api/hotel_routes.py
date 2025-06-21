"""
Hotel API routes for managing rooms, bookings, and guest information.
"""

import logging
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models import (
    RoomResponse, GuestResponse, BookingResponse,
    GuestCreate, BookingCreate, RoomType
)
from models.database import get_db_session
from services.hotel_service import HotelService

logger = logging.getLogger(__name__)
router = APIRouter()
hotel_service = HotelService()


@router.get("/rooms", response_model=List[RoomResponse])
async def get_available_rooms(
    check_in_date: date = Query(..., description="Check-in date"),
    check_out_date: date = Query(..., description="Check-out date"),
    room_type: Optional[RoomType] = Query(None, description="Room type filter"),
    max_occupancy: Optional[int] = Query(None, description="Maximum occupancy"),
    db: Session = Depends(get_db_session)
):
    """
    Get available rooms for specified dates.
    
    Args:
        check_in_date: Check-in date
        check_out_date: Check-out date
        room_type: Optional room type filter
        max_occupancy: Optional occupancy filter
        db: Database session
        
    Returns:
        List of available rooms
    """
    try:
        if check_in_date >= check_out_date:
            raise HTTPException(status_code=400, detail="Check-in date must be before check-out date")
        
        if check_in_date < date.today():
            raise HTTPException(status_code=400, detail="Check-in date cannot be in the past")
        
        rooms = hotel_service.get_available_rooms(
            db=db,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            room_type=room_type,
            max_occupancy=max_occupancy
        )
        
        return rooms
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available rooms: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/room-types")
async def get_room_types():
    """
    Get information about available room types.
    
    Returns:
        Room types and their details
    """
    try:
        return hotel_service.get_room_types_info()
        
    except Exception as e:
        logger.error(f"Error getting room types: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/guest", response_model=GuestResponse)
async def create_guest(
    guest_data: GuestCreate,
    db: Session = Depends(get_db_session)
):
    """
    Create a new guest.
    
    Args:
        guest_data: Guest information
        db: Database session
        
    Returns:
        Created guest information
    """
    try:
        guest = hotel_service.create_guest(db=db, guest_data=guest_data)
        
        if not guest:
            raise HTTPException(status_code=400, detail="Failed to create guest")
        
        return guest
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating guest: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/booking", response_model=BookingResponse)
async def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db_session)
):
    """
    Create a new booking.
    
    Args:
        booking_data: Booking information
        db: Database session
        
    Returns:
        Created booking information
    """
    try:
        booking = hotel_service.create_booking(db=db, booking_data=booking_data)
        
        if not booking:
            raise HTTPException(status_code=400, detail="Failed to create booking")
        
        return booking
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/guest/{guest_id}/bookings", response_model=List[BookingResponse])
async def get_guest_bookings(
    guest_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Get all bookings for a specific guest.
    
    Args:
        guest_id: Guest ID
        db: Database session
        
    Returns:
        List of guest bookings
    """
    try:
        bookings = hotel_service.get_guest_bookings(db=db, guest_id=guest_id)
        return bookings
        
    except Exception as e:
        logger.error(f"Error getting guest bookings: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/booking/{booking_id}/checkin")
async def check_in_guest(
    booking_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Check in a guest.
    
    Args:
        booking_id: Booking ID
        db: Database session
        
    Returns:
        Success message
    """
    try:
        success = hotel_service.check_in_guest(db=db, booking_id=booking_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to check in guest")
        
        return {"message": "Guest checked in successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking in guest: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/booking/{booking_id}/checkout")
async def check_out_guest(
    booking_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Check out a guest.
    
    Args:
        booking_id: Booking ID
        db: Database session
        
    Returns:
        Success message
    """
    try:
        success = hotel_service.check_out_guest(db=db, booking_id=booking_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to check out guest")
        
        return {"message": "Guest checked out successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking out guest: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
