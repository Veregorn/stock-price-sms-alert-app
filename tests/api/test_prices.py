"""
Tests para endpoints de Price History.

Prueba todos los endpoints de histórico de precios:
- GET /api/stocks/{symbol}/prices - Obtener histórico
- GET /api/stocks/{symbol}/prices/latest - Obtener último precio
- POST /api/stocks/{symbol}/prices - Añadir precio manualmente
"""

import pytest
from datetime import datetime, timedelta


@pytest.mark.api
class TestGetPriceHistory:
    """Tests para GET /api/stocks/{symbol}/prices."""

    def test_get_price_history_empty(self, client, sample_stock):
        """Test: Obtener histórico cuando no hay precios."""
        response = client.get("/api/stocks/TSLA/prices")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert data["total"] == 0
        assert data["prices"] == []

    def test_get_price_history_with_data(self, client, sample_prices):
        """Test: Obtener histórico con datos."""
        response = client.get("/api/stocks/TSLA/prices")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert data["total"] > 0
        assert len(data["prices"]) > 0

    def test_get_price_history_ordered_by_date(self, client, sample_prices):
        """Test: Precios ordenados por fecha (más reciente primero)."""
        response = client.get("/api/stocks/TSLA/prices")

        data = response.json()
        prices = data["prices"]

        # Verificar orden descendente por fecha
        for i in range(len(prices) - 1):
            current_date = datetime.fromisoformat(prices[i]["date"])
            next_date = datetime.fromisoformat(prices[i + 1]["date"])
            assert current_date >= next_date

    def test_get_price_history_with_days_filter(self, client, sample_prices):
        """Test: Filtrar por número de días."""
        response = client.get("/api/stocks/TSLA/prices?days=3")

        assert response.status_code == 200
        data = response.json()
        # Debería tener aproximadamente 3 precios (puede variar por timing)
        assert 1 <= len(data["prices"]) <= 4

    def test_get_price_history_invalid_days(self, client, sample_stock):
        """Test: Validar límites del parámetro days."""
        # days menor que 1
        response = client.get("/api/stocks/TSLA/prices?days=0")
        assert response.status_code == 422

        # days mayor que 365
        response = client.get("/api/stocks/TSLA/prices?days=400")
        assert response.status_code == 422

    def test_get_price_history_stock_not_found(self, client, invalid_symbol):
        """Test: Histórico de stock inexistente."""
        response = client.get(f"/api/stocks/{invalid_symbol}/prices")

        assert response.status_code == 404


@pytest.mark.api
class TestGetLatestPrice:
    """Tests para GET /api/stocks/{symbol}/prices/latest."""

    def test_get_latest_price_success(self, client, sample_prices):
        """Test: Obtener último precio exitosamente."""
        response = client.get("/api/stocks/TSLA/prices/latest")

        assert response.status_code == 200
        data = response.json()
        assert "close_price" in data
        assert "date" in data
        assert "percentage_change" in data

    def test_get_latest_price_no_prices(self, client, sample_stock):
        """Test: Último precio cuando no hay precios."""
        response = client.get("/api/stocks/TSLA/prices/latest")

        assert response.status_code == 404

    def test_get_latest_price_stock_not_found(self, client, invalid_symbol):
        """Test: Último precio de stock inexistente."""
        response = client.get(f"/api/stocks/{invalid_symbol}/prices/latest")

        assert response.status_code == 404

    def test_get_latest_price_is_most_recent(self, client, sample_prices):
        """Test: Verificar que devuelve el precio más reciente."""
        # Obtener último precio
        latest = client.get("/api/stocks/TSLA/prices/latest").json()

        # Obtener todo el histórico
        all_prices = client.get("/api/stocks/TSLA/prices").json()["prices"]

        # El último precio debe coincidir con el primero del histórico
        assert latest["id"] == all_prices[0]["id"]
        assert latest["close_price"] == all_prices[0]["close_price"]


@pytest.mark.api
class TestAddPrice:
    """Tests para POST /api/stocks/{symbol}/prices."""

    def test_add_price_success(self, client, sample_stock, sample_price_data):
        """Test: Añadir precio exitosamente."""
        response = client.post("/api/stocks/TSLA/prices", json=sample_price_data)

        assert response.status_code == 201
        data = response.json()
        assert data["close_price"] == sample_price_data["close_price"]
        assert "previous_close" in data
        assert "percentage_change" in data

    def test_add_price_calculates_percentage_change(self, client, sample_prices):
        """Test: Cálculo automático de percentage_change."""
        # Añadir nuevo precio
        new_price_data = {
            "date": datetime.now().isoformat(),
            "close_price": 300.0
        }

        response = client.post("/api/stocks/TSLA/prices", json=new_price_data)

        assert response.status_code == 201
        data = response.json()
        assert data["previous_close"] is not None
        assert data["percentage_change"] is not None

    def test_add_price_first_price_no_previous(self, client, sample_stock):
        """Test: Primer precio no tiene previous_close."""
        price_data = {
            "date": datetime.now().isoformat(),
            "close_price": 250.0
        }

        response = client.post("/api/stocks/TSLA/prices", json=price_data)

        assert response.status_code == 201
        data = response.json()
        assert data["previous_close"] is None
        # percentage_change puede ser None o 0.0 para el primer precio
        assert data["percentage_change"] in [None, 0.0]

    def test_add_price_stock_not_found(self, client, invalid_symbol, sample_price_data):
        """Test: Añadir precio a stock inexistente."""
        response = client.post(
            f"/api/stocks/{invalid_symbol}/prices",
            json=sample_price_data
        )

        assert response.status_code == 404

    def test_add_price_missing_fields(self, client, sample_stock):
        """Test: Datos incompletos."""
        incomplete_data = {"date": datetime.now().isoformat()}

        response = client.post("/api/stocks/TSLA/prices", json=incomplete_data)

        assert response.status_code == 422

    def test_add_price_invalid_close_price(self, client, sample_stock):
        """Test: close_price debe ser positivo."""
        invalid_data = {
            "date": datetime.now().isoformat(),
            "close_price": -50.0
        }

        response = client.post("/api/stocks/TSLA/prices", json=invalid_data)

        assert response.status_code == 422

    def test_add_price_multiple_dates(self, client, sample_stock):
        """Test: Añadir precios de diferentes fechas."""
        dates = [
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=1),
            datetime.now()
        ]

        for i, date in enumerate(dates):
            price_data = {
                "date": date.isoformat(),
                "close_price": 250.0 + (i * 10)
            }

            response = client.post("/api/stocks/TSLA/prices", json=price_data)
            assert response.status_code == 201

        # Verificar que se guardaron los 3
        history = client.get("/api/stocks/TSLA/prices").json()
        assert history["total"] >= 3


@pytest.mark.api
class TestPriceHistoryIntegration:
    """Tests de integración para flujo completo de precios."""

    def test_full_price_workflow(self, client, sample_stock):
        """Test: Flujo completo de añadir precios y consultar histórico."""
        # 1. Añadir primer precio
        price1 = {
            "date": (datetime.now() - timedelta(days=2)).isoformat(),
            "close_price": 100.0
        }
        response1 = client.post("/api/stocks/TSLA/prices", json=price1)
        assert response1.status_code == 201

        # 2. Añadir segundo precio (con incremento)
        price2 = {
            "date": (datetime.now() - timedelta(days=1)).isoformat(),
            "close_price": 110.0
        }
        response2 = client.post("/api/stocks/TSLA/prices", json=price2)
        assert response2.status_code == 201
        data2 = response2.json()
        # Debe calcular 10% de incremento
        assert data2["percentage_change"] == pytest.approx(10.0, rel=0.01)

        # 3. Obtener histórico completo
        history = client.get("/api/stocks/TSLA/prices").json()
        assert history["total"] == 2

        # 4. Obtener último precio
        latest_response = client.get("/api/stocks/TSLA/prices/latest")
        assert latest_response.status_code == 200
        latest = latest_response.json()
        assert "close_price" in latest
        assert latest["close_price"] == 110.0

    def test_price_history_with_filters(self, client, sample_stock):
        """Test: Histórico con diferentes filtros de días."""
        # Añadir precios de los últimos 10 días
        for i in range(10):
            price_data = {
                "date": (datetime.now() - timedelta(days=9-i)).isoformat(),
                "close_price": 100.0 + i
            }
            client.post("/api/stocks/TSLA/prices", json=price_data)

        # Filtrar últimos 3 días (puede variar ligeramente por timing)
        response_3 = client.get("/api/stocks/TSLA/prices?days=3")
        assert 1 <= response_3.json()["total"] <= 4

        # Filtrar últimos 7 días
        response_7 = client.get("/api/stocks/TSLA/prices?days=7")
        assert 5 <= response_7.json()["total"] <= 8

        # Sin filtro (default 30 días, debe devolver todos)
        response_all = client.get("/api/stocks/TSLA/prices")
        assert response_all.json()["total"] == 10
