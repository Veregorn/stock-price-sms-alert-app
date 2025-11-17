"""
Router para endpoints de histórico de precios.

Este módulo contiene todos los endpoints relacionados con los precios históricos
de los stocks:
- Obtener histórico de precios de un stock
- Obtener el último precio registrado
- Añadir precio manualmente (para testing/simulación)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime

from ...database import DatabaseService
from ..dependencies import get_db
from ..schemas import (
    PriceHistoryCreate,
    PriceHistoryResponse,
    PriceHistoryListResponse,
    ErrorResponse
)

# Crear router sin prefijo (se añadirá en main.py)
router = APIRouter(
    tags=["Price History"],  # Agrupa endpoints en la documentación
)


# =============================================================================
# GET /api/stocks/{symbol}/prices - Obtener histórico de precios
# =============================================================================

@router.get(
    "/stocks/{symbol}/prices",
    response_model=PriceHistoryListResponse,
    summary="Obtener histórico de precios",
    description="Obtiene el histórico de precios de un stock específico.",
    responses={
        200: {
            "description": "Histórico obtenido exitosamente",
            "model": PriceHistoryListResponse
        },
        404: {
            "description": "Stock no encontrado",
            "model": ErrorResponse
        }
    }
)
async def get_price_history(
    symbol: str,
    days: int = Query(
        30,
        ge=1,
        le=365,
        description="Número de días hacia atrás (1-365, default: 30)"
    ),
    db: DatabaseService = Depends(get_db)
):
    """
    Obtiene el histórico de precios de un stock.

    Parámetros:
    - **symbol**: Símbolo del stock (ej: TSLA, AAPL)
    - **days**: Número de días hacia atrás (default: 30, máx: 365)

    Retorna:
    - **symbol**: Símbolo del stock
    - **total**: Número de registros encontrados
    - **prices**: Lista de precios ordenados por fecha (más reciente primero)

    Errores:
    - **404**: Si el stock no existe
    """
    # Verificar que el stock existe
    stock = db.get_stock_by_symbol(symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock con símbolo '{symbol.upper()}' no encontrado"
        )

    # Obtener histórico
    prices = db.get_price_history(symbol, days=days)

    return PriceHistoryListResponse(
        symbol=symbol.upper(),
        total=len(prices),
        prices=prices
    )


# =============================================================================
# GET /api/stocks/{symbol}/prices/latest - Obtener último precio
# =============================================================================

@router.get(
    "/stocks/{symbol}/prices/latest",
    response_model=PriceHistoryResponse,
    summary="Obtener último precio",
    description="Obtiene el precio más reciente registrado de un stock.",
    responses={
        200: {
            "description": "Último precio obtenido",
            "model": PriceHistoryResponse
        },
        404: {
            "description": "Stock no encontrado o sin precios registrados",
            "model": ErrorResponse
        }
    }
)
async def get_latest_price(
    symbol: str,
    db: DatabaseService = Depends(get_db)
):
    """
    Obtiene el último precio registrado de un stock.

    Parámetros:
    - **symbol**: Símbolo del stock (ej: TSLA, AAPL)

    Retorna:
    - El registro de precio más reciente

    Errores:
    - **404**: Si el stock no existe o no tiene precios registrados
    """
    # Verificar que el stock existe
    stock = db.get_stock_by_symbol(symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock con símbolo '{symbol.upper()}' no encontrado"
        )

    # Obtener último precio (buscar en todos los registros, no limitar por días)
    # Usamos un rango amplio para asegurar que encontramos el más reciente
    prices = db.get_price_history(symbol, days=365)

    if not prices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay precios registrados para '{symbol.upper()}'"
        )

    # El primer elemento es el más reciente (orden DESC en la BD)
    return prices[0]


# =============================================================================
# POST /api/stocks/{symbol}/prices - Añadir precio manualmente
# =============================================================================

@router.post(
    "/stocks/{symbol}/prices",
    response_model=PriceHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir precio manualmente",
    description="Añade un registro de precio manualmente. Útil para testing o carga inicial de datos.",
    responses={
        201: {
            "description": "Precio añadido exitosamente",
            "model": PriceHistoryResponse
        },
        404: {
            "description": "Stock no encontrado",
            "model": ErrorResponse
        },
        400: {
            "description": "Error al añadir el precio",
            "model": ErrorResponse
        }
    }
)
async def add_price_manually(
    symbol: str,
    price_data: PriceHistoryCreate,
    db: DatabaseService = Depends(get_db)
):
    """
    Añade un registro de precio manualmente.

    **⚠️ Nota**: En producción, los precios se obtienen automáticamente de la API
    de stocks. Este endpoint es útil para:
    - Testing y desarrollo
    - Carga inicial de datos históricos
    - Simulaciones

    Parámetros:
    - **symbol**: Símbolo del stock

    Body (JSON):
    - **date**: Fecha del precio (ISO 8601)
    - **close_price**: Precio de cierre (debe ser > 0)

    El sistema calculará automáticamente:
    - **previous_close**: Buscando el precio anterior en la BD
    - **percentage_change**: Basado en previous_close

    Retorna:
    - El registro de precio creado con todos los campos

    Errores:
    - **404**: Si el stock no existe
    - **400**: Si hay error al añadir el precio
    """
    # Verificar que el stock existe
    stock = db.get_stock_by_symbol(symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock con símbolo '{symbol.upper()}' no encontrado"
        )

    # Obtener el precio anterior más cercano a la fecha proporcionada
    # (para calcular previous_close y percentage_change)
    existing_prices = db.get_price_history(symbol, days=365)

    previous_close = None
    percentage_change = None

    if existing_prices:
        # Buscar el precio más cercano anterior a la fecha proporcionada
        previous_prices = [
            p for p in existing_prices
            if p.date < price_data.date
        ]

        if previous_prices:
            # El más reciente de los anteriores
            previous_price = previous_prices[0]
            previous_close = previous_price.close_price

            # Calcular cambio porcentual
            percentage_change = (
                (price_data.close_price - previous_close) / previous_close * 100
            )

    # Añadir el precio
    try:
        price = db.add_price_history(
            symbol=symbol,
            date=price_data.date,
            close_price=price_data.close_price,
            previous_close=previous_close,
            percentage_change=percentage_change
        )

        if not price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al añadir el precio"
            )

        return price

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al añadir el precio: {str(e)}"
        )
