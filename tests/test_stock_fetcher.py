"""Tests for src.stock_fetcher module."""

import os
import sys
import pytest
from unittest.mock import Mock, patch
import requests

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.stock_fetcher import StockFetcher


class TestStockFetcher:
    """Tests for StockFetcher class."""

    @pytest.fixture
    def stock_fetcher(self):
        """Create a StockFetcher instance for testing."""
        return StockFetcher(api_key='test_api_key')

    def test_init_with_api_key(self):
        """Test initialization with provided API key."""
        fetcher = StockFetcher(api_key='custom_key')
        assert fetcher.api_key == 'custom_key'

    @patch('src.stock_fetcher.config')
    def test_init_without_api_key(self, mock_config):
        """Test initialization without API key uses config."""
        mock_config.ALPHA_VANTAGE_API_KEY = 'config_key'
        fetcher = StockFetcher()
        assert fetcher.api_key == 'config_key'

    @patch('src.stock_fetcher.requests.get')
    def test_get_percentage_change_success(self, mock_get, stock_fetcher):
        """Test successful percentage change calculation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Time Series (Daily)": {
                "2025-01-10": {"4. close": "250.00"},
                "2025-01-09": {"4. close": "240.00"}
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        pct_change, yesterday, day_before, dates = stock_fetcher.get_percentage_change('TSLA')

        assert pct_change is not None
        assert abs(pct_change - 4.166666666666667) < 0.01  # (250-240)/240 * 100
        assert yesterday == 250.00
        assert day_before == 240.00
        assert dates == ["2025-01-10", "2025-01-09"]

    @patch('src.stock_fetcher.requests.get')
    def test_get_percentage_change_negative(self, mock_get, stock_fetcher):
        """Test percentage change with negative result."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Time Series (Daily)": {
                "2025-01-10": {"4. close": "230.00"},
                "2025-01-09": {"4. close": "250.00"}
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        pct_change, yesterday, day_before, dates = stock_fetcher.get_percentage_change('AAPL')

        assert pct_change is not None
        assert pct_change < 0
        assert abs(pct_change - (-8.0)) < 0.01  # (230-250)/250 * 100
        assert yesterday == 230.00
        assert day_before == 250.00

    @patch('src.stock_fetcher.requests.get')
    def test_get_percentage_change_no_time_series(self, mock_get, stock_fetcher):
        """Test when API response has no time series data."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute."
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        pct_change, yesterday, day_before, dates = stock_fetcher.get_percentage_change('INVALID')

        assert pct_change is None
        assert yesterday is None
        assert day_before is None
        assert dates is None

    @patch('src.stock_fetcher.requests.get')
    def test_get_percentage_change_timeout(self, mock_get, stock_fetcher):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()

        pct_change, yesterday, day_before, dates = stock_fetcher.get_percentage_change('TSLA')

        assert pct_change is None
        assert yesterday is None
        assert day_before is None
        assert dates is None

    @patch('src.stock_fetcher.requests.get')
    def test_get_percentage_change_request_error(self, mock_get, stock_fetcher):
        """Test handling of request errors."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        pct_change, yesterday, day_before, dates = stock_fetcher.get_percentage_change('TSLA')

        assert pct_change is None
        assert yesterday is None
        assert day_before is None
        assert dates is None

    @patch('src.stock_fetcher.requests.get')
    def test_get_percentage_change_http_error(self, mock_get, stock_fetcher):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        pct_change, yesterday, day_before, dates = stock_fetcher.get_percentage_change('TSLA')

        assert pct_change is None
        assert yesterday is None
        assert day_before is None
        assert dates is None
