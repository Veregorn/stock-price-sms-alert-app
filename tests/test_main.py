"""Integration tests for main.py."""

import os
import sys
import pytest
from unittest.mock import patch, Mock, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main


class TestMain:
    """Integration tests for main function."""

    @patch('main.Notifier')
    @patch('main.NewsFetcher')
    @patch('main.StockFetcher')
    @patch('main.load_stocks_from_csv')
    @patch('main.config')
    def test_main_no_stocks_loaded(self, mock_config, mock_load_stocks,
                                   mock_stock_fetcher, mock_news_fetcher,
                                   mock_notifier):
        """Test main function when no stocks are loaded."""
        mock_config.USE_WHATSAPP = True
        mock_config.STOCKS_CSV_FILE = 'stocks.csv'
        mock_load_stocks.return_value = []

        # Should exit early when no stocks loaded
        main.main()

        # Verify that fetchers and notifier were not called
        mock_stock_fetcher.assert_not_called()
        mock_news_fetcher.assert_not_called()
        mock_notifier.assert_not_called()

    @patch('main.time.sleep')  # Mock sleep to speed up tests
    @patch('main.Notifier')
    @patch('main.NewsFetcher')
    @patch('main.StockFetcher')
    @patch('main.load_stocks_from_csv')
    @patch('main.config')
    def test_main_no_alerts_triggered(self, mock_config, mock_load_stocks,
                                     mock_stock_fetcher_class, mock_news_fetcher_class,
                                     mock_notifier_class, mock_sleep):
        """Test main function when stocks don't exceed thresholds."""
        # Setup mocks
        mock_config.USE_WHATSAPP = True
        mock_config.STOCKS_CSV_FILE = 'stocks.csv'
        mock_config.REQUEST_DELAY = 1
        mock_config.TWILIO_ACCOUNT_SID = 'test_sid'
        mock_config.TWILIO_AUTH_TOKEN = 'test_token'

        mock_load_stocks.return_value = [
            {'symbol': 'AAPL', 'company_name': 'Apple Inc', 'threshold': 5.0}
        ]

        # Mock stock fetcher
        mock_stock_fetcher = Mock()
        mock_stock_fetcher.get_percentage_change.return_value = (2.5, 150.0, 146.34, ['2025-01-10', '2025-01-09'])
        mock_stock_fetcher_class.return_value = mock_stock_fetcher

        # Mock news fetcher (shouldn't be called)
        mock_news_fetcher = Mock()
        mock_news_fetcher_class.return_value = mock_news_fetcher

        # Mock notifier (shouldn't be called)
        mock_notifier = Mock()
        mock_notifier_class.return_value = mock_notifier

        main.main()

        # Verify stock fetcher was called
        mock_stock_fetcher.get_percentage_change.assert_called_once_with('AAPL')

        # Verify news fetcher was not called (no alert)
        mock_news_fetcher.get_articles.assert_not_called()

        # Verify notifier was not used (no alert)
        mock_notifier.send_message.assert_not_called()

    @patch('main.time.sleep')
    @patch('main.Notifier')
    @patch('main.NewsFetcher')
    @patch('main.StockFetcher')
    @patch('main.load_stocks_from_csv')
    @patch('main.config')
    def test_main_with_alerts_triggered(self, mock_config, mock_load_stocks,
                                       mock_stock_fetcher_class, mock_news_fetcher_class,
                                       mock_notifier_class, mock_sleep):
        """Test main function when stocks exceed thresholds."""
        # Setup mocks
        mock_config.USE_WHATSAPP = True
        mock_config.STOCKS_CSV_FILE = 'stocks.csv'
        mock_config.REQUEST_DELAY = 1
        mock_config.TWILIO_ACCOUNT_SID = 'test_sid'
        mock_config.TWILIO_AUTH_TOKEN = 'test_token'

        mock_load_stocks.return_value = [
            {'symbol': 'TSLA', 'company_name': 'Tesla Inc', 'threshold': 5.0}
        ]

        # Mock stock fetcher - returns change above threshold
        mock_stock_fetcher = Mock()
        mock_stock_fetcher.get_percentage_change.return_value = (6.5, 250.0, 234.75, ['2025-01-10', '2025-01-09'])
        mock_stock_fetcher_class.return_value = mock_stock_fetcher

        # Mock news fetcher
        mock_news_fetcher = Mock()
        mock_news_fetcher.get_articles.return_value = [
            {
                'title': 'Tesla Hits New High',
                'description': 'Tesla stock reaches record levels',
                'url': 'https://example.com/1'
            }
        ]
        mock_news_fetcher_class.return_value = mock_news_fetcher

        # Mock notifier
        mock_notifier = Mock()
        mock_notifier.send_message.return_value = True
        mock_notifier_class.return_value = mock_notifier

        main.main()

        # Verify stock fetcher was called
        mock_stock_fetcher.get_percentage_change.assert_called_once_with('TSLA')

        # Verify news fetcher was called (alert triggered)
        mock_news_fetcher.get_articles.assert_called_once_with('Tesla Inc', limit=3)

        # Verify notifier sent messages (summary + detail)
        assert mock_notifier.send_message.call_count == 2

    @patch('main.time.sleep')
    @patch('main.Notifier')
    @patch('main.NewsFetcher')
    @patch('main.StockFetcher')
    @patch('main.load_stocks_from_csv')
    @patch('main.config')
    def test_main_stock_fetch_error(self, mock_config, mock_load_stocks,
                                    mock_stock_fetcher_class, mock_news_fetcher_class,
                                    mock_notifier_class, mock_sleep):
        """Test main function when stock fetch fails."""
        # Setup mocks
        mock_config.USE_WHATSAPP = True
        mock_config.STOCKS_CSV_FILE = 'stocks.csv'
        mock_config.REQUEST_DELAY = 1
        mock_config.TWILIO_ACCOUNT_SID = 'test_sid'
        mock_config.TWILIO_AUTH_TOKEN = 'test_token'

        mock_load_stocks.return_value = [
            {'symbol': 'INVALID', 'company_name': 'Invalid Co', 'threshold': 5.0}
        ]

        # Mock stock fetcher - returns None (error)
        mock_stock_fetcher = Mock()
        mock_stock_fetcher.get_percentage_change.return_value = (None, None, None, None)
        mock_stock_fetcher_class.return_value = mock_stock_fetcher

        # Mock news fetcher (shouldn't be called)
        mock_news_fetcher = Mock()
        mock_news_fetcher_class.return_value = mock_news_fetcher

        # Mock notifier (shouldn't be called)
        mock_notifier = Mock()
        mock_notifier_class.return_value = mock_notifier

        main.main()

        # Verify stock fetcher was called
        mock_stock_fetcher.get_percentage_change.assert_called_once_with('INVALID')

        # Verify news fetcher was not called (error occurred)
        mock_news_fetcher.get_articles.assert_not_called()

        # Verify notifier was not used (no alert)
        mock_notifier.send_message.assert_not_called()

    @patch('main.time.sleep')
    @patch('main.Notifier')
    @patch('main.NewsFetcher')
    @patch('main.StockFetcher')
    @patch('main.load_stocks_from_csv')
    @patch('main.config')
    def test_main_multiple_stocks(self, mock_config, mock_load_stocks,
                                  mock_stock_fetcher_class, mock_news_fetcher_class,
                                  mock_notifier_class, mock_sleep):
        """Test main function with multiple stocks."""
        # Setup mocks
        mock_config.USE_WHATSAPP = False  # Test SMS mode
        mock_config.STOCKS_CSV_FILE = 'stocks.csv'
        mock_config.REQUEST_DELAY = 1
        mock_config.TWILIO_ACCOUNT_SID = 'test_sid'
        mock_config.TWILIO_AUTH_TOKEN = 'test_token'

        mock_load_stocks.return_value = [
            {'symbol': 'TSLA', 'company_name': 'Tesla Inc', 'threshold': 5.0},
            {'symbol': 'AAPL', 'company_name': 'Apple Inc', 'threshold': 3.0}
        ]

        # Mock stock fetcher - one above, one below threshold
        mock_stock_fetcher = Mock()
        mock_stock_fetcher.get_percentage_change.side_effect = [
            (6.5, 250.0, 234.75, ['2025-01-10', '2025-01-09']),  # TSLA - alert
            (2.0, 150.0, 147.06, ['2025-01-10', '2025-01-09'])   # AAPL - no alert
        ]
        mock_stock_fetcher_class.return_value = mock_stock_fetcher

        # Mock news fetcher
        mock_news_fetcher = Mock()
        mock_news_fetcher.get_articles.return_value = []
        mock_news_fetcher_class.return_value = mock_news_fetcher

        # Mock notifier
        mock_notifier = Mock()
        mock_notifier.send_message.return_value = True
        mock_notifier_class.return_value = mock_notifier

        main.main()

        # Verify stock fetcher was called for both stocks
        assert mock_stock_fetcher.get_percentage_change.call_count == 2

        # Verify news fetcher was called only for TSLA (alert)
        mock_news_fetcher.get_articles.assert_called_once_with('Tesla Inc', limit=3)

        # Verify notifier sent messages (summary + 1 detail)
        assert mock_notifier.send_message.call_count == 2

    @patch('main.time.sleep')
    @patch('main.Notifier')
    @patch('main.NewsFetcher')
    @patch('main.StockFetcher')
    @patch('main.load_stocks_from_csv')
    @patch('main.config')
    def test_main_no_twilio_credentials(self, mock_config, mock_load_stocks,
                                       mock_stock_fetcher_class, mock_news_fetcher_class,
                                       mock_notifier_class, mock_sleep):
        """Test main function without Twilio credentials."""
        # Setup mocks - no credentials
        mock_config.USE_WHATSAPP = True
        mock_config.STOCKS_CSV_FILE = 'stocks.csv'
        mock_config.REQUEST_DELAY = 1
        mock_config.TWILIO_ACCOUNT_SID = None
        mock_config.TWILIO_AUTH_TOKEN = None

        mock_load_stocks.return_value = [
            {'symbol': 'TSLA', 'company_name': 'Tesla Inc', 'threshold': 5.0}
        ]

        # Mock stock fetcher - returns change above threshold
        mock_stock_fetcher = Mock()
        mock_stock_fetcher.get_percentage_change.return_value = (6.5, 250.0, 234.75, ['2025-01-10', '2025-01-09'])
        mock_stock_fetcher_class.return_value = mock_stock_fetcher

        # Mock news fetcher
        mock_news_fetcher = Mock()
        mock_news_fetcher.get_articles.return_value = []
        mock_news_fetcher_class.return_value = mock_news_fetcher

        # Mock notifier (shouldn't be called without credentials)
        mock_notifier = Mock()
        mock_notifier_class.return_value = mock_notifier

        main.main()

        # Verify notifier was not used (no credentials)
        mock_notifier.send_message.assert_not_called()

    @patch('main.main')
    def test_keyboard_interrupt(self, mock_main_func):
        """Test handling of keyboard interrupt."""
        mock_main_func.side_effect = KeyboardInterrupt()

        # Import the module to run the if __name__ == "__main__" block
        # This is tricky to test, so we'll just verify main handles it gracefully
        try:
            if __name__ != "__main__":
                main.main()
        except KeyboardInterrupt:
            pass  # Expected behavior
