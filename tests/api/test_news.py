"""
Tests para endpoints de News.

Prueba:
- GET /api/stocks/{symbol}/news - Obtener noticias de un stock
- POST /api/stocks/{symbol}/news - Guardar noticia manualmente
"""

import pytest
from datetime import datetime


@pytest.mark.api
class TestGetStockNews:
    """Tests para GET /api/stocks/{symbol}/news."""

    def test_get_news_empty(self, client, sample_stock):
        """Test: Obtener noticias cuando no hay ninguna."""
        response = client.get("/api/stocks/TSLA/news")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert data["total"] == 0
        assert data["news"] == []

    def test_get_news_with_data(self, client, sample_news):
        """Test: Obtener noticias cuando existen."""
        response = client.get("/api/stocks/TSLA/news")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert data["total"] >= 3
        assert len(data["news"]) >= 3

    def test_get_news_structure(self, client, sample_news):
        """Test: Estructura de cada noticia."""
        response = client.get("/api/stocks/TSLA/news")

        data = response.json()
        news = data["news"][0]
        assert "id" in news
        assert "stock_id" in news
        assert "title" in news
        assert "description" in news
        assert "url" in news
        assert "published_at" in news
        assert "fetched_at" in news

    def test_get_news_ordered_by_fetched_date(self, client, sample_news):
        """Test: Noticias ordenadas por fecha de obtención (más reciente primero)."""
        response = client.get("/api/stocks/TSLA/news")

        data = response.json()
        news_items = data["news"]

        # Verificar orden descendente
        for i in range(len(news_items) - 1):
            current = datetime.fromisoformat(news_items[i]["fetched_at"])
            next_item = datetime.fromisoformat(news_items[i + 1]["fetched_at"])
            assert current >= next_item

    def test_get_news_with_limit(self, client, sample_news):
        """Test: Limitar número de noticias."""
        response = client.get("/api/stocks/TSLA/news?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["news"]) <= 2

    def test_get_news_limit_validation(self, client, sample_stock):
        """Test: Validación del parámetro limit."""
        # limit < 1
        response = client.get("/api/stocks/TSLA/news?limit=0")
        assert response.status_code == 422

        # limit > 100
        response = client.get("/api/stocks/TSLA/news?limit=101")
        assert response.status_code == 422

    def test_get_news_valid_limit_range(self, client, sample_stock):
        """Test: Rango válido de limit."""
        valid_limits = [1, 10, 50, 100]

        for limit in valid_limits:
            response = client.get(f"/api/stocks/TSLA/news?limit={limit}")
            assert response.status_code == 200

    def test_get_news_stock_not_found(self, client, invalid_symbol):
        """Test: Noticias de stock inexistente."""
        response = client.get(f"/api/stocks/{invalid_symbol}/news")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_news_case_insensitive(self, client, sample_news):
        """Test: Símbolo case-insensitive."""
        response = client.get("/api/stocks/tsla/news")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TSLA"


@pytest.mark.api
class TestSaveNewsArticle:
    """Tests para POST /api/stocks/{symbol}/news."""

    def test_save_news_complete(self, client, sample_stock, sample_news_data):
        """Test: Guardar noticia con todos los campos."""
        response = client.post("/api/stocks/TSLA/news", json=sample_news_data)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_news_data["title"]
        assert data["description"] == sample_news_data["description"]
        assert data["url"] == sample_news_data["url"]
        assert "id" in data
        assert "stock_id" in data
        assert "fetched_at" in data

    def test_save_news_minimal(self, client, sample_stock):
        """Test: Guardar noticia con datos mínimos (solo título)."""
        minimal_data = {
            "title": "Noticia de prueba"
        }

        response = client.post("/api/stocks/TSLA/news", json=minimal_data)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == minimal_data["title"]
        assert data["description"] is None
        assert data["url"] is None
        assert data["published_at"] is None

    def test_save_news_missing_title(self, client, sample_stock):
        """Test: No se puede guardar sin título."""
        invalid_data = {
            "description": "Descripción sin título"
        }

        response = client.post("/api/stocks/TSLA/news", json=invalid_data)

        assert response.status_code == 422

    def test_save_news_title_validation(self, client, sample_stock):
        """Test: Validación del título."""
        # Título vacío
        empty_title = {"title": ""}
        response = client.post("/api/stocks/TSLA/news", json=empty_title)
        assert response.status_code == 422

        # Título muy largo (> 500 caracteres)
        long_title = {"title": "A" * 501}
        response = client.post("/api/stocks/TSLA/news", json=long_title)
        assert response.status_code == 422

    def test_save_news_description_validation(self, client, sample_stock):
        """Test: Validación de descripción."""
        # Descripción muy larga (> 2000 caracteres)
        long_desc = {
            "title": "Título válido",
            "description": "A" * 2001
        }

        response = client.post("/api/stocks/TSLA/news", json=long_desc)
        assert response.status_code == 422

    def test_save_news_url_validation(self, client, sample_stock):
        """Test: Validación de URL."""
        # URL muy larga (> 1000 caracteres)
        long_url = {
            "title": "Título válido",
            "url": "https://example.com/" + "a" * 1000
        }

        response = client.post("/api/stocks/TSLA/news", json=long_url)
        assert response.status_code == 422

    def test_save_news_stock_not_found(self, client, invalid_symbol, sample_news_data):
        """Test: Guardar noticia para stock inexistente."""
        response = client.post(
            f"/api/stocks/{invalid_symbol}/news",
            json=sample_news_data
        )

        assert response.status_code == 404

    def test_save_news_with_published_at(self, client, sample_stock):
        """Test: Guardar noticia con fecha de publicación."""
        news_data = {
            "title": "Noticia con fecha",
            "published_at": "2024-01-15T10:30:00"
        }

        response = client.post("/api/stocks/TSLA/news", json=news_data)

        assert response.status_code == 201
        data = response.json()
        assert data["published_at"] is not None

    def test_save_news_auto_fetched_at(self, client, sample_stock):
        """Test: fetched_at se asigna automáticamente."""
        news_data = {
            "title": "Noticia de prueba"
        }

        response = client.post("/api/stocks/TSLA/news", json=news_data)

        assert response.status_code == 201
        data = response.json()
        assert "fetched_at" in data
        # Verificar que es una fecha válida
        fetched_at = datetime.fromisoformat(data["fetched_at"])
        assert fetched_at is not None


@pytest.mark.api
class TestNewsIntegration:
    """Tests de integración para flujo completo de noticias."""

    def test_full_news_workflow(self, client, sample_stock):
        """Test: Flujo completo de guardar y consultar noticias."""
        # 1. Verificar que no hay noticias
        initial = client.get("/api/stocks/TSLA/news").json()
        initial_count = initial["total"]

        # 2. Guardar primera noticia
        news1 = {
            "title": "Primera noticia",
            "description": "Descripción de la primera noticia"
        }
        response1 = client.post("/api/stocks/TSLA/news", json=news1)
        assert response1.status_code == 201

        # 3. Guardar segunda noticia
        news2 = {
            "title": "Segunda noticia",
            "url": "https://example.com/news-2"
        }
        response2 = client.post("/api/stocks/TSLA/news", json=news2)
        assert response2.status_code == 201

        # 4. Verificar que ambas se guardaron
        final = client.get("/api/stocks/TSLA/news").json()
        assert final["total"] == initial_count + 2

        # 5. Verificar orden (más reciente primero)
        assert final["news"][0]["title"] == "Segunda noticia"
        assert final["news"][1]["title"] == "Primera noticia"

    def test_news_with_different_limits(self, client, sample_stock):
        """Test: Guardar múltiples noticias y consultar con límites."""
        # Guardar 5 noticias
        for i in range(5):
            news_data = {
                "title": f"Noticia {i+1}"
            }
            client.post("/api/stocks/TSLA/news", json=news_data)

        # Consultar con límite 3
        response_3 = client.get("/api/stocks/TSLA/news?limit=3")
        assert response_3.json()["total"] == 3

        # Consultar con límite 10 (debería devolver solo 5)
        response_10 = client.get("/api/stocks/TSLA/news?limit=10")
        data = response_10.json()
        assert data["total"] <= 10
        assert len(data["news"]) >= 5

    def test_news_for_multiple_stocks(self, client, multiple_stocks):
        """Test: Noticias de diferentes stocks están separadas."""
        # Guardar noticias para TSLA
        tsla_news = {"title": "Noticia de TSLA"}
        client.post("/api/stocks/TSLA/news", json=tsla_news)

        # Guardar noticias para AAPL
        aapl_news = {"title": "Noticia de AAPL"}
        client.post("/api/stocks/AAPL/news", json=aapl_news)

        # Verificar que cada stock tiene sus propias noticias
        tsla_response = client.get("/api/stocks/TSLA/news").json()
        aapl_response = client.get("/api/stocks/AAPL/news").json()

        # Verificar que las noticias de TSLA no incluyen las de AAPL
        tsla_titles = [n["title"] for n in tsla_response["news"]]
        assert "Noticia de TSLA" in tsla_titles
        assert "Noticia de AAPL" not in tsla_titles

    def test_news_persists_after_retrieval(self, client, sample_stock):
        """Test: Las noticias persisten después de consultarlas."""
        # Guardar noticia
        news_data = {"title": "Noticia persistente"}
        client.post("/api/stocks/TSLA/news", json=news_data)

        # Consultar múltiples veces
        for _ in range(3):
            response = client.get("/api/stocks/TSLA/news")
            assert response.status_code == 200
            data = response.json()
            assert any(n["title"] == "Noticia persistente" for n in data["news"])
