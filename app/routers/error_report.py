"""
Router untuk menangani error reporting dari frontend.
Ini digunakan untuk melacak 404 errors dan masalah teknis lainnya.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from fastapi import Depends
from ..models.activity_log import ActivityLog
from ..utils.error_handler import error_tracker

router = APIRouter(prefix="/api", tags=["error-reporting"])
logger = logging.getLogger(__name__)


class ErrorReportRequest(BaseModel):
    """Model untuk error report dari frontend."""
    issue: str
    path: str
    user_agent: str
    timestamp: str
    reference_id: str
    include_screenshot: Optional[bool] = False
    additional_info: Optional[Dict[str, Any]] = None


@router.post("/error-report", status_code=status.HTTP_201_CREATED)
async def submit_error_report(
    request: Request,
    report_data: ErrorReportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk menerima error report dari frontend.
    Digunakan untuk tracking 404 errors dan masalah lainnya.
    """
    try:
        # Log error report untuk monitoring
        logger.warning(
            f"Frontend Error Report - Ref ID: {report_data.reference_id} - "
            f"Path: {report_data.path} - Issue: {report_data.issue[:100]}..."
        )

        # Track error untuk monitoring internal
        error_tracker.track_error(
            operation="frontend_error_report",
            error=Exception(f"Frontend Error: {report_data.issue}"),
            context={
                "path": report_data.path,
                "reference_id": report_data.reference_id,
                "user_agent": report_data.user_agent,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )

        # Simpan ke activity log
        try:
            import json
            # Simpan error report sebagai activity log dengan JSON string
            activity_log = ActivityLog(
                user_id=None,  # Anonymous error report
                action="FRONTEND_ERROR_REPORT",
                details=json.dumps({
                    "reference_id": report_data.reference_id,
                    "path": report_data.path,
                    "issue": report_data.issue,
                    "user_agent": report_data.user_agent,
                    "timestamp": report_data.timestamp,
                    "client_ip": request.client.host if request.client else "unknown",
                    "include_screenshot": report_data.include_screenshot,
                    "additional_info": report_data.additional_info
                })
            )
            db.add(activity_log)
            await db.commit()
        except Exception as db_error:
            logger.error(f"Failed to save error report to database: {db_error}")
            # Continue even if database save fails

        return {
            "success": True,
            "message": "Error report berhasil dikirim",
            "reference_id": report_data.reference_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing error report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal memproses error report"
        )


@router.get("/error-stats")
async def get_error_stats(db: AsyncSession = Depends(get_db)):
    """
    Endpoint untuk mendapatkan statistik error (admin only).
    Ini bisa digunakan untuk monitoring dashboard.
    """
    try:
        # Get error stats from error tracker
        error_summary = error_tracker.get_error_summary()

        # Get recent error reports from database
        recent_errors = []
        try:
            from sqlalchemy import select, desc
            import json

            stmt = select(ActivityLog).where(
                ActivityLog.action == "FRONTEND_ERROR_REPORT"
            ).order_by(desc(ActivityLog.id)).limit(10)
            result = await db.execute(stmt)
            recent_activities = result.scalars().all()

            for activity in recent_activities:
                try:
                    # Parse JSON from details field
                    details = json.loads(activity.details) if activity.details else {}
                    recent_errors.append({
                        "id": activity.id,
                        "timestamp": activity.timestamp.isoformat() if activity.timestamp else None,
                        "path": details.get("path"),
                        "issue": details.get("issue", "")[:100] + "..." if details.get("issue") else "",
                        "reference_id": details.get("reference_id"),
                        "client_ip": details.get("client_ip")
                    })
                except json.JSONDecodeError:
                    # Handle case where details is not valid JSON
                    recent_errors.append({
                        "id": activity.id,
                        "timestamp": activity.timestamp.isoformat() if activity.timestamp else None,
                        "path": None,
                        "issue": activity.details[:100] + "..." if activity.details else "No details available",
                        "reference_id": None,
                        "client_ip": None
                    })

        except Exception as db_error:
            logger.warning(f"Failed to get recent errors from database: {db_error}")

        return {
            "total_errors": error_summary.get("total_errors", 0),
            "unique_errors": error_summary.get("unique_errors", 0),
            "error_details": error_summary.get("error_details", {}),
            "recent_frontend_errors": recent_errors,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting error stats: {e}")
        return {
            "total_errors": 0,
            "unique_errors": 0,
            "error_details": {},
            "recent_frontend_errors": [],
            "error": "Failed to get error statistics"
        }