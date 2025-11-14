"""
Schemas de Pydantic para validación de datos de la API.

Los schemas definen la estructura de los datos que entran y salen de la API.
Son diferentes de los modelos SQLAlchemy:
- Modelos SQLAlchemy = estructura de la BD
- Schemas Pydantic = estructura de peticiones/respuestas HTTP

Pydantic valida automáticamente los tipos y formatos.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# SCHEMAS PARA STOCK
# =============================================================================

class StockBase(BaseModel):
    """
    Schema base de Stock con campos comunes.

    Otros schemas heredan de este para reutilizar campos.
    """
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Símbolo del stock (ej: TSLA, AAPL)",
        examples=["TSLA"]
    )
    company_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre de la compañía",
        examples=["Tesla Inc"]
    )
    threshold: float = Field(
        ...,
        gt=0,
        le=100,
        description="Umbral de alerta en porcentaje (debe ser > 0 y <= 100)",
        examples=[5.0]
    )


class StockCreate(StockBase):
    """
    Schema para crear un nuevo stock.

    Usado en: POST /api/stocks
    Hereda todos los campos de StockBase.
    """
    is_active: bool = Field(
        default=True,
        description="Si el stock está activo para monitoreo"
    )


class StockUpdate(BaseModel):
    """
    Schema para actualizar un stock existente.

    Usado en: PUT /api/stocks/{symbol}
    Todos los campos son opcionales (permite actualización parcial).
    """
    company_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Nuevo nombre de la compañía"
    )
    threshold: Optional[float] = Field(
        None,
        gt=0,
        le=100,
        description="Nuevo umbral de alerta en porcentaje"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Nuevo estado de activación"
    )


class StockResponse(StockBase):
    """
    Schema de respuesta para un stock.

    Usado en: respuestas de GET, POST, PUT
    Incluye campos adicionales que genera la BD (id, fechas).
    """
    id: int = Field(
        ...,
        description="ID único del stock en la base de datos"
    )
    is_active: bool = Field(
        ...,
        description="Si el stock está activo para monitoreo"
    )
    created_at: datetime = Field(
        ...,
        description="Fecha de creación del registro"
    )
    updated_at: datetime = Field(
        ...,
        description="Fecha de última actualización"
    )

    # Configuración de Pydantic v2
    model_config = ConfigDict(
        from_attributes=True,  # Permite crear desde objetos SQLAlchemy
        json_schema_extra={
            "example": {
                "id": 1,
                "symbol": "TSLA",
                "company_name": "Tesla Inc",
                "threshold": 5.0,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )


# =============================================================================
# SCHEMAS PARA RESPUESTAS MÚLTIPLES
# =============================================================================

class StockListResponse(BaseModel):
    """
    Schema para respuesta con lista de stocks.

    Usado en: GET /api/stocks
    """
    total: int = Field(
        ...,
        description="Número total de stocks"
    )
    stocks: list[StockResponse] = Field(
        ...,
        description="Lista de stocks"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 2,
                "stocks": [
                    {
                        "id": 1,
                        "symbol": "TSLA",
                        "company_name": "Tesla Inc",
                        "threshold": 5.0,
                        "is_active": True,
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T10:30:00"
                    },
                    {
                        "id": 2,
                        "symbol": "AAPL",
                        "company_name": "Apple Inc",
                        "threshold": 3.0,
                        "is_active": True,
                        "created_at": "2024-01-15T10:31:00",
                        "updated_at": "2024-01-15T10:31:00"
                    }
                ]
            }
        }
    )


# =============================================================================
# SCHEMAS PARA MENSAJES Y ERRORES
# =============================================================================

class MessageResponse(BaseModel):
    """
    Schema para respuestas simples con mensaje.

    Usado en: operaciones exitosas, errores, etc.
    """
    message: str = Field(
        ...,
        description="Mensaje descriptivo"
    )
    detail: Optional[str] = Field(
        None,
        description="Detalles adicionales opcionales"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Stock eliminado correctamente",
                "detail": "El stock TSLA fue eliminado junto con sus datos relacionados"
            }
        }
    )


class ErrorResponse(BaseModel):
    """
    Schema para respuestas de error.

    Usado en: manejo de excepciones y errores.
    """
    error: str = Field(
        ...,
        description="Tipo de error"
    )
    message: str = Field(
        ...,
        description="Mensaje de error legible"
    )
    detail: Optional[str] = Field(
        None,
        description="Detalles técnicos del error"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "NotFound",
                "message": "Stock no encontrado",
                "detail": "El stock con símbolo 'XYZ' no existe en la base de datos"
            }
        }
    )
