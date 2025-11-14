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

## 🧪 Probar la API

### Usando cURL

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/
```

### Usando Python requests

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Root endpoint
response = requests.get("http://localhost:8000/")
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

- `/api/stocks` - CRUD de stocks
- `/api/prices` - Histórico de precios
- `/api/alerts` - Alertas generadas
- `/api/dashboard` - Estadísticas y resumen
