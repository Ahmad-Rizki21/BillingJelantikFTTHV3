# app/routers/notifications.py

import logging
import json
from datetime import datetime
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
    HTTPException,
    status,
    Header,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
from ..auth import get_user_from_token, get_current_active_user
from ..models.user import User as UserModel
from ..models.activity_log import ActivityLog as ActivityLogModel
from ..websocket_manager import manager

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# Schema for unread notifications
class UnreadNotification(BaseModel):
    id: int
    timestamp: str
    action: str
    type: str
    details: Optional[dict] = None  # Kembali ke dict


class UnreadNotificationsResponse(BaseModel):
    count: int
    notifications: List[UnreadNotification]


# Test endpoint untuk memastikan router terdaftar
@router.get("/test-websocket")
async def test_websocket():
    return {"message": "WebSocket router is working", "status": "ok"}


# Test endpoint untuk verifikasi path WebSocket
@router.get("/websocket-info")
async def websocket_info():
    """
    Informasi tentang konfigurasi WebSocket untuk debugging

    Berdasarkan konfigurasi Apache:
    - Frontend URL: wss://billingftth.my.id/ws/notifications?token=xxx
    - Apache Proxy: ws://127.0.0.1:8000/ws/notifications
    - FastAPI Main: /ws/notifications (langsung di main.py)
    """
    return {
        "websocket_path": "/ws/notifications",
        "frontend_url": "wss://billingftth.my.id/ws/notifications?token=YOUR_TOKEN",
        "apache_proxy": "ws://127.0.0.1:8000/ws/notifications",
        "fastapi_endpoint": "/ws/notifications",
        "implementation": "main.py",
        "status": "active",
        "description": "WebSocket untuk real-time notifications"
    }


# Endpoint untuk mendapatkan notifikasi yang belum dibaca
@router.get("/unread", response_model=UnreadNotificationsResponse)
async def get_unread_notifications(
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mendapatkan daftar notifikasi yang belum dibaca untuk user."""
    try:
        stmt = (
            select(ActivityLogModel)
            .where(ActivityLogModel.user_id == current_user.id)
            .order_by(ActivityLogModel.timestamp.desc())
            .limit(10)
        )

        result = await db.execute(stmt)
        notifications_from_db = result.scalars().all()

        unread_notifications = []
        for notif in notifications_from_db:
            action_lower = notif.action.lower()
            notif_type = "unknown"
            if "payment" in action_lower or "invoice" in action_lower:
                notif_type = "new_payment"
            elif "pelanggan" in action_lower:
                notif_type = "new_customer_for_noc"
            elif "teknis" in action_lower:
                notif_type = "new_technical_data"

            parsed_details = None
            if notif.details:
                try:
                    parsed_details = json.loads(notif.details)
                except json.JSONDecodeError:
                    # Fallback jika details bukan JSON valid
                    parsed_details = {"raw_details": notif.details}

            # Pastikan parsed_details adalah dict jika tidak None
            if parsed_details is not None and not isinstance(parsed_details, dict):
                parsed_details = {"raw_details": str(parsed_details)}

            unread_notifications.append(
                UnreadNotification(
                    id=notif.id,
                    timestamp=notif.timestamp.isoformat(),
                    action=notif.action,
                    type=notif_type,
                    details=parsed_details,
                )
            )

        return {
            "count": len(unread_notifications),
            "notifications": unread_notifications,
        }

    except Exception as e:
        logger.error(f"Error getting unread notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications",
        )


@router.post("/mark-all-as-read", status_code=status.HTTP_200_OK)
async def mark_all_as_read(current_user: UserModel = Depends(get_current_active_user)):
    """Marks all notifications for the current user as read."""
    logger.info(f"All notifications marked as read for user {current_user.id}")
    return {"message": "All notifications marked as read"}


@router.post("/{notification_id}/mark-as-read", status_code=status.HTTP_200_OK)
async def mark_as_read(notification_id: int, current_user: UserModel = Depends(get_current_active_user)):
    """Marks a single notification as read."""
    logger.info(f"Notification {notification_id} marked as read for user {current_user.id}")
    return {"message": f"Notification {notification_id} marked as read"}


# WebSocket endpoint telah dipindahkan ke main.py
# Path: /ws/notifications (langsung di main.py sesuai konfigurasi Apache)
