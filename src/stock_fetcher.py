"""
Stock data fetching module.

Handles all interactions with the Alpha Vantage API for stock price data.
"""

import logging
import requests
from typing import Optional, Tuple, List

from .config import config

logger = logging.getLogger(__name__)


class StockFetcher:
    """Fetches stock price data from Alpha Vantage API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize StockFetcher.

        Args:
            api_key: Alpha Vantage API key. If None, uses config value.
        """
        self.api_key = api_key or config.ALPHA_VANTAGE_API_KEY
        self.endpoint = config.ALPHA_VANTAGE_ENDPOINT
        self.timeout = config.API_TIMEOUT

    def get_percentage_change(
        self, symbol: str
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[List[str]]]:
        """
        Get the percentage change of a stock between yesterday and the day before.

        Args:
            symbol: Stock ticker symbol (e.g., 'TSLA')

        Returns:
            Tuple of (percentage_change, yesterday_close, day_before_close, dates)
            Returns (None, None, None, None) if error occurs
        """
        logger.debug(f"Fetching stock data for {symbol}")

        parameters = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": self.api_key
        }

        try:
            response = requests.get(
                self.endpoint,
                params=parameters,
                timeout=self.timeout
            )
            response.raise_for_status()
            stock_data = response.json()

            if "Time Series (Daily)" not in stock_data:
                logger.warning(
                    f"No time series data for {symbol}. Response: {stock_data}"
                )
                return None, None, None, None

            # Get the two most recent days of data
            daily_data = stock_data["Time Series (Daily)"]
            recent_dates = list(daily_data.keys())[:2]

            yesterday_close = float(daily_data[recent_dates[0]]["4. close"])
            day_before_yesterday_close = float(daily_data[recent_dates[1]]["4. close"])

            # Calculate percentage change
            difference = yesterday_close - day_before_yesterday_close
            percentage_change = (difference / day_before_yesterday_close) * 100

            logger.info(f"{symbol}: ${yesterday_close:.2f} ({percentage_change:+.2f}%)")
            return percentage_change, yesterday_close, day_before_yesterday_close, recent_dates

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching data for {symbol}")
            return None, None, None, None

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}", exc_info=True)
            return None, None, None, None
