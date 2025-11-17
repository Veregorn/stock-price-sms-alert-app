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

## 🔜 Próximos Endpoints

En las siguientes fases se añadirán:

- `/api/alerts` - Alertas generadas
- `/api/dashboard` - Estadísticas y resumen
- `/api/news` - Noticias relacionadas
