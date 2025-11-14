"""
Aplicación principal de FastAPI.

Este módulo configura y crea la aplicación FastAPI con todas sus
configuraciones: CORS, middleware, rutas, etc.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import config
from .routers import stocks

# Crear la aplicación FastAPI
app = FastAPI(
    title="Stock Price Alert API",
    description="API REST para monitoreo de precios de acciones con alertas automáticas",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc
)

# ============================================================================
# CONFIGURACIÓN DE CORS
# ============================================================================
# CORS (Cross-Origin Resource Sharing) permite que el frontend
# (que puede estar en otro dominio/puerto) pueda hacer peticiones a la API

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend local
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # API local
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,  # Permitir cookies
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permitir todos los headers
)


# ============================================================================
# REGISTRAR ROUTERS
# ============================================================================
# Los routers organizan endpoints relacionados en grupos lógicos
# El prefijo /api se añade a todos los routers

app.include_router(stocks.router, prefix="/api")


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================
# Endpoint simple para verificar que la API está funcionando
# Útil para monitoreo, load balancers, y verificación de despliegue

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint de health check.

    Retorna el estado de la API y su versión.
    Útil para monitoreo y verificación de que el servicio está activo.
    """
    return {
        "status": "healthy",
        "service": "Stock Price Alert API",
        "version": "1.0.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz.

    Proporciona información básica sobre la API y enlaces a la documentación.
    """
    return {
        "message": "Stock Price Alert API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "health": "/health"
    }
