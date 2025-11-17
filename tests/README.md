# Tests - Stock Price Alert API

Este directorio contiene los tests automatizados para la API REST del proyecto.

## 📁 Estructura

```
tests/
├── conftest.py              # Fixtures compartidas de pytest
├── api/                     # Tests de endpoints REST
│   ├── test_stocks.py       # Tests de CRUD de stocks
│   ├── test_prices.py       # Tests de histórico de precios
│   ├── test_dashboard_alerts.py  # Tests de dashboard y alertas
│   └── test_news.py         # Tests de noticias
└── test_database.py         # Tests de modelos de base de datos
```

## 🚀 Ejecutar Tests

### Todos los tests

```bash
pytest
```

### Tests de un módulo específico

```bash
pytest tests/api/test_stocks.py
pytest tests/api/test_prices.py
pytest tests/api/test_news.py
```

### Tests con más detalle (verbose)

```bash
pytest -v
```

### Tests con output completo

```bash
pytest -vv
```

### Ejecutar solo tests marcados

```bash
# Solo tests de API
pytest -m api

# Solo tests de integración
pytest -m integration

# Solo tests unitarios
pytest -m unit
```

### Ver coverage

```bash
pytest --cov=src --cov-report=html
```

Luego abre `htmlcov/index.html` en tu navegador.

## 🧪 Fixtures Disponibles

### Infraestructura
- `client`: TestClient de FastAPI para hacer requests HTTP
- `db`: DatabaseService para operaciones de BD

### Datos de Prueba
- `sample_stock`: Crea un stock de prueba (TSLA)
- `multiple_stocks`: Crea 3 stocks de prueba
- `sample_prices`: Crea histórico de precios (7 días)
- `sample_news`: Crea 3 noticias de prueba

### Helpers
- `invalid_symbol`: Símbolo que no existe ("NONEXISTENT")
- `auth_headers`: Headers de autenticación (futuro)

## 📝 Escribir Nuevos Tests

### Estructura Recomendada

```python
import pytest

@pytest.mark.api
class TestMyFeature:
    """Tests para mi feature."""

    def test_basic_functionality(self, client):
        """Test: Descripción de lo que prueba."""
        response = client.get("/api/endpoint")

        assert response.status_code == 200
        data = response.json()
        assert "field" in data
```

### Mejores Prácticas

1. **Nombres descriptivos**: `test_get_stock_not_found` es mejor que `test_error`
2. **Un concepto por test**: Cada test debe verificar una cosa específica
3. **Usar fixtures**: Reutilizar setup común con fixtures
4. **Docstrings**: Explicar qué prueba cada test
5. **Assertions claras**: Verificar valores específicos, no solo que no falle

### Marcadores Disponibles

- `@pytest.mark.api`: Tests de endpoints REST
- `@pytest.mark.unit`: Tests unitarios
- `@pytest.mark.integration`: Tests de integración
- `@pytest.mark.slow`: Tests que tardan más tiempo

## 🔧 Configuración

La configuración de pytest está en [`pytest.ini`](../pytest.ini) en la raíz del proyecto.

## 📊 Coverage Actual

Los tests cubren:
- ✅ Todos los endpoints de Stocks (CRUD completo)
- ✅ Todos los endpoints de Prices (histórico)
- ✅ Dashboard y estadísticas
- ✅ Alertas (listado y por stock)
- ✅ Noticias (GET y POST)
- ✅ Health check y root
- ✅ Validaciones de parámetros
- ✅ Casos de error (404, 422, etc.)

## 🐛 Debugging Tests

### Ver print statements

```bash
pytest -s
```

### Ver solo tests fallidos

```bash
pytest --lf
```

### Ver solo el primer fallo

```bash
pytest -x
```

### Ver traceback completo

```bash
pytest --tb=long
```

## 📚 Recursos

- [Documentación de pytest](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
