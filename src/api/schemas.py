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


# =============================================================================
# SCHEMAS PARA PRICE HISTORY
# =============================================================================

class PriceHistoryBase(BaseModel):
    """
    Schema base para PriceHistory.

    Contiene los campos comunes del histórico de precios.
    """
    date: datetime = Field(
        ...,
        description="Fecha del precio"
    )
    close_price: float = Field(
        ...,
        gt=0,
        description="Precio de cierre (debe ser > 0)"
    )
    previous_close: Optional[float] = Field(
        None,
        gt=0,
        description="Precio de cierre anterior"
    )
    percentage_change: Optional[float] = Field(
        None,
        description="Cambio porcentual respecto al precio anterior"
    )


class PriceHistoryCreate(BaseModel):
    """
    Schema para crear un registro de precio.

    Usado en: POST /api/stocks/{symbol}/prices
    Solo requiere date y close_price, el resto se calcula automáticamente.
    """
    date: datetime = Field(
        ...,
        description="Fecha del precio"
    )
    close_price: float = Field(
        ...,
        gt=0,
        description="Precio de cierre (debe ser > 0)",
        examples=[250.75]
    )


class PriceHistoryResponse(PriceHistoryBase):
    """
    Schema de respuesta para un registro de precio.

    Usado en: respuestas de GET y POST
    Incluye campos adicionales generados por la BD.
    """
    id: int = Field(
        ...,
        description="ID único del registro"
    )
    stock_id: int = Field(
        ...,
        description="ID del stock al que pertenece"
    )
    created_at: datetime = Field(
        ...,
        description="Fecha de creación del registro"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "stock_id": 1,
                "date": "2024-01-15T00:00:00",
                "close_price": 250.75,
                "previous_close": 245.50,
                "percentage_change": 2.14,
                "created_at": "2024-01-15T10:30:00"
            }
        }
    )


class PriceHistoryListResponse(BaseModel):
    """
    Schema para respuesta con lista de precios históricos.

    Usado en: GET /api/stocks/{symbol}/prices
    """
    symbol: str = Field(
        ...,
        description="Símbolo del stock"
    )
    total: int = Field(
        ...,
        description="Número total de registros"
    )
    prices: list[PriceHistoryResponse] = Field(
        ...,
        description="Lista de precios históricos"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "TSLA",
                "total": 30,
                "prices": [
                    {
                        "id": 1,
                        "stock_id": 1,
                        "date": "2024-01-15T00:00:00",
                        "close_price": 250.75,
                        "previous_close": 245.50,
                        "percentage_change": 2.14,
                        "created_at": "2024-01-15T10:30:00"
                    }
                ]
            }
        }
    )


# =============================================================================
# SCHEMAS PARA ALERTS
# =============================================================================

class AlertResponse(BaseModel):
    """
    Schema de respuesta para una alerta.

    Usado en: respuestas de GET para alertas
    """
    id: int = Field(
        ...,
        description="ID único de la alerta"
    )
    stock_id: int = Field(
        ...,
        description="ID del stock que disparó la alerta"
    )
    percentage_change: float = Field(
        ...,
        description="Cambio porcentual que disparó la alerta"
    )
    threshold_at_time: float = Field(
        ...,
        description="Umbral configurado en el momento de la alerta"
    )
    price_before: Optional[float] = Field(
        None,
        description="Precio anterior"
    )
    price_after: Optional[float] = Field(
        None,
        description="Precio nuevo que disparó la alerta"
    )
    message_sent: bool = Field(
        ...,
        description="Si se envió la notificación exitosamente"
    )
    notification_type: Optional[str] = Field(
        None,
        description="Tipo de notificación enviada (whatsapp, sms)"
    )
    error_message: Optional[str] = Field(
        None,
        description="Mensaje de error si falló el envío"
    )
    triggered_at: datetime = Field(
        ...,
        description="Fecha y hora en que se disparó la alerta"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "stock_id": 1,
                "percentage_change": 6.5,
                "threshold_at_time": 5.0,
                "price_before": 250.00,
                "price_after": 266.25,
                "message_sent": True,
                "notification_type": "whatsapp",
                "error_message": None,
                "triggered_at": "2024-01-15T10:30:00"
            }
        }
    )


class AlertListResponse(BaseModel):
    """
    Schema para respuesta con lista de alertas.

    Usado en: GET /api/alerts
    """
    total: int = Field(
        ...,
        description="Número total de alertas"
    )
    alerts: list[AlertResponse] = Field(
        ...,
        description="Lista de alertas"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 5,
                "alerts": [
                    {
                        "id": 1,
                        "stock_id": 1,
                        "percentage_change": 6.5,
                        "threshold_at_time": 5.0,
                        "price_before": 250.00,
                        "price_after": 266.25,
                        "message_sent": True,
                        "notification_type": "whatsapp",
                        "error_message": None,
                        "triggered_at": "2024-01-15T10:30:00"
                    }
                ]
            }
        }
    )


# =============================================================================
# SCHEMAS PARA DASHBOARD
# =============================================================================

class DashboardSummaryResponse(BaseModel):
    """
    Schema para el resumen del dashboard.

    Contiene estadísticas generales del sistema.
    """
    total_stocks: int = Field(
        ...,
        description="Número total de stocks configurados"
    )
    active_stocks: int = Field(
        ...,
        description="Número de stocks activos"
    )
    recent_alerts_24h: int = Field(
        ...,
        description="Alertas generadas en las últimas 24 horas"
    )
    last_price_update: Optional[datetime] = Field(
        None,
        description="Fecha de la última actualización de precios"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_stocks": 8,
                "active_stocks": 7,
                "recent_alerts_24h": 3,
                "last_price_update": "2024-01-15T14:30:00"
            }
        }
    )


# =============================================================================
# SCHEMAS PARA NEWS ARTICLES
# =============================================================================

class NewsArticleCreate(BaseModel):
    """
    Schema para guardar una noticia.

    Usado en: POST /api/stocks/{symbol}/news
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Título de la noticia",
        examples=["Tesla anuncia nuevo modelo eléctrico"]
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Descripción o resumen de la noticia"
    )
    url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL de la noticia original"
    )
    published_at: Optional[datetime] = Field(
        None,
        description="Fecha de publicación de la noticia"
    )


class NewsArticleResponse(BaseModel):
    """
    Schema de respuesta para una noticia.

    Usado en: respuestas de GET y POST
    """
    id: int = Field(
        ...,
        description="ID único de la noticia"
    )
    stock_id: int = Field(
        ...,
        description="ID del stock relacionado"
    )
    title: str = Field(
        ...,
        description="Título de la noticia"
    )
    description: Optional[str] = Field(
        None,
        description="Descripción o resumen"
    )
    url: Optional[str] = Field(
        None,
        description="URL de la noticia"
    )
    published_at: Optional[datetime] = Field(
        None,
        description="Fecha de publicación"
    )
    fetched_at: datetime = Field(
        ...,
        description="Fecha en que se guardó la noticia"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "stock_id": 1,
                "title": "Tesla anuncia nuevo modelo eléctrico",
                "description": "La compañía ha revelado detalles sobre su próximo vehículo...",
                "url": "https://example.com/tesla-news",
                "published_at": "2024-01-15T10:00:00",
                "fetched_at": "2024-01-15T10:30:00"
            }
        }
    )


class NewsArticleListResponse(BaseModel):
    """
    Schema para respuesta con lista de noticias.

    Usado en: GET /api/stocks/{symbol}/news
    """
    symbol: str = Field(
        ...,
        description="Símbolo del stock"
    )
    total: int = Field(
        ...,
        description="Número total de noticias"
    )
    news: list[NewsArticleResponse] = Field(
        ...,
        description="Lista de noticias"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "TSLA",
                "total": 5,
                "news": [
                    {
                        "id": 1,
                        "stock_id": 1,
                        "title": "Tesla anuncia nuevo modelo eléctrico",
                        "description": "La compañía ha revelado detalles...",
                        "url": "https://example.com/tesla-news",
                        "published_at": "2024-01-15T10:00:00",
                        "fetched_at": "2024-01-15T10:30:00"
                    }
                ]
            }
        }
    )
