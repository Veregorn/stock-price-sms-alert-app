"""
Tests para endpoints de Stocks.

Prueba todos los endpoints del CRUD de stocks:
- GET /api/stocks - Listar stocks
- GET /api/stocks/{symbol} - Obtener stock específico
- POST /api/stocks - Crear stock
- PUT /api/stocks/{symbol} - Actualizar stock
- PATCH /api/stocks/{symbol}/toggle - Toggle estado
- DELETE /api/stocks/{symbol} - Eliminar stock
"""

import pytest


@pytest.mark.api
class TestListStocks:
    """Tests para GET /api/stocks."""

    def test_list_stocks_empty(self, client):
        """Test: Listar stocks cuando no hay ninguno."""
        response = client.get("/api/stocks")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "stocks" in data
        assert isinstance(data["stocks"], list)

    def test_list_stocks_with_data(self, client, multiple_stocks):
        """Test: Listar stocks cuando existen varios."""
        response = client.get("/api/stocks")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["stocks"]) >= 3

    def test_list_stocks_only_active(self, client, multiple_stocks):
        """Test: Filtrar solo stocks activos."""
        response = client.get("/api/stocks?only_active=true")

        assert response.status_code == 200
        data = response.json()
        # Verificar que todos los stocks devueltos están activos
        for stock in data["stocks"]:
            assert stock["is_active"] is True


@pytest.mark.api
class TestGetStock:
    """Tests para GET /api/stocks/{symbol}."""

    def test_get_stock_success(self, client, sample_stock):
        """Test: Obtener stock existente."""
        response = client.get("/api/stocks/TSLA")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert data["company_name"] == "Tesla Inc"
        assert "threshold" in data
        assert "is_active" in data

    def test_get_stock_not_found(self, client, invalid_symbol):
        """Test: Intentar obtener stock inexistente."""
        response = client.get(f"/api/stocks/{invalid_symbol}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_stock_case_insensitive(self, client, sample_stock):
        """Test: Símbolos son case-insensitive."""
        response = client.get("/api/stocks/tsla")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TSLA"


@pytest.mark.api
class TestCreateStock:
    """Tests para POST /api/stocks."""

    def test_create_stock_success(self, client, sample_stock_data):
        """Test: Crear stock exitosamente."""
        # Usar un símbolo diferente para evitar conflictos
        sample_stock_data["symbol"] = "NVDA"

        response = client.post("/api/stocks", json=sample_stock_data)

        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "NVDA"
        assert data["company_name"] == sample_stock_data["company_name"]
        assert data["threshold"] == sample_stock_data["threshold"]

    def test_create_stock_duplicate(self, client, sample_stock, sample_stock_data):
        """Test: Intentar crear stock duplicado."""
        response = client.post("/api/stocks", json=sample_stock_data)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "existe" in data["detail"].lower()

    def test_create_stock_missing_fields(self, client):
        """Test: Crear stock sin campos requeridos."""
        incomplete_data = {"symbol": "AAPL"}

        response = client.post("/api/stocks", json=incomplete_data)

        assert response.status_code == 422

    def test_create_stock_invalid_threshold(self, client):
        """Test: Threshold debe ser positivo."""
        invalid_data = {
            "symbol": "TEST",
            "company_name": "Test Corp",
            "threshold": -5.0
        }

        response = client.post("/api/stocks", json=invalid_data)

        assert response.status_code == 422

    def test_create_stock_uppercase_symbol(self, client):
        """Test: Símbolo se convierte a mayúsculas."""
        data = {
            "symbol": "msft",
            "company_name": "Microsoft Corp",
            "threshold": 5.0
        }

        response = client.post("/api/stocks", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["symbol"] == "MSFT"


@pytest.mark.api
class TestUpdateStock:
    """Tests para PUT /api/stocks/{symbol}."""

    def test_update_stock_success(self, client, sample_stock):
        """Test: Actualizar stock exitosamente."""
        update_data = {
            "company_name": "Tesla Motors Inc",
            "threshold": 7.0
        }

        response = client.put("/api/stocks/TSLA", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == update_data["company_name"]
        assert data["threshold"] == update_data["threshold"]

    def test_update_stock_not_found(self, client, invalid_symbol):
        """Test: Actualizar stock inexistente."""
        update_data = {"threshold": 7.0}

        response = client.put(f"/api/stocks/{invalid_symbol}", json=update_data)

        assert response.status_code == 404

    def test_update_stock_partial(self, client, sample_stock):
        """Test: Actualización parcial (solo threshold)."""
        update_data = {"threshold": 8.0}

        response = client.put("/api/stocks/TSLA", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["threshold"] == 8.0
        # company_name no debería cambiar
        assert data["company_name"] == "Tesla Inc"

    def test_update_stock_invalid_threshold(self, client, sample_stock):
        """Test: No permitir threshold negativo en actualización."""
        update_data = {"threshold": -5.0}

        response = client.put("/api/stocks/TSLA", json=update_data)

        assert response.status_code == 422


@pytest.mark.api
class TestToggleStock:
    """Tests para PATCH /api/stocks/{symbol}/toggle."""

    def test_toggle_stock_active_to_inactive(self, client, sample_stock):
        """Test: Desactivar stock activo."""
        # Asegurar que está activo
        stock = client.get("/api/stocks/TSLA").json()
        initial_state = stock["is_active"]

        # Toggle
        response = client.patch("/api/stocks/TSLA/toggle")

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] != initial_state

    def test_toggle_stock_twice(self, client, sample_stock):
        """Test: Toggle dos veces vuelve al estado original."""
        # Obtener estado inicial
        initial = client.get("/api/stocks/TSLA").json()
        initial_state = initial["is_active"]

        # Toggle 1
        client.patch("/api/stocks/TSLA/toggle")

        # Toggle 2
        response = client.patch("/api/stocks/TSLA/toggle")

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == initial_state

    def test_toggle_stock_not_found(self, client, invalid_symbol):
        """Test: Toggle de stock inexistente."""
        response = client.patch(f"/api/stocks/{invalid_symbol}/toggle")

        assert response.status_code == 404


@pytest.mark.api
class TestDeleteStock:
    """Tests para DELETE /api/stocks/{symbol}."""

    def test_delete_stock_success(self, client):
        """Test: Eliminar stock exitosamente."""
        # Crear stock temporal
        create_data = {
            "symbol": "TEMP",
            "company_name": "Temporary Corp",
            "threshold": 5.0
        }
        client.post("/api/stocks", json=create_data)

        # Eliminar
        response = client.delete("/api/stocks/TEMP")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Verificar que ya no existe
        get_response = client.get("/api/stocks/TEMP")
        assert get_response.status_code == 404

    def test_delete_stock_not_found(self, client, invalid_symbol):
        """Test: Eliminar stock inexistente."""
        response = client.delete(f"/api/stocks/{invalid_symbol}")

        assert response.status_code == 404

    def test_delete_stock_cascades(self, client, sample_stock, sample_prices):
        """Test: Eliminar stock elimina datos relacionados."""
        # Verificar que tiene precios
        prices_before = client.get("/api/stocks/TSLA/prices").json()
        assert prices_before["total"] > 0

        # Eliminar stock
        response = client.delete("/api/stocks/TSLA")
        assert response.status_code == 200

        # Verificar que los precios también se eliminaron
        prices_after = client.get("/api/stocks/TSLA/prices")
        assert prices_after.status_code == 404
