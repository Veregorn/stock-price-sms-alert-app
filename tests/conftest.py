"""
Configuración de fixtures de pytest para todos los tests.

Este módulo contiene fixtures compartidas que pueden ser utilizadas
por todos los tests del proyecto. Las fixtures proporcionan:
- Cliente de prueba de FastAPI
- Base de datos de prueba
- Datos de ejemplo (stocks, precios, etc.)
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from src.api.main import app
from src.database import DatabaseService


# =============================================================================
# FIXTURES DE INFRAESTRUCTURA
# =============================================================================

@pytest.fixture
def client():
    """
    Cliente de prueba de FastAPI.

    Proporciona un TestClient configurado para hacer peticiones HTTP
    a la API sin necesidad de levantar un servidor real.
    """
    return TestClient(app)


@pytest.fixture
def db():
    """
    Servicio de base de datos para tests.

    Proporciona una instancia de DatabaseService que puede ser
    usada para setup de datos o verificación de estado.
    """
    return DatabaseService()


# =============================================================================
# FIXTURES DE DATOS - STOCKS
# =============================================================================

@pytest.fixture
def sample_stock_data():
    """Datos de ejemplo para crear un stock."""
    return {
        "symbol": "TSLA",
        "company_name": "Tesla Inc",
        "threshold": 5.0,
        "is_active": True
    }


@pytest.fixture
def sample_stock(db):
    """
    Crea un stock de prueba en la base de datos.

    Este stock se puede usar en tests que requieren datos existentes.
    Retorna el objeto Stock creado.
    """
    stock = db.get_stock_by_symbol("TSLA")
    if not stock:
        stock = db.create_stock(
            symbol="TSLA",
            company_name="Tesla Inc",
            threshold=5.0
        )
    return stock


@pytest.fixture
def multiple_stocks(db):
    """
    Crea múltiples stocks de prueba.

    Retorna una lista de stocks para tests que necesitan
    varios registros.
    """
    stocks_data = [
        ("TSLA", "Tesla Inc", 5.0, True),
        ("AAPL", "Apple Inc", 3.0, True),
        ("GOOGL", "Alphabet Inc", 4.0, False),
    ]

    stocks = []
    for symbol, name, threshold, is_active in stocks_data:
        stock = db.get_stock_by_symbol(symbol)
        if not stock:
            stock = db.create_stock(
                symbol=symbol,
                company_name=name,
                threshold=threshold
            )
            if not is_active:
                db.toggle_stock_active(symbol)
        stocks.append(stock)

    return stocks


# =============================================================================
# FIXTURES DE DATOS - PRECIOS
# =============================================================================

@pytest.fixture
def sample_price_data():
    """Datos de ejemplo para crear un precio."""
    return {
        "date": datetime.now().isoformat(),
        "close_price": 250.75
    }


@pytest.fixture
def sample_prices(db, sample_stock):
    """
    Crea un histórico de precios para un stock.

    Genera precios de los últimos 7 días con variaciones.
    Útil para tests de histórico y cálculos.
    """
    prices = []
    base_price = 250.0

    for i in range(7):
        date = datetime.now() - timedelta(days=6-i)
        price = base_price + (i * 5)  # Incremento gradual

        db.add_price_history(
            symbol="TSLA",
            date=date,
            close_price=price
        )

    # Obtener los precios creados
    prices = db.get_price_history("TSLA", days=7)
    return prices


# =============================================================================
# FIXTURES DE DATOS - NOTICIAS
# =============================================================================

@pytest.fixture
def sample_news_data():
    """Datos de ejemplo para crear una noticia."""
    return {
        "title": "Tesla anuncia nuevo modelo de vehículo eléctrico",
        "description": "Tesla ha anunciado un nuevo modelo revolucionario.",
        "url": "https://example.com/tesla-news",
        "published_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_news(db, sample_stock):
    """
    Crea noticias de prueba para un stock.

    Genera 3 noticias de ejemplo.
    """
    news_items = []

    for i in range(3):
        article = db.save_news_article(
            symbol="TSLA",
            title=f"Noticia de prueba {i+1}",
            description=f"Descripción de la noticia {i+1}",
            url=f"https://example.com/news-{i+1}"
        )
        news_items.append(article)

    return news_items


# =============================================================================
# FIXTURES DE CLEANUP
# =============================================================================

@pytest.fixture
def clean_db(db):
    """
    Limpia la base de datos antes y después de cada test.

    ADVERTENCIA: Esto eliminará TODOS los datos de la base de datos.
    Solo usar en entornos de test.
    """
    # Cleanup antes del test
    # (Aquí podrías añadir lógica de limpieza si fuera necesario)

    yield db

    # Cleanup después del test
    # (Opcional: limpiar datos creados durante el test)


# =============================================================================
# FIXTURES DE HELPERS
# =============================================================================

@pytest.fixture
def auth_headers():
    """
    Headers de autenticación para tests (placeholder).

    En el futuro, cuando se implemente autenticación,
    esta fixture proporcionará los headers necesarios.
    """
    return {}


@pytest.fixture
def invalid_symbol():
    """Símbolo de stock que no existe, útil para tests de 404."""
    return "NONEXISTENT"
