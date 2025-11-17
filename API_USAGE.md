# 🚀 API REST - Stock Price Alert

Esta guía explica cómo ejecutar y utilizar la API REST del proyecto.

## 📋 Requisitos

Asegúrate de tener todas las dependencias instaladas:

```bash
pip install -r requirements.txt
```

## 🏃 Ejecutar la API

### Modo desarrollo (con auto-reload)

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Modo producción

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 Documentación Interactiva

Una vez que la API esté corriendo, puedes acceder a:

- **Swagger UI**: http://localhost:8000/api/docs
  - Interfaz interactiva para probar todos los endpoints
  - Documentación automática de parámetros y respuestas

- **ReDoc**: http://localhost:8000/api/redoc
  - Documentación alternativa más limpia y fácil de leer

## 🔗 Endpoints Disponibles

### Health Check

- **GET** `/health`
  - Verifica que la API está funcionando
  - Retorna el estado y versión del servicio

### Root

- **GET** `/`
  - Información básica de la API
  - Enlaces a documentación

### 📊 Stocks (CRUD Completo)

- **GET** `/api/stocks`
  - Lista todos los stocks
  - Query params: `only_active=true` para filtrar solo activos

- **GET** `/api/stocks/{symbol}`
  - Obtiene un stock específico por símbolo
  - Retorna 404 si no existe

- **POST** `/api/stocks`
  - Crea un nuevo stock
  - Body: `{"symbol": "TSLA", "company_name": "Tesla Inc", "threshold": 5.0, "is_active": true}`
  - Retorna 201 si se crea exitosamente
  - Retorna 400 si el stock ya existe

- **PUT** `/api/stocks/{symbol}`
  - Actualiza un stock existente
  - Body: campos opcionales `{"company_name": "...", "threshold": 5.0, "is_active": true}`
  - Retorna 404 si no existe

- **PATCH** `/api/stocks/{symbol}/toggle`
  - Activa/desactiva un stock (toggle)
  - Útil para pausar monitoreo sin eliminar

- **DELETE** `/api/stocks/{symbol}`
  - Elimina un stock y todos sus datos relacionados
  - Retorna 404 si no existe

### 📈 Price History (Histórico de Precios)

- **GET** `/api/stocks/{symbol}/prices`
  - Obtiene el histórico de precios de un stock
  - Query params: `days=30` (número de días hacia atrás, default: 30, máx: 365)
  - Retorna lista ordenada por fecha (más reciente primero)

- **GET** `/api/stocks/{symbol}/prices/latest`
  - Obtiene el último precio registrado de un stock
  - Retorna 404 si no existe o no tiene precios

- **POST** `/api/stocks/{symbol}/prices`
  - Añade un precio manualmente (útil para testing/simulación)
  - Body: `{"date": "2024-01-15T00:00:00", "close_price": 250.75}`
  - Calcula automáticamente `previous_close` y `percentage_change`
  - Retorna 201 si se añade exitosamente

### 📊 Dashboard (Estadísticas y Resumen)

- **GET** `/api/dashboard/summary`
  - Obtiene resumen general del sistema
  - Retorna: total de stocks, stocks activos, alertas 24h, última actualización

### 🚨 Alerts (Alertas Generadas)

- **GET** `/api/alerts`
  - Lista alertas recientes del sistema
  - Query params: `days=7` (número de días hacia atrás, default: 7, máx: 365)
  - Retorna lista ordenada por fecha (más reciente primero)

- **GET** `/api/alerts/{stock_symbol}`
  - Obtiene alertas de un stock específico
  - Query params: `days=30` (default: 30, máx: 365)
  - Retorna 404 si el stock no existe

### 📰 News (Noticias)

- **GET** `/api/stocks/{symbol}/news`
  - Obtiene las noticias archivadas de un stock
  - Query params: `limit=10` (número máximo de noticias, default: 10, máx: 100)
  - Retorna lista ordenada por fecha de obtención (más reciente primero)
  - Retorna 404 si el stock no existe

- **POST** `/api/stocks/{symbol}/news`
  - Guarda una noticia relacionada con un stock manualmente
  - Body: `{"title": "...", "description": "...", "url": "...", "published_at": "..."}`
  - Solo `title` es obligatorio, los demás campos son opcionales
  - Útil para testing, integración manual o importación de datos históricos
  - Retorna 201 si se guarda exitosamente
  - Retorna 404 si el stock no existe

## 🧪 Probar la API

### Usando cURL

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# Listar todos los stocks
curl http://localhost:8000/api/stocks

# Obtener stock específico
curl http://localhost:8000/api/stocks/TSLA

# Crear nuevo stock
curl -X POST http://localhost:8000/api/stocks \
  -H "Content-Type: application/json" \
  -d '{"symbol":"NVDA","company_name":"NVIDIA Corp","threshold":6.0}'

# Actualizar stock
curl -X PUT http://localhost:8000/api/stocks/NVDA \
  -H "Content-Type: application/json" \
  -d '{"threshold":7.0}'

# Toggle estado
curl -X PATCH http://localhost:8000/api/stocks/NVDA/toggle

# Eliminar stock
curl -X DELETE http://localhost:8000/api/stocks/NVDA

# === PRICE HISTORY ===

# Obtener histórico de precios (últimos 30 días)
curl http://localhost:8000/api/stocks/TSLA/prices

# Obtener histórico de precios (últimos 7 días)
curl http://localhost:8000/api/stocks/TSLA/prices?days=7

# Obtener último precio
curl http://localhost:8000/api/stocks/TSLA/prices/latest

# Añadir precio manualmente
curl -X POST http://localhost:8000/api/stocks/TSLA/prices \
  -H "Content-Type: application/json" \
  -d '{"date":"2024-01-15T00:00:00","close_price":250.75}'

# === DASHBOARD & ALERTS ===

# Obtener resumen del dashboard
curl http://localhost:8000/api/dashboard/summary

# Listar alertas recientes (últimos 7 días)
curl http://localhost:8000/api/alerts

# Listar alertas de los últimos 30 días
curl http://localhost:8000/api/alerts?days=30

# Obtener alertas de un stock específico
curl http://localhost:8000/api/alerts/TSLA

# === NEWS (NOTICIAS) ===

# Obtener noticias de un stock (últimas 10)
curl http://localhost:8000/api/stocks/TSLA/news

# Obtener noticias con límite personalizado
curl http://localhost:8000/api/stocks/TSLA/news?limit=5

# Guardar una noticia manualmente
curl -X POST http://localhost:8000/api/stocks/TSLA/news \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tesla anuncia nuevo modelo de vehículo eléctrico",
    "description": "Tesla ha anunciado un nuevo modelo revolucionario.",
    "url": "https://example.com/tesla-nuevo-modelo",
    "published_at": "2024-01-15T10:30:00"
  }'

# Guardar noticia con datos mínimos (solo título)
curl -X POST http://localhost:8000/api/stocks/TSLA/news \
  -H "Content-Type: application/json" \
  -d '{"title": "Tesla actualiza su software"}'
```

### Usando Python requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Listar stocks
response = requests.get(f"{BASE_URL}/api/stocks")
data = response.json()
print(f"Total stocks: {data['total']}")

# Obtener stock específico
response = requests.get(f"{BASE_URL}/api/stocks/TSLA")
stock = response.json()
print(f"{stock['symbol']}: {stock['company_name']}")

# Crear stock
new_stock = {
    "symbol": "NVDA",
    "company_name": "NVIDIA Corp",
    "threshold": 6.0
}
response = requests.post(f"{BASE_URL}/api/stocks", json=new_stock)
print(response.json())

# Actualizar stock
update = {"threshold": 7.0}
response = requests.put(f"{BASE_URL}/api/stocks/NVDA", json=update)
print(response.json())

# Eliminar stock
response = requests.delete(f"{BASE_URL}/api/stocks/NVDA")
print(response.json())

# === PRICE HISTORY ===

# Obtener histórico de precios
response = requests.get(f"{BASE_URL}/api/stocks/TSLA/prices")
data = response.json()
print(f"Total precios: {data['total']}")

# Obtener histórico con días personalizados
response = requests.get(f"{BASE_URL}/api/stocks/TSLA/prices", params={"days": 7})
prices = response.json()

# Obtener último precio
response = requests.get(f"{BASE_URL}/api/stocks/TSLA/prices/latest")
latest_price = response.json()
print(f"Último precio: ${latest_price['close_price']:.2f}")

# Añadir precio manualmente
from datetime import datetime
new_price = {
    "date": datetime.now().isoformat(),
    "close_price": 250.75
}
response = requests.post(f"{BASE_URL}/api/stocks/TSLA/prices", json=new_price)
print(response.json())

# === DASHBOARD & ALERTS ===

# Obtener resumen del dashboard
response = requests.get(f"{BASE_URL}/api/dashboard/summary")
summary = response.json()
print(f"Stocks activos: {summary['active_stocks']}/{summary['total_stocks']}")
print(f"Alertas 24h: {summary['recent_alerts_24h']}")

# Listar alertas recientes
response = requests.get(f"{BASE_URL}/api/alerts")
alerts = response.json()
print(f"Alertas (últimos 7 días): {alerts['total']}")

# Alertas con días personalizados
response = requests.get(f"{BASE_URL}/api/alerts", params={"days": 30})
alerts_30d = response.json()

# Alertas de un stock específico
response = requests.get(f"{BASE_URL}/api/alerts/TSLA")
tsla_alerts = response.json()
print(f"Alertas de TSLA: {tsla_alerts['total']}")

# === NEWS (NOTICIAS) ===

# Obtener noticias de un stock
response = requests.get(f"{BASE_URL}/api/stocks/TSLA/news")
data = response.json()
print(f"Noticias de TSLA: {data['total']}")

# Obtener noticias con límite personalizado
response = requests.get(f"{BASE_URL}/api/stocks/TSLA/news", params={"limit": 5})
news = response.json()

# Guardar una noticia completa
news_data = {
    "title": "Tesla anuncia nuevo modelo de vehículo eléctrico",
    "description": "Tesla ha anunciado un nuevo modelo revolucionario que promete cambiar el mercado.",
    "url": "https://example.com/tesla-nuevo-modelo",
    "published_at": "2024-01-15T10:30:00"
}
response = requests.post(f"{BASE_URL}/api/stocks/TSLA/news", json=news_data)
print(response.json())

# Guardar noticia con datos mínimos
minimal_news = {
    "title": "Tesla actualiza su software de conducción autónoma"
}
response = requests.post(f"{BASE_URL}/api/stocks/TSLA/news", json=minimal_news)
saved_news = response.json()
print(f"Noticia guardada con ID: {saved_news['id']}")
```

## 🔧 Configuración

La API utiliza las siguientes configuraciones desde `src/config.py`:

- `DATABASE_URL`: URL de conexión a la base de datos
- Variables de entorno desde `.env`

## 📝 Notas

- La API incluye CORS configurado para desarrollo local
- Los puertos por defecto son:
  - API: `8000`
  - Frontend (futuro): `3000`

## 🎉 Estado Actual

Todos los endpoints de la API REST están implementados y funcionando:

- ✅ Health Check y Root
- ✅ Stocks (CRUD completo)
- ✅ Price History (histórico de precios)
- ✅ Dashboard (estadísticas)
- ✅ Alerts (alertas generadas)
- ✅ News (noticias archivadas)

## 🔜 Próximas Fases

- **PHASE 2.6**: Tests formales con pytest
- **PHASE 3**: Frontend con Tailwind CSS
- **PHASE 4**: Integración y Scheduler
- **PHASE 5**: Documentación y Deployment
