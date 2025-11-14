"""Tests for src.news_fetcher module."""

import os
import sys
import pytest
from unittest.mock import Mock, patch
import requests

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.news_fetcher import NewsFetcher


class TestNewsFetcher:
    """Tests for NewsFetcher class."""

    @pytest.fixture
    def news_fetcher(self):
        """Create a NewsFetcher instance for testing."""
        return NewsFetcher(api_key='test_api_key')

    def test_init_with_api_key(self):
        """Test initialization with provided API key."""
        fetcher = NewsFetcher(api_key='custom_key')
        assert fetcher.api_key == 'custom_key'

    @patch('src.news_fetcher.config')
    def test_init_without_api_key(self, mock_config):
        """Test initialization without API key uses config."""
        mock_config.NEWS_API_KEY = 'config_key'
        fetcher = NewsFetcher()
        assert fetcher.api_key == 'config_key'

    @patch('src.news_fetcher.requests.get')
    def test_get_articles_success(self, mock_get, news_fetcher):
        """Test successful news article retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Tesla Hits New High",
                    "description": "Tesla stock reaches record levels",
                    "url": "https://example.com/1"
                },
                {
                    "title": "Tesla Expands Production",
                    "description": "New factory opens",
                    "url": "https://example.com/2"
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        articles = news_fetcher.get_articles('Tesla Inc', limit=3)

        assert len(articles) == 2
        assert articles[0]['title'] == "Tesla Hits New High"
        assert articles[0]['description'] == "Tesla stock reaches record levels"
        assert articles[0]['url'] == "https://example.com/1"

    @patch('src.news_fetcher.requests.get')
    def test_get_articles_empty_result(self, mock_get, news_fetcher):
        """Test when API returns no articles."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": []
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        articles = news_fetcher.get_articles('Unknown Company')

        assert articles == []

    @patch('src.news_fetcher.requests.get')
    def test_get_articles_non_ok_status(self, mock_get, news_fetcher):
        """Test when API returns non-ok status."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "error",
            "message": "API key invalid"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        articles = news_fetcher.get_articles('Tesla Inc')

        assert articles == []

    @patch('src.news_fetcher.requests.get')
    def test_get_articles_timeout(self, mock_get, news_fetcher):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()

        articles = news_fetcher.get_articles('Tesla Inc')

        assert articles == []

    @patch('src.news_fetcher.requests.get')
    def test_get_articles_request_error(self, mock_get, news_fetcher):
        """Test handling of request errors."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        articles = news_fetcher.get_articles('Tesla Inc')

        assert articles == []

    @patch('src.news_fetcher.requests.get')
    def test_get_articles_http_error(self, mock_get, news_fetcher):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_response

        articles = news_fetcher.get_articles('Tesla Inc')

        assert articles == []

    @patch('src.news_fetcher.requests.get')
    def test_get_articles_limit_parameter(self, mock_get, news_fetcher):
        """Test that limit parameter is passed correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [{"title": "News 1", "description": "Desc 1", "url": "url1"}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        news_fetcher.get_articles('Tesla Inc', limit=5)

        # Verify the API was called with correct pageSize parameter
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['params']['pageSize'] == 5

    @patch('src.news_fetcher.requests.get')
    def test_get_articles_with_company_name(self, mock_get, news_fetcher):
        """Test that company name is passed correctly in query."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": []
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        news_fetcher.get_articles('Apple Inc', limit=3)

        # Verify the API was called with correct company name
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['params']['q'] == 'Apple Inc'
