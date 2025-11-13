import os
import sys
import pytest
import tempfile
from unittest.mock import patch, MagicMock, mock_open

# Add parent directory to path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main


class TestLoadStocksFromCSV:
    """Tests for load_stocks_from_csv function"""

    def test_load_stocks_success(self, tmp_path):
        """Test successful loading of stocks from CSV"""
        # Create a temporary CSV file
        csv_file = tmp_path / "test_stocks.csv"
        csv_content = """symbol,company_name,threshold
TSLA,Tesla Inc,5
AAPL,Apple Inc,3
GOOGL,Alphabet Inc,4"""
        csv_file.write_text(csv_content)

        # Load stocks
        stocks = main.load_stocks_from_csv(str(csv_file))

        # Assertions
        assert len(stocks) == 3
        assert stocks[0]['symbol'] == 'TSLA'
        assert stocks[0]['company_name'] == 'Tesla Inc'
        assert stocks[0]['threshold'] == 5.0
        assert stocks[1]['symbol'] == 'AAPL'
        assert stocks[2]['symbol'] == 'GOOGL'

    def test_load_stocks_file_not_found(self):
        """Test loading stocks from non-existent file"""
        stocks = main.load_stocks_from_csv("non_existent_file.csv")
        assert stocks == []

    def test_load_stocks_empty_file(self, tmp_path):
        """Test loading stocks from empty CSV file"""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("symbol,company_name,threshold\n")

        stocks = main.load_stocks_from_csv(str(csv_file))
        assert stocks == []

    def test_load_stocks_with_whitespace(self, tmp_path):
        """Test that whitespace is properly stripped"""
        csv_file = tmp_path / "whitespace.csv"
        csv_content = """symbol,company_name,threshold
  TSLA  ,  Tesla Inc  ,  5  """
        csv_file.write_text(csv_content)

        stocks = main.load_stocks_from_csv(str(csv_file))
        assert stocks[0]['symbol'] == 'TSLA'
        assert stocks[0]['company_name'] == 'Tesla Inc'


class TestGetStockPercentageChange:
    """Tests for get_stock_percentage_change function"""

    @patch('main.requests.get')
    def test_get_stock_percentage_change_success(self, mock_get):
        """Test successful stock data retrieval and calculation"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Time Series (Daily)": {
                "2024-01-10": {"4. close": "250.00"},
                "2024-01-09": {"4. close": "240.00"}
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Call function
        percentage_change, yesterday_close, day_before_close, dates = main.get_stock_percentage_change("AAPL")

        # Assertions
        assert yesterday_close == 250.00
        assert day_before_close == 240.00
        assert abs(percentage_change - 4.17) < 0.01  # 4.17% increase
        assert dates == ["2024-01-10", "2024-01-09"]

    @patch('main.requests.get')
    def test_get_stock_percentage_change_negative(self, mock_get):
        """Test stock with negative percentage change"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Time Series (Daily)": {
                "2024-01-10": {"4. close": "100.00"},
                "2024-01-09": {"4. close": "110.00"}
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        percentage_change, _, _, _ = main.get_stock_percentage_change("TSLA")
        assert percentage_change < 0
        assert abs(percentage_change - (-9.09)) < 0.01

    @patch('main.requests.get')
    def test_get_stock_percentage_change_api_error(self, mock_get):
        """Test handling of API errors"""
        mock_get.side_effect = Exception("API Error")

        result = main.get_stock_percentage_change("INVALID")
        assert result == (None, None, None, None)

    @patch('main.requests.get')
    def test_get_stock_percentage_change_timeout(self, mock_get):
        """Test handling of timeout errors"""
        mock_get.side_effect = main.requests.exceptions.Timeout("Timeout")

        result = main.get_stock_percentage_change("AAPL")
        assert result == (None, None, None, None)

    @patch('main.requests.get')
    def test_get_stock_percentage_change_no_data(self, mock_get):
        """Test handling when no time series data is returned"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"Error Message": "Invalid API call"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = main.get_stock_percentage_change("INVALID")
        assert result == (None, None, None, None)


class TestGetNewsArticles:
    """Tests for get_news_articles function"""

    @patch('main.requests.get')
    def test_get_news_articles_success(self, mock_get):
        """Test successful news retrieval"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Tesla News 1",
                    "description": "Description 1",
                    "url": "https://example.com/1"
                },
                {
                    "title": "Tesla News 2",
                    "description": "Description 2",
                    "url": "https://example.com/2"
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        articles = main.get_news_articles("Tesla Inc", limit=3)

        assert len(articles) == 2
        assert articles[0]['title'] == "Tesla News 1"
        assert articles[1]['title'] == "Tesla News 2"

    @patch('main.requests.get')
    def test_get_news_articles_empty(self, mock_get):
        """Test when no news articles are found"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": []
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        articles = main.get_news_articles("Unknown Company")
        assert articles == []

    @patch('main.requests.get')
    def test_get_news_articles_api_error(self, mock_get):
        """Test handling of API errors"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "error",
            "message": "API key invalid"
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        articles = main.get_news_articles("Tesla Inc")
        assert articles == []

    @patch('main.requests.get')
    def test_get_news_articles_exception(self, mock_get):
        """Test handling of network exceptions"""
        mock_get.side_effect = Exception("Network error")

        articles = main.get_news_articles("Tesla Inc")
        assert articles == []


class TestGenerateStockReport:
    """Tests for generate_stock_report function"""

    def test_generate_stock_report_with_news(self):
        """Test report generation with news articles"""
        stock_info = {
            'symbol': 'TSLA',
            'company_name': 'Tesla Inc',
            'threshold': 5
        }
        percentage_change = 6.5
        articles = [
            {
                'title': 'Tesla Hits New High',
                'description': 'Tesla stock reaches record levels',
                'url': 'https://example.com/1'
            }
        ]

        report = main.generate_stock_report(stock_info, percentage_change, articles)

        assert 'TSLA' in report
        assert 'Tesla Inc' in report
        assert '6.50%' in report
        assert '5%' in report  # threshold
        assert 'Tesla Hits New High' in report
        assert 'https://example.com/1' in report
        assert '🔺' in report  # up arrow for positive change

    def test_generate_stock_report_negative_change(self):
        """Test report generation with negative change"""
        stock_info = {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc',
            'threshold': 3
        }
        percentage_change = -4.2
        articles = []

        report = main.generate_stock_report(stock_info, percentage_change, articles)

        assert 'AAPL' in report
        assert '4.20%' in report  # absolute value
        assert '🔻' in report  # down arrow for negative change

    def test_generate_stock_report_no_news(self):
        """Test report generation without news articles"""
        stock_info = {
            'symbol': 'GOOGL',
            'company_name': 'Alphabet Inc',
            'threshold': 4
        }
        percentage_change = 5.0
        articles = []

        report = main.generate_stock_report(stock_info, percentage_change, articles)

        assert 'GOOGL' in report
        assert 'No se encontraron noticias recientes' in report

    def test_generate_stock_report_multiple_news(self):
        """Test report generation with multiple news articles"""
        stock_info = {
            'symbol': 'MSFT',
            'company_name': 'Microsoft',
            'threshold': 3
        }
        percentage_change = 4.5
        articles = [
            {'title': 'News 1', 'description': 'Desc 1', 'url': 'https://example.com/1'},
            {'title': 'News 2', 'description': 'Desc 2', 'url': 'https://example.com/2'},
            {'title': 'News 3', 'description': 'Desc 3', 'url': 'https://example.com/3'},
            {'title': 'News 4', 'description': 'Desc 4', 'url': 'https://example.com/4'}
        ]

        report = main.generate_stock_report(stock_info, percentage_change, articles)

        # Should only include first 3 articles
        assert 'News 1' in report
        assert 'News 2' in report
        assert 'News 3' in report
        assert 'News 4' not in report


class TestSendAlertMessage:
    """Tests for send_alert_message function"""

    @patch('main.Client')
    @patch('main.TWILIO_ACCOUNT_SID', 'test_sid')
    @patch('main.TWILIO_AUTH_TOKEN', 'test_token')
    @patch('main.TWILIO_PHONE_NUMBER', '+1234567890')
    @patch('main.MY_PHONE_NUMBER', '+0987654321')
    def test_send_alert_message_whatsapp_success(self, mock_client_class):
        """Test successful WhatsApp message sending"""
        # Mock Twilio client
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM123456789"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        # Set WhatsApp mode
        with patch('main.USE_WHATSAPP', True):
            result = main.send_alert_message("Test alert message")

        assert result is True
        mock_client.messages.create.assert_called_once()

    @patch('main.Client')
    @patch('main.TWILIO_ACCOUNT_SID', 'test_sid')
    @patch('main.TWILIO_AUTH_TOKEN', 'test_token')
    @patch('main.TWILIO_PHONE_NUMBER', '+1234567890')
    @patch('main.MY_PHONE_NUMBER', '+0987654321')
    def test_send_alert_message_sms_success(self, mock_client_class):
        """Test successful SMS message sending"""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM987654321"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        with patch('main.USE_WHATSAPP', False):
            result = main.send_alert_message("Test SMS message")

        assert result is True

    def test_send_alert_message_no_credentials(self):
        """Test message sending without credentials"""
        with patch('main.TWILIO_ACCOUNT_SID', None):
            result = main.send_alert_message("Test message")
            assert result is False

    @patch('main.Client')
    @patch('main.TWILIO_ACCOUNT_SID', 'test_sid')
    @patch('main.TWILIO_AUTH_TOKEN', 'test_token')
    def test_send_alert_message_error(self, mock_client_class):
        """Test handling of Twilio errors"""
        mock_client_class.side_effect = Exception("Twilio error")

        result = main.send_alert_message("Test message")
        assert result is False
