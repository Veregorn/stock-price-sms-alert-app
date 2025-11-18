"""
Router for sending notifications.

Handles sending WhatsApp/SMS alerts for triggered price changes using Twilio.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
import logging

from ...database import DatabaseService
from ...notifier import Notifier
from ...config import config
from ..dependencies import get_db
from ..schemas import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Notifications"],
)


# =============================================================================
# POST /api/alerts/{alert_id}/send - Send notification for a specific alert
# =============================================================================

@router.post(
    "/alerts/{alert_id}/send",
    response_model=dict,
    summary="Send notification for a specific alert",
    description="Sends a WhatsApp or SMS notification for a specific alert using Twilio.",
    responses={
        200: {
            "description": "Notification sent successfully"
        },
        404: {
            "description": "Alert not found",
            "model": ErrorResponse
        },
        503: {
            "description": "Twilio service unavailable or credentials not configured",
            "model": ErrorResponse
        }
    }
)
async def send_alert_notification(
    alert_id: int,
    use_whatsapp: bool = Query(
        True,
        description="Send via WhatsApp (true) or SMS (false)"
    ),
    db: DatabaseService = Depends(get_db)
):
    """
    Send notification for a specific alert.

    This endpoint:
    1. Retrieves the alert from the database
    2. Gets the associated stock information
    3. Formats a notification message
    4. Sends via WhatsApp or SMS using Twilio
    5. Updates the alert status in the database

    **Note**: Requires Twilio credentials in environment variables.

    Parameters:
    - **alert_id**: ID of the alert to send
    - **use_whatsapp**: Send via WhatsApp (true) or SMS (false)

    Returns:
    - **message**: Success message
    - **alert_id**: ID of the alert
    - **notification_type**: "whatsapp" or "sms"
    - **sent**: Whether the notification was sent successfully
    """
    # Get alert from database
    with db.get_session() as session:
        from ...database.models import Alert
        alert = session.query(Alert).filter(Alert.id == alert_id).first()

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found"
            )

        # Get stock information
        stock = db.get_stock_by_id(alert.stock_id)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock with ID {alert.stock_id} not found"
            )

        # Format notification message
        symbol = stock.symbol
        company_name = stock.company_name
        percentage_change = alert.percentage_change
        price_before = alert.price_before
        price_after = alert.price_after
        threshold = alert.threshold_at_time

        # Determine if it's an increase or decrease
        direction = "increased" if percentage_change > 0 else "decreased"
        arrow = "📈" if percentage_change > 0 else "📉"

        message_body = (
            f"{arrow} STOCK ALERT: {symbol}\n\n"
            f"Company: {company_name}\n"
            f"Price {direction} by {abs(percentage_change):.2f}%\n\n"
            f"Previous Close: ${price_before:.2f}\n"
            f"Current Close: ${price_after:.2f}\n"
            f"Threshold: {threshold:.2f}%\n\n"
            f"This alert was triggered because the price change exceeded your configured threshold."
        )

        # Initialize notifier
        notifier = Notifier(use_whatsapp=use_whatsapp)

        # Check if Twilio credentials are configured
        if not notifier.account_sid or not notifier.auth_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Twilio credentials not configured. Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in environment variables."
            )

        # Send notification
        try:
            success = notifier.send_message(message_body)
            notification_type = "whatsapp" if use_whatsapp else "sms"

            # Update alert status in database
            db.update_alert_status(
                alert_id=alert_id,
                message_sent=success,
                notification_type=notification_type,
                error_message=None if success else "Failed to send notification"
            )

            if success:
                logger.info(f"Notification sent successfully for alert {alert_id} via {notification_type}")
                return {
                    "message": f"Notification sent successfully via {notification_type}",
                    "alert_id": alert_id,
                    "notification_type": notification_type,
                    "sent": True,
                    "symbol": symbol,
                    "percentage_change": percentage_change
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to send notification. Check Twilio credentials and logs."
                )

        except Exception as e:
            logger.error(f"Error sending notification for alert {alert_id}: {str(e)}")

            # Update alert with error
            db.update_alert_status(
                alert_id=alert_id,
                message_sent=False,
                notification_type="whatsapp" if use_whatsapp else "sms",
                error_message=str(e)
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to send notification: {str(e)}"
            )


# =============================================================================
# POST /api/alerts/send-pending - Send notifications for all pending alerts
# =============================================================================

@router.post(
    "/alerts/send-pending",
    response_model=dict,
    summary="Send notifications for all pending alerts",
    description="Sends WhatsApp or SMS notifications for all alerts that haven't been sent yet.",
    responses={
        200: {
            "description": "Notifications sent"
        }
    }
)
async def send_pending_alerts(
    use_whatsapp: bool = Query(
        True,
        description="Send via WhatsApp (true) or SMS (false)"
    ),
    db: DatabaseService = Depends(get_db)
):
    """
    Send notifications for all pending alerts.

    This endpoint:
    1. Retrieves all alerts with message_sent=False
    2. Sends a notification for each alert
    3. Updates each alert's status

    **Note**: Be mindful of Twilio API rate limits when sending many alerts.

    Parameters:
    - **use_whatsapp**: Send via WhatsApp (true) or SMS (false)

    Returns:
    - **message**: Summary message
    - **total_pending**: Number of pending alerts found
    - **sent**: Number of notifications sent successfully
    - **failed**: Number of notifications that failed
    - **results**: List of per-alert results
    """
    # Get pending alerts
    pending_alerts = db.get_pending_alerts()

    if not pending_alerts:
        return {
            "message": "No pending alerts to send",
            "total_pending": 0,
            "sent": 0,
            "failed": 0,
            "results": []
        }

    # Initialize notifier
    notifier = Notifier(use_whatsapp=use_whatsapp)
    notification_type = "whatsapp" if use_whatsapp else "sms"

    # Check if Twilio credentials are configured
    if not notifier.account_sid or not notifier.auth_token:
        logger.warning("Twilio credentials not configured, skipping notifications")
        return {
            "message": "Twilio credentials not configured",
            "total_pending": len(pending_alerts),
            "sent": 0,
            "failed": len(pending_alerts),
            "results": [
                {
                    "alert_id": alert.id,
                    "success": False,
                    "error": "Twilio credentials not configured"
                }
                for alert in pending_alerts
            ]
        }

    # Initialize counters
    sent_count = 0
    failed_count = 0
    results = []

    # Send notification for each alert
    for alert in pending_alerts:
        result = {
            "alert_id": alert.id,
            "success": False,
            "symbol": None,
            "percentage_change": alert.percentage_change,
            "error": None
        }

        try:
            # Get stock information
            stock = db.get_stock_by_id(alert.stock_id)
            if not stock:
                result["error"] = f"Stock with ID {alert.stock_id} not found"
                failed_count += 1
                results.append(result)
                continue

            result["symbol"] = stock.symbol

            # Format notification message
            direction = "increased" if alert.percentage_change > 0 else "decreased"
            arrow = "📈" if alert.percentage_change > 0 else "📉"

            message_body = (
                f"{arrow} STOCK ALERT: {stock.symbol}\n\n"
                f"Company: {stock.company_name}\n"
                f"Price {direction} by {abs(alert.percentage_change):.2f}%\n\n"
                f"Previous Close: ${alert.price_before:.2f}\n"
                f"Current Close: ${alert.price_after:.2f}\n"
                f"Threshold: {alert.threshold_at_time:.2f}%\n\n"
                f"This alert was triggered because the price change exceeded your configured threshold."
            )

            # Send notification
            success = notifier.send_message(message_body)

            # Update alert status
            db.update_alert_status(
                alert_id=alert.id,
                message_sent=success,
                notification_type=notification_type,
                error_message=None if success else "Failed to send notification"
            )

            if success:
                result["success"] = True
                sent_count += 1
                logger.info(f"Notification sent for alert {alert.id} ({stock.symbol})")
            else:
                result["error"] = "Failed to send notification"
                failed_count += 1

        except Exception as e:
            logger.error(f"Error sending notification for alert {alert.id}: {str(e)}")
            result["error"] = str(e)
            failed_count += 1

            # Update alert with error
            db.update_alert_status(
                alert_id=alert.id,
                message_sent=False,
                notification_type=notification_type,
                error_message=str(e)
            )

        results.append(result)

    # Return summary
    return {
        "message": f"Sent {sent_count} of {len(pending_alerts)} pending alerts",
        "total_pending": len(pending_alerts),
        "sent": sent_count,
        "failed": failed_count,
        "notification_type": notification_type,
        "results": results
    }
