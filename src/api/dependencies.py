"""
Dependencias de FastAPI (Dependency Injection).

Este módulo contiene las funciones de dependency injection que se utilizan
en los endpoints de la API. FastAPI las ejecuta automáticamente y proporciona
los objetos necesarios a las funciones de los endpoints.
"""

from typing import Generator

from ..database import DatabaseService
from ..config import config


def get_db() -> Generator[DatabaseService, None, None]:
    """
    Dependency que proporciona una instancia de DatabaseService.

    Esta función se usa como dependency en los endpoints de FastAPI.
    FastAPI se encarga de ejecutarla y pasar el resultado al endpoint.

    Uso en un endpoint:
        @app.get("/stocks")
        def get_stocks(db: DatabaseService = Depends(get_db)):
            return db.get_all_stocks()

    Ventajas del patrón Dependency Injection:
    - Facilita los tests (puedes inyectar mocks)
    - Gestión automática del ciclo de vida (crear/cerrar)
    - Código más limpio y desacoplado

    Yields:
        DatabaseService: Instancia del servicio de base de datos
    """
    # Crear instancia del servicio
    db = DatabaseService(database_url=config.DATABASE_URL)

    try:
        # Yield proporciona la instancia al endpoint
        # FastAPI esperará a que el endpoint termine antes de continuar
        yield db
    finally:
        # Este código se ejecuta después de que el endpoint termine
        # Garantiza que la conexión siempre se cierre
        db.close()
