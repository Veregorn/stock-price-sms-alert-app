"""
Aplicación principal de FastAPI.

Este módulo configura y crea la aplicación FastAPI con todas sus
configuraciones: CORS, middleware, rutas, scheduler automático, etc.
"""

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..config import config
from ..database.service import DatabaseService
from ..scheduler import PriceUpdateScheduler, set_scheduler
from .routers import stocks, prices, dashboard, alerts, news, pages, stock_updates, news_updates, notifications

logger = logging.getLogger(__name__)

# Configurar rutas de templates y archivos estáticos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Crear directorios si no existen
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# LIFESPAN CONTEXT MANAGER (Startup/Shutdown Events)
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para eventos de inicio y cierre de la aplicación.

    Startup:
    - Inicializa el scheduler para actualizaciones automáticas de precios cada 15 min

    Shutdown:
    - Detiene el scheduler de forma segura
    """
    # Startup
    logger.info("=" * 70)
    logger.info("STARTING STOCK PRICE ALERT API")
    logger.info("=" * 70)

    # Inicializar database service
    db_service = DatabaseService()

    # Inicializar y arrancar scheduler
    # Ejecutar diariamente a las 18:00 UTC (después del cierre de mercado US)
    scheduler = PriceUpdateScheduler(db_service, hour=18, minute=0)
    set_scheduler(scheduler)
    scheduler.start()

    logger.info("✓ Scheduler started - automatic price updates daily at 18:00 UTC")
    logger.info("=" * 70)

    yield  # La aplicación corre aquí

    # Shutdown
    logger.info("=" * 70)
    logger.info("SHUTTING DOWN STOCK PRICE ALERT API")
    logger.info("=" * 70)

    # Detener scheduler
    scheduler.stop()
    logger.info("✓ Scheduler stopped")
    logger.info("=" * 70)


# Crear la aplicación FastAPI
app = FastAPI(
    title="Stock Price Alert API",
    description="API REST para monitoreo de precios de acciones con alertas automáticas",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc
    lifespan=lifespan  # Añadir lifespan context manager
)

# Configurar templates Jinja2
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

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
# El prefijo /api se añade a todos los routers de API
# Las páginas HTML se sirven sin prefijo

# Routers de API REST
app.include_router(stocks.router, prefix="/api")
app.include_router(prices.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(stock_updates.router, prefix="/api")
app.include_router(news_updates.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")

# Router de páginas HTML (sin prefijo)
app.include_router(pages.router)


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


@app.get("/scheduler/status", tags=["Scheduler"])
async def scheduler_status():
    """
    Endpoint para verificar el estado del scheduler.

    Retorna información sobre el scheduler de actualizaciones automáticas.
    """
    from ..scheduler import get_scheduler

    scheduler = get_scheduler()

    if not scheduler or not scheduler.scheduler:
        return {
            "status": "not_running",
            "message": "Scheduler is not active"
        }

    jobs = scheduler.scheduler.get_jobs()

    return {
        "status": "running",
        "schedule": f"Daily at {scheduler.hour:02d}:{scheduler.minute:02d} UTC",
        "active_jobs": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in jobs
        ]
    }
