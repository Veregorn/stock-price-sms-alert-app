"""
Tests para modelos y servicios de base de datos.

Cubre:
- Modelos SQLAlchemy (Stock, PriceHistory, Alert, NewsArticle)
- DatabaseService (operaciones CRUD completas)
- Manejo de sesiones y transacciones
"""

import pytest
from datetime import datetime, timedelta
from src.database import DatabaseService, Stock, PriceHistory, Alert, NewsArticle


# =========================================================================
# FIXTURES
# =========================================================================

@pytest.fixture
def db_service():
    """
    Fixture que proporciona un DatabaseService con BD en memoria.

    Se crea una nueva BD para cada test y se limpia automáticamente.
    """
    # Crear servicio con BD en memoria
    service = DatabaseService(database_url='sqlite:///:memory:')

    # Crear tablas
    service.create_tables()

    # Proporcionar el servicio al test
    yield service

    # Cleanup: cerrar conexión
    service.close()


@pytest.fixture
def sample_stock(db_service):
    """Fixture que proporciona un stock de ejemplo."""
    return db_service.create_stock('TSLA', 'Tesla Inc', 5.0)


@pytest.fixture
def multiple_stocks(db_service):
    """Fixture que proporciona varios stocks de ejemplo."""
    stocks = [
        db_service.create_stock('TSLA', 'Tesla Inc', 5.0),
        db_service.create_stock('AAPL', 'Apple Inc', 3.0),
        db_service.create_stock('GOOGL', 'Alphabet Inc', 4.0, is_active=False),
    ]
    return stocks


# =========================================================================
# TESTS DE MODELOS
# =========================================================================

class TestModels:
    """Tests para verificar los modelos SQLAlchemy."""

    def test_stock_creation(self, db_service):
        """Verifica que se puede crear un Stock correctamente."""
        stock = db_service.create_stock('TSLA', 'Tesla Inc', 5.0)

        assert stock.id is not None
        assert stock.symbol == 'TSLA'
        assert stock.company_name == 'Tesla Inc'
        assert stock.threshold == 5.0
        assert stock.is_active is True
        assert stock.created_at is not None
        assert stock.updated_at is not None

    def test_stock_representation(self, sample_stock):
        """Verifica la representación en string del Stock."""
        repr_str = repr(sample_stock)
        assert 'TSLA' in repr_str
        assert 'Tesla Inc' in repr_str
        assert '5.0' in repr_str

    def test_price_history_creation(self, db_service, sample_stock):
        """Verifica que se puede crear un PriceHistory correctamente."""
        now = datetime.utcnow()
        price = db_service.add_price_history(
            'TSLA',
            now,
            250.00,
            previous_close=240.00,
            percentage_change=4.17
        )

        assert price.id is not None
        assert price.stock_id == sample_stock.id
        assert price.close_price == 250.00
        assert price.previous_close == 240.00
        assert price.percentage_change == 4.17
        assert price.created_at is not None

    def test_price_history_representation(self, db_service, sample_stock):
        """Verifica la representación en string del PriceHistory."""
        price = db_service.add_price_history('TSLA', datetime.utcnow(), 250.00)
        repr_str = repr(price)
        assert 'PriceHistory' in repr_str
        assert '250.00' in repr_str

    def test_alert_creation(self, db_service, sample_stock):
        """Verifica que se puede crear una Alert correctamente."""
        alert = db_service.create_alert(
            'TSLA',
            percentage_change=4.17,
            threshold_at_time=5.0,
            price_before=240.00,
            price_after=250.00,
            message_sent=True,
            notification_type='whatsapp'
        )

        assert alert.id is not None
        assert alert.stock_id == sample_stock.id
        assert alert.percentage_change == 4.17
        assert alert.threshold_at_time == 5.0
        assert alert.message_sent is True
        assert alert.notification_type == 'whatsapp'
        assert alert.triggered_at is not None

    def test_alert_representation(self, db_service, sample_stock):
        """Verifica la representación en string de Alert."""
        alert = db_service.create_alert('TSLA', 4.17, 5.0, message_sent=True)
        repr_str = repr(alert)
        assert 'Alert' in repr_str
        assert '4.17' in repr_str

    def test_news_article_creation(self, db_service, sample_stock):
        """Verifica que se puede crear un NewsArticle correctamente."""
        article = db_service.save_news_article(
            'TSLA',
            'Tesla Stock Surges',
            description='Tesla shares reached new highs',
            url='https://example.com/news',
            published_at=datetime.utcnow()
        )

        assert article.id is not None
        assert article.stock_id == sample_stock.id
        assert article.title == 'Tesla Stock Surges'
        assert article.description == 'Tesla shares reached new highs'
        assert article.url == 'https://example.com/news'
        assert article.fetched_at is not None

    def test_news_article_representation(self, db_service, sample_stock):
        """Verifica la representación en string de NewsArticle."""
        article = db_service.save_news_article('TSLA', 'Tesla Stock Surges')
        repr_str = repr(article)
        assert 'NewsArticle' in repr_str
        assert 'Tesla Stock Surges' in repr_str


# =========================================================================
# TESTS DE DATABASE SERVICE - STOCK CRUD
# =========================================================================

class TestStockCRUD:
    """Tests para operaciones CRUD de Stock."""

    def test_create_stock(self, db_service):
        """Verifica la creación de un stock."""
        stock = db_service.create_stock('AAPL', 'Apple Inc', 3.0)

        assert stock is not None
        assert stock.symbol == 'AAPL'
        assert stock.company_name == 'Apple Inc'
        assert stock.threshold == 3.0
        assert stock.is_active is True

    def test_create_stock_normalizes_symbol(self, db_service):
        """Verifica que el símbolo se normaliza a mayúsculas."""
        stock = db_service.create_stock('tsla', 'Tesla Inc', 5.0)
        assert stock.symbol == 'TSLA'

    def test_get_stock_by_symbol(self, db_service, sample_stock):
        """Verifica obtener un stock por su símbolo."""
        stock = db_service.get_stock_by_symbol('TSLA')

        assert stock is not None
        assert stock.id == sample_stock.id
        assert stock.symbol == 'TSLA'

    def test_get_stock_by_symbol_case_insensitive(self, db_service, sample_stock):
        """Verifica que la búsqueda es case-insensitive."""
        stock = db_service.get_stock_by_symbol('tsla')
        assert stock is not None
        assert stock.symbol == 'TSLA'

    def test_get_stock_by_symbol_not_found(self, db_service):
        """Verifica que devuelve None si el stock no existe."""
        stock = db_service.get_stock_by_symbol('NOTEXIST')
        assert stock is None

    def test_get_all_stocks(self, db_service, multiple_stocks):
        """Verifica obtener todos los stocks."""
        stocks = db_service.get_all_stocks()

        assert len(stocks) == 3
        # Verificar orden alfabético
        assert stocks[0].symbol == 'AAPL'
        assert stocks[1].symbol == 'GOOGL'
        assert stocks[2].symbol == 'TSLA'

    def test_get_all_stocks_only_active(self, db_service, multiple_stocks):
        """Verifica filtrar solo stocks activos."""
        active_stocks = db_service.get_all_stocks(only_active=True)

        assert len(active_stocks) == 2
        assert all(stock.is_active for stock in active_stocks)

    def test_update_stock(self, db_service, sample_stock):
        """Verifica actualizar un stock."""
        updated = db_service.update_stock('TSLA', threshold=6.0, is_active=False)

        assert updated is not None
        assert updated.threshold == 6.0
        assert updated.is_active is False

    def test_update_stock_not_found(self, db_service):
        """Verifica que devuelve None si el stock no existe."""
        result = db_service.update_stock('NOTEXIST', threshold=5.0)
        assert result is None

    def test_delete_stock(self, db_service, sample_stock):
        """Verifica eliminar un stock."""
        result = db_service.delete_stock('TSLA')

        assert result is True
        # Verificar que ya no existe
        stock = db_service.get_stock_by_symbol('TSLA')
        assert stock is None

    def test_delete_stock_not_found(self, db_service):
        """Verifica que devuelve False si el stock no existe."""
        result = db_service.delete_stock('NOTEXIST')
        assert result is False

    def test_delete_stock_cascades(self, db_service, sample_stock):
        """Verifica que eliminar un stock elimina datos relacionados."""
        # Crear datos relacionados
        db_service.add_price_history('TSLA', datetime.utcnow(), 250.00)
        db_service.create_alert('TSLA', 4.17, 5.0)
        db_service.save_news_article('TSLA', 'Test News')

        # Eliminar stock
        db_service.delete_stock('TSLA')

        # Verificar que los datos relacionados también se eliminaron
        prices = db_service.get_price_history('TSLA')
        alerts = db_service.get_recent_alerts(symbol='TSLA')
        news = db_service.get_news_for_stock('TSLA')

        assert len(prices) == 0
        assert len(alerts) == 0
        assert len(news) == 0


# =========================================================================
# TESTS DE PRICE HISTORY
# =========================================================================

class TestPriceHistory:
    """Tests para operaciones de PriceHistory."""

    def test_add_price_history(self, db_service, sample_stock):
        """Verifica añadir precio histórico."""
        now = datetime.utcnow()
        price = db_service.add_price_history(
            'TSLA',
            now,
            250.00,
            previous_close=240.00,
            percentage_change=4.17
        )

        assert price is not None
        assert price.stock_id == sample_stock.id
        assert price.close_price == 250.00

    def test_add_price_history_nonexistent_stock(self, db_service):
        """Verifica que devuelve None si el stock no existe."""
        price = db_service.add_price_history('NOTEXIST', datetime.utcnow(), 250.00)
        assert price is None

    def test_get_price_history(self, db_service, sample_stock):
        """Verifica obtener histórico de precios."""
        now = datetime.utcnow()

        # Añadir varios precios
        db_service.add_price_history('TSLA', now - timedelta(days=2), 240.00)
        db_service.add_price_history('TSLA', now - timedelta(days=1), 245.00)
        db_service.add_price_history('TSLA', now, 250.00)

        # Obtener histórico
        prices = db_service.get_price_history('TSLA', days=30)

        assert len(prices) == 3
        # Verificar orden (más reciente primero)
        assert prices[0].close_price == 250.00
        assert prices[1].close_price == 245.00
        assert prices[2].close_price == 240.00

    def test_get_price_history_with_limit(self, db_service, sample_stock):
        """Verifica filtrado por días."""
        now = datetime.utcnow()

        # Añadir precios antiguos y recientes
        db_service.add_price_history('TSLA', now - timedelta(days=40), 200.00)
        db_service.add_price_history('TSLA', now - timedelta(days=1), 250.00)

        # Obtener solo últimos 30 días
        prices = db_service.get_price_history('TSLA', days=30)

        assert len(prices) == 1
        assert prices[0].close_price == 250.00

    def test_get_price_history_nonexistent_stock(self, db_service):
        """Verifica que devuelve lista vacía si el stock no existe."""
        prices = db_service.get_price_history('NOTEXIST')
        assert prices == []


# =========================================================================
# TESTS DE ALERTS
# =========================================================================

class TestAlerts:
    """Tests para operaciones de Alert."""

    def test_create_alert(self, db_service, sample_stock):
        """Verifica crear una alerta."""
        alert = db_service.create_alert(
            'TSLA',
            percentage_change=4.17,
            threshold_at_time=5.0,
            price_before=240.00,
            price_after=250.00,
            message_sent=True
        )

        assert alert is not None
        assert alert.stock_id == sample_stock.id
        assert alert.percentage_change == 4.17

    def test_create_alert_nonexistent_stock(self, db_service):
        """Verifica que devuelve None si el stock no existe."""
        alert = db_service.create_alert('NOTEXIST', 4.17, 5.0)
        assert alert is None

    def test_get_recent_alerts(self, db_service, sample_stock):
        """Verifica obtener alertas recientes."""
        # Crear alertas
        db_service.create_alert('TSLA', 4.17, 5.0)
        db_service.create_alert('TSLA', 3.5, 5.0)

        # Obtener alertas
        alerts = db_service.get_recent_alerts(days=7)

        assert len(alerts) == 2

    def test_get_recent_alerts_filtered_by_symbol(self, db_service):
        """Verifica filtrar alertas por símbolo."""
        # Crear stocks y alertas
        db_service.create_stock('TSLA', 'Tesla Inc', 5.0)
        db_service.create_stock('AAPL', 'Apple Inc', 3.0)

        db_service.create_alert('TSLA', 4.17, 5.0)
        db_service.create_alert('AAPL', 3.2, 3.0)

        # Filtrar por TSLA
        tsla_alerts = db_service.get_recent_alerts(symbol='TSLA', days=7)

        assert len(tsla_alerts) == 1

    def test_get_recent_alerts_with_time_limit(self, db_service, sample_stock):
        """Verifica filtrado por tiempo."""
        # Crear alerta antigua (simulada modificando created_at sería complejo,
        # así que este test verifica que el método funciona con el parámetro days)
        db_service.create_alert('TSLA', 4.17, 5.0)

        # Obtener alertas del último día
        alerts = db_service.get_recent_alerts(days=1)

        assert len(alerts) == 1


# =========================================================================
# TESTS DE NEWS ARTICLES
# =========================================================================

class TestNewsArticles:
    """Tests para operaciones de NewsArticle."""

    def test_save_news_article(self, db_service, sample_stock):
        """Verifica guardar una noticia."""
        article = db_service.save_news_article(
            'TSLA',
            'Tesla Stock Surges',
            description='Tesla shares reached new highs',
            url='https://example.com/news'
        )

        assert article is not None
        assert article.stock_id == sample_stock.id
        assert article.title == 'Tesla Stock Surges'

    def test_save_news_article_nonexistent_stock(self, db_service):
        """Verifica que devuelve None si el stock no existe."""
        article = db_service.save_news_article('NOTEXIST', 'Test News')
        assert article is None

    def test_get_news_for_stock(self, db_service, sample_stock):
        """Verifica obtener noticias de un stock."""
        # Guardar varias noticias
        db_service.save_news_article('TSLA', 'News 1')
        db_service.save_news_article('TSLA', 'News 2')
        db_service.save_news_article('TSLA', 'News 3')

        # Obtener noticias
        news = db_service.get_news_for_stock('TSLA', limit=10)

        assert len(news) == 3

    def test_get_news_for_stock_with_limit(self, db_service, sample_stock):
        """Verifica límite de noticias."""
        # Guardar muchas noticias
        for i in range(5):
            db_service.save_news_article('TSLA', f'News {i}')

        # Obtener solo 2
        news = db_service.get_news_for_stock('TSLA', limit=2)

        assert len(news) == 2

    def test_get_news_for_nonexistent_stock(self, db_service):
        """Verifica que devuelve lista vacía si el stock no existe."""
        news = db_service.get_news_for_stock('NOTEXIST')
        assert news == []


# =========================================================================
# TESTS DE UTILIDADES
# =========================================================================

class TestDashboardSummary:
    """Tests para get_dashboard_summary."""

    def test_dashboard_summary_empty(self, db_service):
        """Verifica resumen con base de datos vacía."""
        summary = db_service.get_dashboard_summary()

        assert summary['total_stocks'] == 0
        assert summary['active_stocks'] == 0
        assert summary['recent_alerts_24h'] == 0
        assert summary['last_price_update'] is None

    def test_dashboard_summary_with_data(self, db_service):
        """Verifica resumen con datos."""
        # Crear stocks
        db_service.create_stock('TSLA', 'Tesla Inc', 5.0)
        db_service.create_stock('AAPL', 'Apple Inc', 3.0, is_active=False)

        # Crear alerta
        db_service.create_alert('TSLA', 4.17, 5.0)

        # Crear precio
        db_service.add_price_history('TSLA', datetime.utcnow(), 250.00)

        # Obtener resumen
        summary = db_service.get_dashboard_summary()

        assert summary['total_stocks'] == 2
        assert summary['active_stocks'] == 1
        assert summary['recent_alerts_24h'] == 1
        assert summary['last_price_update'] is not None


# =========================================================================
# TESTS DE MANEJO DE SESIONES
# =========================================================================

class TestSessionManagement:
    """Tests para verificar el manejo correcto de sesiones."""

    def test_session_context_manager(self, db_service):
        """Verifica que el context manager funciona correctamente."""
        with db_service.get_session() as session:
            # Crear un stock dentro de la sesión
            stock = Stock(symbol='TEST', company_name='Test Inc', threshold=5.0)
            session.add(stock)
            # No hacer commit manualmente, el context manager lo hace

        # Verificar que se guardó
        retrieved = db_service.get_stock_by_symbol('TEST')
        assert retrieved is not None

    def test_session_rollback_on_error(self, db_service):
        """Verifica que la sesión hace rollback en caso de error."""
        try:
            with db_service.get_session() as session:
                stock = Stock(symbol='TEST', company_name='Test Inc', threshold=5.0)
                session.add(stock)
                # Forzar un error
                raise ValueError("Test error")
        except ValueError:
            pass

        # Verificar que NO se guardó (rollback)
        retrieved = db_service.get_stock_by_symbol('TEST')
        assert retrieved is None

    def test_objects_usable_outside_session(self, db_service, sample_stock):
        """Verifica que los objetos son usables fuera de la sesión (expunge)."""
        # El objeto ya fue creado y expunged por la fixture
        # Verificar que podemos acceder a sus atributos
        assert sample_stock.symbol == 'TSLA'
        assert sample_stock.company_name == 'Tesla Inc'
        assert sample_stock.threshold == 5.0
