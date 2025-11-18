"""
Configuration module for Stock Price Alert App.

Centralizes all configuration values and environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration class."""

    # API Keys
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

    # Twilio Credentials
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER")

    # Application Settings
    USE_WHATSAPP = True  # True for WhatsApp, False for SMS
    STOCKS_CSV_FILE = "stocks.csv"
    LOG_DIR = "logs"

    # Database Settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///stock_monitor.db")
    DATABASE_ECHO = False  # Set to True for SQL query debugging

    # API Endpoints
    ALPHA_VANTAGE_ENDPOINT = "https://www.alphavantage.co/query"
    NEWS_API_ENDPOINT = "https://newsapi.org/v2/everything"
    UNSPLASH_API_ENDPOINT = "https://api.unsplash.com"

    # Request Settings
    API_TIMEOUT = 10  # seconds
    REQUEST_DELAY = 1  # seconds between API calls

    # Logging Settings
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5
    LOG_FORMAT_FILE = '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s'
    LOG_FORMAT_CONSOLE = '%(levelname)-8s | %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


# Create a singleton instance
config = Config()
