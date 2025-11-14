"""Tests for src.utils module."""

import os
import sys
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import load_stocks_from_csv, generate_stock_report


class TestLoadStocksFromCSV:
    """Tests for load_stocks_from_csv function."""

    def test_load_stocks_success(self, tmp_path):
        """Test successful loading of stocks from CSV."""
        csv_file = tmp_path / "test_stocks.csv"
        csv_content = """symbol,company_name,threshold
TSLA,Tesla Inc,5
AAPL,Apple Inc,3
GOOGL,Alphabet Inc,4"""
        csv_file.write_text(csv_content)

        stocks = load_stocks_from_csv(str(csv_file))

        assert len(stocks) == 3
        assert stocks[0]['symbol'] == 'TSLA'
        assert stocks[0]['company_name'] == 'Tesla Inc'
        assert stocks[0]['threshold'] == 5.0
        assert stocks[1]['symbol'] == 'AAPL'
        assert stocks[2]['symbol'] == 'GOOGL'

    def test_load_stocks_file_not_found(self):
        """Test loading stocks from non-existent file."""
        stocks = load_stocks_from_csv("non_existent_file.csv")
        assert stocks == []

    def test_load_stocks_empty_file(self, tmp_path):
        """Test loading stocks from empty CSV file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("symbol,company_name,threshold\n")

        stocks = load_stocks_from_csv(str(csv_file))
        assert stocks == []

    def test_load_stocks_with_whitespace(self, tmp_path):
        """Test that whitespace is properly stripped."""
        csv_file = tmp_path / "whitespace.csv"
        csv_content = """symbol,company_name,threshold
  TSLA  ,  Tesla Inc  ,  5  """
        csv_file.write_text(csv_content)

        stocks = load_stocks_from_csv(str(csv_file))
        assert stocks[0]['symbol'] == 'TSLA'
        assert stocks[0]['company_name'] == 'Tesla Inc'


class TestGenerateStockReport:
    """Tests for generate_stock_report function."""

    def test_generate_stock_report_with_news(self):
        """Test report generation with news articles."""
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

        report = generate_stock_report(stock_info, percentage_change, articles)

        assert 'TSLA' in report
        assert 'Tesla Inc' in report
        assert '6.50%' in report
        assert '5%' in report
        assert 'Tesla Hits New High' in report
        assert 'https://example.com/1' in report
        assert '🔺' in report

    def test_generate_stock_report_negative_change(self):
        """Test report generation with negative change."""
        stock_info = {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc',
            'threshold': 3
        }
        percentage_change = -4.2
        articles = []

        report = generate_stock_report(stock_info, percentage_change, articles)

        assert 'AAPL' in report
        assert '4.20%' in report
        assert '🔻' in report

    def test_generate_stock_report_no_news(self):
        """Test report generation without news articles."""
        stock_info = {
            'symbol': 'GOOGL',
            'company_name': 'Alphabet Inc',
            'threshold': 4
        }
        percentage_change = 5.0
        articles = []

        report = generate_stock_report(stock_info, percentage_change, articles)

        assert 'GOOGL' in report
        assert 'No se encontraron noticias recientes' in report

    def test_generate_stock_report_multiple_news(self):
        """Test report generation with multiple news articles."""
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

        report = generate_stock_report(stock_info, percentage_change, articles)

        assert 'News 1' in report
        assert 'News 2' in report
        assert 'News 3' in report
        assert 'News 4' not in report
