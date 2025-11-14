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

- `/api/prices` - Histórico de precios
- `/api/alerts` - Alertas generadas
- `/api/dashboard` - Estadísticas y resumen
- `/api/news` - Noticias relacionadas
