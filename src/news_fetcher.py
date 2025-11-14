"""
News fetching module.

Handles all interactions with the News API for financial news articles.
"""

import logging
import requests
from typing import List, Dict, Optional

from .config import config

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetches news articles from News API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NewsFetcher.

        Args:
            api_key: News API key. If None, uses config value.
        """
        self.api_key = api_key or config.NEWS_API_KEY
        self.endpoint = config.NEWS_API_ENDPOINT
        self.timeout = config.API_TIMEOUT

    def get_articles(
        self, company_name: str, limit: int = 3
    ) -> List[Dict[str, str]]:
        """
        Get the most recent news articles about a company.

        Args:
            company_name: Name of the company
            limit: Number of articles to retrieve

        Returns:
            List of article dictionaries with keys: title, description, url
        """
        logger.debug(f"Fetching news for {company_name}")

        parameters = {
            "q": company_name,
            "sortBy": "publishedAt",
            "apiKey": self.api_key,
            "language": "en",
            "pageSize": limit
        }

        try:
            response = requests.get(
                self.endpoint,
                params=parameters,
                timeout=self.timeout
            )
            response.raise_for_status()
            news_data = response.json()

            if news_data.get("status") == "ok":
                articles = news_data.get("articles", [])
                logger.info(f"Found {len(articles)} news articles for {company_name}")
                return articles
            else:
                logger.warning(
                    f"News API returned non-ok status for {company_name}: "
                    f"{news_data.get('message')}"
                )
                return []

        except Exception as e:
            logger.error(
                f"Error fetching news for {company_name}: {str(e)}",
                exc_info=True
            )
            return []
