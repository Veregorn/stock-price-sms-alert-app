"""
Router for stock price updates.

Handles fetching real-time stock prices from Alpha Vantage API
and updating the database with new price data and alerts.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from ...database import DatabaseService
from ...stock_fetcher import StockFetcher
from ..dependencies import get_db
from ..schemas import (
    PriceHistoryResponse,
    AlertResponse,
    MessageResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["Stock Updates"],
)


# =============================================================================
# POST /api/stocks/{symbol}/update-price - Update price for single stock
# =============================================================================

@router.post(
    "/stocks/{symbol}/update-price",
    response_model=dict,
    summary="Update stock price from Alpha Vantage",
    description="Fetches the latest price from Alpha Vantage API, saves to database, and creates alert if threshold exceeded.",
    responses={
        200: {
            "description": "Price updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Price updated successfully",
                        "symbol": "AAPL",
                        "price": {
                            "id": 1,
                            "stock_id": 1,
                            "date": "2024-01-15T00:00:00",
                            "close_price": 175.50,
                            "previous_close": 173.20,
                            "percentage_change": 1.33,
                            "created_at": "2024-01-15T10:30:00"
                        },
                        "alert_triggered": True,
                        "alert": {
                            "id": 1,
                            "stock_id": 1,
                            "percentage_change": 6.5,
                            "threshold_at_time": 5.0,
                            "price_before": 173.20,
                            "price_after": 175.50,
                            "message_sent": False,
                            "notification_type": None,
                            "error_message": None,
                            "triggered_at": "2024-01-15T10:30:00"
                        }
                    }
                }
            }
        },
        404: {
            "description": "Stock not found",
            "model": ErrorResponse
        },
        503: {
            "description": "External API error",
            "model": ErrorResponse
        }
    }
)
async def update_stock_price(
    symbol: str,
    db: DatabaseService = Depends(get_db)
):
    """
    Update stock price from Alpha Vantage API.

    This endpoint:
    1. Fetches the latest price data from Alpha Vantage
    2. Calculates percentage change from previous day
    3. Saves price history to database
    4. Checks if threshold is exceeded
    5. Creates alert if threshold exceeded
    6. Returns updated price and alert info

    **Note**: Requires ALPHA_VANTAGE_API_KEY in environment variables.

    Parameters:
    - **symbol**: Stock symbol (e.g., AAPL, TSLA)

    Returns:
    - **message**: Success message
    - **symbol**: Stock symbol
    - **price**: Created PriceHistory object
    - **alert_triggered**: Boolean indicating if alert was created
    - **alert**: Alert object if created, otherwise None

    Errors:
    - **404**: Stock not found in database
    - **503**: Alpha Vantage API error or timeout
    """
    # Verify stock exists
    stock = db.get_stock_by_symbol(symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol.upper()}' not found"
        )

    # Initialize stock fetcher
    fetcher = StockFetcher()

    # Fetch price data from Alpha Vantage
    try:
        percentage_change, yesterday_close, day_before_close, dates = fetcher.get_percentage_change(symbol)
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch price data from Alpha Vantage: {str(e)}"
        )

    # Check if we got valid data
    if percentage_change is None or yesterday_close is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Alpha Vantage API returned no data for {symbol}. Check API key and rate limits."
        )

    # Parse date from Alpha Vantage response
    price_date = datetime.strptime(dates[0], "%Y-%m-%d") if dates else datetime.utcnow()

    # Save price history to database
    try:
        price_record = db.add_price_history(
            symbol=symbol,
            date=price_date,
            close_price=yesterday_close,
            previous_close=day_before_close,
            percentage_change=percentage_change
        )

        if not price_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save price to database"
            )

        logger.info(f"Price saved for {symbol}: ${yesterday_close:.2f} ({percentage_change:+.2f}%)")

    except Exception as e:
        logger.error(f"Error saving price for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save price to database: {str(e)}"
        )

    # Check if alert should be triggered
    alert_triggered = False
    alert = None
    alert_already_exists = False

    if stock.is_active and abs(percentage_change) >= stock.threshold:
        # Check if an alert already exists for this stock with these prices
        # Alpha Vantage returns daily data, so we avoid duplicate alerts for the same day
        if db.has_alert_for_price_date(symbol, price_date, day_before_close, yesterday_close):
            alert_already_exists = True
            logger.info(
                f"Alert for {symbol} with prices {day_before_close} -> {yesterday_close} already exists, skipping duplicate"
            )
        else:
            # Create alert
            try:
                alert = db.create_alert(
                    symbol=symbol,
                    percentage_change=percentage_change,
                    threshold_at_time=stock.threshold,
                    price_before=day_before_close,
                    price_after=yesterday_close,
                    message_sent=False,  # Will be updated by notification service
                    notification_type=None,
                    error_message=None
                )

                if alert:
                    alert_triggered = True
                    logger.warning(
                        f"Alert created for {symbol}: {percentage_change:+.2f}% "
                        f"(threshold: {stock.threshold}%)"
                    )
            except Exception as e:
                logger.error(f"Error creating alert for {symbol}: {str(e)}")
                # Don't fail the request if alert creation fails
                pass

    # Return response
    response_message = "Price updated successfully"
    if alert_already_exists:
        response_message += " (alert already exists for this date)"

    return {
        "message": response_message,
        "symbol": symbol.upper(),
        "price": {
            "id": price_record.id,
            "stock_id": price_record.stock_id,
            "date": price_record.date.isoformat(),
            "close_price": price_record.close_price,
            "previous_close": price_record.previous_close,
            "percentage_change": price_record.percentage_change,
            "created_at": price_record.created_at.isoformat()
        },
        "alert_triggered": alert_triggered,
        "alert_already_exists": alert_already_exists,
        "alert": {
            "id": alert.id,
            "stock_id": alert.stock_id,
            "percentage_change": alert.percentage_change,
            "threshold_at_time": alert.threshold_at_time,
            "price_before": alert.price_before,
            "price_after": alert.price_after,
            "message_sent": alert.message_sent,
            "notification_type": alert.notification_type,
            "error_message": alert.error_message,
            "triggered_at": alert.triggered_at.isoformat()
        } if alert else None
    }


# =============================================================================
# POST /api/stocks/update-all-prices - Update prices for all active stocks
# =============================================================================

@router.post(
    "/stocks/update-all-prices",
    response_model=dict,
    summary="Update all active stock prices",
    description="Fetches latest prices for all active stocks from Alpha Vantage API.",
    responses={
        200: {
            "description": "Prices updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Updated prices for 5 stocks",
                        "total_stocks": 8,
                        "active_stocks": 5,
                        "updated": 4,
                        "failed": 1,
                        "alerts_triggered": 2,
                        "results": [
                            {
                                "symbol": "AAPL",
                                "success": True,
                                "price": 175.50,
                                "change": 1.33,
                                "alert_triggered": False
                            },
                            {
                                "symbol": "TSLA",
                                "success": True,
                                "price": 250.75,
                                "change": 6.5,
                                "alert_triggered": True
                            }
                        ]
                    }
                }
            }
        },
        503: {
            "description": "Partial or complete failure",
            "model": ErrorResponse
        }
    }
)
async def update_all_stock_prices(
    db: DatabaseService = Depends(get_db)
):
    """
    Update prices for all active stocks.

    This endpoint:
    1. Fetches all active stocks from database
    2. Updates price for each stock from Alpha Vantage
    3. Creates alerts for stocks exceeding thresholds
    4. Returns summary of updates

    **Note**:
    - Requires ALPHA_VANTAGE_API_KEY in environment
    - Subject to Alpha Vantage rate limits (5 requests/minute on free tier)
    - Failed updates for individual stocks won't stop the process

    Returns:
    - **message**: Summary message
    - **total_stocks**: Total stocks in database
    - **active_stocks**: Number of active stocks
    - **updated**: Number of successfully updated stocks
    - **failed**: Number of failed updates
    - **alerts_triggered**: Number of alerts created
    - **results**: Array of update results per stock

    Errors:
    - **503**: If all updates fail
    """
    # Get all active stocks
    active_stocks = db.get_all_stocks(only_active=True)
    total_stocks = len(db.get_all_stocks(only_active=False))

    if not active_stocks:
        return {
            "message": "No active stocks to update",
            "total_stocks": total_stocks,
            "active_stocks": 0,
            "updated": 0,
            "failed": 0,
            "alerts_triggered": 0,
            "results": []
        }

    # Initialize counters
    updated_count = 0
    failed_count = 0
    alerts_count = 0
    results = []

    # Initialize fetcher once
    fetcher = StockFetcher()

    # Update each stock
    for stock in active_stocks:
        result = {
            "symbol": stock.symbol,
            "success": False,
            "price": None,
            "change": None,
            "alert_triggered": False,
            "alert_already_exists": False,
            "error": None
        }

        try:
            # Fetch price from Alpha Vantage
            percentage_change, yesterday_close, day_before_close, dates = fetcher.get_percentage_change(stock.symbol)

            if percentage_change is None or yesterday_close is None:
                result["error"] = "No data returned from Alpha Vantage"
                failed_count += 1
                results.append(result)
                continue

            # Parse date
            price_date = datetime.strptime(dates[0], "%Y-%m-%d") if dates else datetime.utcnow()

            # Save price
            price_record = db.add_price_history(
                symbol=stock.symbol,
                date=price_date,
                close_price=yesterday_close,
                previous_close=day_before_close,
                percentage_change=percentage_change
            )

            if price_record:
                result["success"] = True
                result["price"] = yesterday_close
                result["change"] = percentage_change
                updated_count += 1

                # Check for alert
                if abs(percentage_change) >= stock.threshold:
                    # Check if alert already exists with these prices
                    if not db.has_alert_for_price_date(stock.symbol, price_date, day_before_close, yesterday_close):
                        alert = db.create_alert(
                            symbol=stock.symbol,
                            percentage_change=percentage_change,
                            threshold_at_time=stock.threshold,
                            price_before=day_before_close,
                            price_after=yesterday_close,
                            message_sent=False,
                            notification_type=None,
                            error_message=None
                        )

                        if alert:
                            result["alert_triggered"] = True
                            alerts_count += 1
                    else:
                        logger.info(
                            f"Alert for {stock.symbol} with prices {day_before_close} -> {yesterday_close} already exists, skipping"
                        )
                        result["alert_already_exists"] = True

            else:
                result["error"] = "Failed to save price to database"
                failed_count += 1

        except Exception as e:
            logger.error(f"Error updating {stock.symbol}: {str(e)}")
            result["error"] = str(e)
            failed_count += 1

        results.append(result)

    # Return summary
    return {
        "message": f"Updated prices for {updated_count} of {len(active_stocks)} active stocks",
        "total_stocks": total_stocks,
        "active_stocks": len(active_stocks),
        "updated": updated_count,
        "failed": failed_count,
        "alerts_triggered": alerts_count,
        "results": results
    }
