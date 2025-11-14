"""
Database package.

Contiene los modelos SQLAlchemy y servicios para persistencia de datos.
"""

from .models import Stock, PriceHistory, Alert, NewsArticle
from .service import DatabaseService

__all__ = [
    'Stock',
    'PriceHistory',
    'Alert',
    'NewsArticle',
    'DatabaseService',
]
