"""
Router para endpoints de alertas.

Este módulo contiene endpoints para consultar las alertas que ha generado
el sistema cuando los stocks superan sus umbrales configurados.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query

from ...database import DatabaseService
from ..dependencies import get_db
from ..schemas import (
    AlertResponse,
    AlertListResponse,
    ErrorResponse
)

# Crear router
router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


# =============================================================================
# GET /api/alerts - Listar alertas recientes
# =============================================================================

@router.get(
    "",
    response_model=AlertListResponse,
    summary="Listar alertas recientes",
    description="Obtiene las alertas generadas recientemente por el sistema.",
    responses={
        200: {
            "description": "Alertas obtenidas exitosamente",
            "model": AlertListResponse
        }
    }
)
async def list_alerts(
    days: int = Query(
        7,
        ge=1,
        le=365,
        description="Número de días hacia atrás (1-365, default: 7)"
    ),
    db: DatabaseService = Depends(get_db)
):
    """
    Obtiene las alertas recientes del sistema.

    Parámetros:
    - **days**: Número de días hacia atrás (default: 7, máx: 365)

    Retorna:
    - **total**: Número de alertas encontradas
    - **alerts**: Lista de alertas ordenadas por fecha (más reciente primero)

    Las alertas incluyen información sobre:
    - Qué stock disparó la alerta
    - El cambio porcentual que la causó
    - El umbral configurado en ese momento
    - Si se envió la notificación exitosamente
    - Tipo de notificación (whatsapp, sms)
    """
    alerts = db.get_recent_alerts(symbol=None, days=days)

    return AlertListResponse(
        total=len(alerts),
        alerts=alerts
    )


# =============================================================================
# GET /api/alerts/{stock_symbol} - Alertas de un stock específico
# =============================================================================

@router.get(
    "/{stock_symbol}",
    response_model=AlertListResponse,
    summary="Alertas de un stock específico",
    description="Obtiene las alertas de un stock en particular.",
    responses={
        200: {
            "description": "Alertas obtenidas exitosamente",
            "model": AlertListResponse
        },
        404: {
            "description": "Stock no encontrado",
            "model": ErrorResponse
        }
    }
)
async def get_stock_alerts(
    stock_symbol: str,
    days: int = Query(
        30,
        ge=1,
        le=365,
        description="Número de días hacia atrás (1-365, default: 30)"
    ),
    db: DatabaseService = Depends(get_db)
):
    """
    Obtiene las alertas de un stock específico.

    Parámetros:
    - **stock_symbol**: Símbolo del stock (ej: TSLA, AAPL)
    - **days**: Número de días hacia atrás (default: 30, máx: 365)

    Retorna:
    - **total**: Número de alertas encontradas
    - **alerts**: Lista de alertas del stock ordenadas por fecha

    Errores:
    - **404**: Si el stock no existe

    Útil para:
    - Ver el historial de alertas de un stock
    - Analizar qué stocks generan más alertas
    - Ajustar umbrales basándose en alertas históricas
    """
    # Verificar que el stock existe
    stock = db.get_stock_by_symbol(stock_symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock con símbolo '{stock_symbol.upper()}' no encontrado"
        )

    # Obtener alertas del stock
    alerts = db.get_recent_alerts(symbol=stock_symbol, days=days)

    return AlertListResponse(
        total=len(alerts),
        alerts=alerts
    )
