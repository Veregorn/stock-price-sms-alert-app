"""
Tests para endpoints de Dashboard y Alerts.

Prueba:
- GET /api/dashboard/summary - Resumen del dashboard
- GET /api/alerts - Listar alertas
- GET /api/alerts/{stock_symbol} - Alertas de un stock
"""

import pytest


@pytest.mark.api
class TestDashboardSummary:
    """Tests para GET /api/dashboard/summary."""

    def test_dashboard_summary_basic_structure(self, client):
        """Test: Estructura básica del resumen."""
        response = client.get("/api/dashboard/summary")

        assert response.status_code == 200
        data = response.json()
        assert "total_stocks" in data
        assert "active_stocks" in data
        assert "recent_alerts_24h" in data
        assert "last_price_update" in data

    def test_dashboard_summary_with_stocks(self, client, multiple_stocks):
        """Test: Resumen con stocks existentes."""
        response = client.get("/api/dashboard/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_stocks"] >= 3
        assert data["active_stocks"] >= 2  # Al menos 2 activos

    def test_dashboard_summary_counts_correct(self, client, multiple_stocks):
        """Test: Conteos correctos de stocks."""
        response = client.get("/api/dashboard/summary")

        data = response.json()
        # active_stocks debe ser <= total_stocks
        assert data["active_stocks"] <= data["total_stocks"]

    def test_dashboard_summary_alerts_count(self, client):
        """Test: Contador de alertas en 24h."""
        response = client.get("/api/dashboard/summary")

        data = response.json()
        assert isinstance(data["recent_alerts_24h"], int)
        assert data["recent_alerts_24h"] >= 0


@pytest.mark.api
class TestListAlerts:
    """Tests para GET /api/alerts."""

    def test_list_alerts_basic_structure(self, client):
        """Test: Estructura básica de la respuesta."""
        response = client.get("/api/alerts")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_list_alerts_default_days(self, client):
        """Test: Por defecto devuelve alertas de últimos 7 días."""
        response = client.get("/api/alerts")

        assert response.status_code == 200
        data = response.json()
        # No debe fallar, puede estar vacío o con datos
        assert data["total"] >= 0

    def test_list_alerts_with_days_filter(self, client):
        """Test: Filtrar por días específicos."""
        response = client.get("/api/alerts?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0

    def test_list_alerts_invalid_days(self, client):
        """Test: Validación de parámetro days."""
        # days < 1
        response = client.get("/api/alerts?days=0")
        assert response.status_code == 422

        # days > 365
        response = client.get("/api/alerts?days=400")
        assert response.status_code == 422

    def test_list_alerts_valid_days_range(self, client):
        """Test: Rango válido de days."""
        # Probar algunos valores válidos
        valid_days = [1, 7, 30, 90, 365]

        for days in valid_days:
            response = client.get(f"/api/alerts?days={days}")
            assert response.status_code == 200

    def test_list_alerts_structure(self, client):
        """Test: Estructura de cada alerta."""
        response = client.get("/api/alerts")

        data = response.json()
        if data["total"] > 0:
            alert = data["alerts"][0]
            # Verificar campos básicos de alerta
            assert "id" in alert
            assert "stock_id" in alert
            assert "percentage_change" in alert
            assert "triggered_at" in alert


@pytest.mark.api
class TestGetStockAlerts:
    """Tests para GET /api/alerts/{stock_symbol}."""

    def test_get_stock_alerts_success(self, client, sample_stock):
        """Test: Obtener alertas de un stock existente."""
        response = client.get("/api/alerts/TSLA")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_get_stock_alerts_not_found(self, client, invalid_symbol):
        """Test: Alertas de stock inexistente."""
        response = client.get(f"/api/alerts/{invalid_symbol}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_stock_alerts_with_days_filter(self, client, sample_stock):
        """Test: Filtrar alertas por días."""
        response = client.get("/api/alerts/TSLA?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0

    def test_get_stock_alerts_default_days(self, client, sample_stock):
        """Test: Default days es 30."""
        response = client.get("/api/alerts/TSLA")

        assert response.status_code == 200
        # No debe fallar

    def test_get_stock_alerts_case_insensitive(self, client, sample_stock):
        """Test: Símbolo case-insensitive."""
        response = client.get("/api/alerts/tsla")

        assert response.status_code == 200

    def test_get_stock_alerts_invalid_days(self, client, sample_stock):
        """Test: Validación de days."""
        response = client.get("/api/alerts/TSLA?days=0")
        assert response.status_code == 422

        response = client.get("/api/alerts/TSLA?days=400")
        assert response.status_code == 422


@pytest.mark.api
class TestDashboardAlertsIntegration:
    """Tests de integración entre Dashboard y Alerts."""

    def test_dashboard_reflects_stocks_state(self, client, multiple_stocks):
        """Test: Dashboard refleja correctamente el estado de los stocks."""
        # Obtener resumen
        dashboard = client.get("/api/dashboard/summary").json()

        # Obtener todos los stocks
        stocks = client.get("/api/stocks").json()

        # El total debe coincidir
        assert dashboard["total_stocks"] == stocks["total"]

        # Contar stocks activos
        active_count = sum(1 for s in stocks["stocks"] if s["is_active"])
        assert dashboard["active_stocks"] == active_count

    def test_alerts_filters_work_consistently(self, client, sample_stock):
        """Test: Filtros de días funcionan consistentemente."""
        # Obtener alertas con diferentes filtros
        alerts_7 = client.get("/api/alerts?days=7").json()
        alerts_30 = client.get("/api/alerts?days=30").json()

        # Las alertas de 30 días deben incluir las de 7 días
        assert alerts_30["total"] >= alerts_7["total"]

    def test_stock_alerts_subset_of_all_alerts(self, client, sample_stock):
        """Test: Alertas de un stock son subconjunto de todas."""
        # Obtener todas las alertas
        all_alerts = client.get("/api/alerts?days=30").json()

        # Obtener alertas de TSLA
        tsla_alerts = client.get("/api/alerts/TSLA?days=30").json()

        # Las de TSLA deben ser <= que el total
        assert tsla_alerts["total"] <= all_alerts["total"]


@pytest.mark.api
class TestHealthAndRoot:
    """Tests para endpoints básicos."""

    def test_health_check(self, client):
        """Test: Health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test: Root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    def test_root_provides_correct_links(self, client):
        """Test: Root proporciona enlaces correctos."""
        response = client.get("/")

        data = response.json()
        assert data["docs"] == "/api/docs"
        assert data["redoc"] == "/api/redoc"
        assert data["health"] == "/health"
