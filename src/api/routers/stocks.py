"""
Router para endpoints de Stocks (CRUD completo).

Este módulo contiene todos los endpoints relacionados con la gestión de stocks:
- Listar todos los stocks
- Obtener un stock específico
- Crear nuevo stock
- Actualizar stock existente
- Eliminar stock
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from ...database import DatabaseService
from ..dependencies import get_db
from ..schemas import (
    StockCreate,
    StockUpdate,
    StockResponse,
    StockListResponse,
    MessageResponse,
    ErrorResponse
)

# Crear router con prefijo y tags
# El prefijo /stocks se añadirá a todas las rutas de este router
router = APIRouter(
    prefix="/stocks",
    tags=["Stocks"],  # Agrupa endpoints en la documentación
)


# =============================================================================
# GET /api/stocks - Listar todos los stocks
# =============================================================================

@router.get(
    "",
    response_model=StockListResponse,
    summary="Listar todos los stocks",
    description="Obtiene la lista completa de stocks configurados en el sistema.",
    responses={
        200: {
            "description": "Lista de stocks obtenida exitosamente",
            "model": StockListResponse
        }
    }
)
async def list_stocks(
    only_active: bool = Query(
        False,
        description="Si es True, solo devuelve stocks activos"
    ),
    db: DatabaseService = Depends(get_db)
):
    """
    Lista todos los stocks del sistema.

    Parámetros:
    - **only_active**: Filtrar solo stocks activos (default: False)

    Retorna:
    - **total**: Número total de stocks
    - **stocks**: Lista de objetos Stock
    """
    stocks = db.get_all_stocks(only_active=only_active)

    return StockListResponse(
        total=len(stocks),
        stocks=stocks
    )


# =============================================================================
# GET /api/stocks/{symbol} - Obtener un stock específico
# =============================================================================

@router.get(
    "/{symbol}",
    response_model=StockResponse,
    summary="Obtener stock por símbolo",
    description="Obtiene los detalles de un stock específico por su símbolo.",
    responses={
        200: {
            "description": "Stock encontrado",
            "model": StockResponse
        },
        404: {
            "description": "Stock no encontrado",
            "model": ErrorResponse
        }
    }
)
async def get_stock(
    symbol: str,
    db: DatabaseService = Depends(get_db)
):
    """
    Obtiene un stock por su símbolo.

    Parámetros:
    - **symbol**: Símbolo del stock (ej: TSLA, AAPL)

    Retorna:
    - Objeto Stock con todos sus detalles

    Errores:
    - **404**: Si el stock no existe
    """
    stock = db.get_stock_by_symbol(symbol)

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock con símbolo '{symbol.upper()}' no encontrado"
        )

    return stock


# =============================================================================
# POST /api/stocks - Crear nuevo stock
# =============================================================================

@router.post(
    "",
    response_model=StockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo stock",
    description="Crea un nuevo stock en el sistema para monitoreo.",
    responses={
        201: {
            "description": "Stock creado exitosamente",
            "model": StockResponse
        },
        400: {
            "description": "Error de validación o stock ya existe",
            "model": ErrorResponse
        }
    }
)
async def create_stock(
    stock_data: StockCreate,
    db: DatabaseService = Depends(get_db)
):
    """
    Crea un nuevo stock.

    Body (JSON):
    - **symbol**: Símbolo del stock (obligatorio)
    - **company_name**: Nombre de la compañía (obligatorio)
    - **threshold**: Umbral de alerta en % (obligatorio, > 0 y <= 100)
    - **is_active**: Si está activo (opcional, default: True)

    Retorna:
    - El stock creado con su ID y fechas

    Errores:
    - **400**: Si el stock ya existe o datos inválidos
    """
    # Verificar si ya existe
    existing = db.get_stock_by_symbol(stock_data.symbol)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El stock '{stock_data.symbol.upper()}' ya existe en el sistema"
        )

    # Crear el stock
    try:
        stock = db.create_stock(
            symbol=stock_data.symbol,
            company_name=stock_data.company_name,
            threshold=stock_data.threshold,
            is_active=stock_data.is_active
        )
        return stock

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear el stock: {str(e)}"
        )


# =============================================================================
# PUT /api/stocks/{symbol} - Actualizar stock existente
# =============================================================================

@router.put(
    "/{symbol}",
    response_model=StockResponse,
    summary="Actualizar stock",
    description="Actualiza los datos de un stock existente.",
    responses={
        200: {
            "description": "Stock actualizado exitosamente",
            "model": StockResponse
        },
        404: {
            "description": "Stock no encontrado",
            "model": ErrorResponse
        },
        400: {
            "description": "Error de validación",
            "model": ErrorResponse
        }
    }
)
async def update_stock(
    symbol: str,
    stock_data: StockUpdate,
    db: DatabaseService = Depends(get_db)
):
    """
    Actualiza un stock existente.

    Parámetros:
    - **symbol**: Símbolo del stock a actualizar

    Body (JSON) - Todos los campos son opcionales:
    - **company_name**: Nuevo nombre de la compañía
    - **threshold**: Nuevo umbral de alerta
    - **is_active**: Nuevo estado de activación

    Retorna:
    - El stock actualizado

    Errores:
    - **404**: Si el stock no existe
    - **400**: Si los datos son inválidos
    """
    # Verificar que existe
    existing = db.get_stock_by_symbol(symbol)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock con símbolo '{symbol.upper()}' no encontrado"
        )

    # Construir diccionario solo con campos proporcionados (no None)
    update_data = stock_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron campos para actualizar"
        )

    # Actualizar
    try:
        updated_stock = db.update_stock(symbol, **update_data)
        return updated_stock

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al actualizar el stock: {str(e)}"
        )


# =============================================================================
# DELETE /api/stocks/{symbol} - Eliminar stock
# =============================================================================

@router.delete(
    "/{symbol}",
    response_model=MessageResponse,
    summary="Eliminar stock",
    description="Elimina un stock del sistema junto con todos sus datos relacionados.",
    responses={
        200: {
            "description": "Stock eliminado exitosamente",
            "model": MessageResponse
        },
        404: {
            "description": "Stock no encontrado",
            "model": ErrorResponse
        }
    }
)
async def delete_stock(
    symbol: str,
    db: DatabaseService = Depends(get_db)
):
    """
    Elimina un stock del sistema.

    ⚠️  ADVERTENCIA: Esta operación también eliminará:
    - Todos los precios históricos
    - Todas las alertas generadas
    - Todas las noticias archivadas

    Parámetros:
    - **symbol**: Símbolo del stock a eliminar

    Retorna:
    - Mensaje de confirmación

    Errores:
    - **404**: Si el stock no existe
    """
    # Intentar eliminar
    deleted = db.delete_stock(symbol)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock con símbolo '{symbol.upper()}' no encontrado"
        )

    return MessageResponse(
        message=f"Stock '{symbol.upper()}' eliminado correctamente",
        detail="Todos los datos relacionados (precios, alertas, noticias) también fueron eliminados"
    )


# =============================================================================
# PATCH /api/stocks/{symbol}/toggle - Activar/Desactivar stock
# =============================================================================

@router.patch(
    "/{symbol}/toggle",
    response_model=StockResponse,
    summary="Activar/Desactivar stock",
    description="Cambia el estado de activación de un stock (toggle).",
    responses={
        200: {
            "description": "Estado cambiado exitosamente",
            "model": StockResponse
        },
        404: {
            "description": "Stock no encontrado",
            "model": ErrorResponse
        }
    }
)
async def toggle_stock_active(
    symbol: str,
    db: DatabaseService = Depends(get_db)
):
    """
    Activa o desactiva un stock (toggle).

    Útil para pausar/reanudar el monitoreo de un stock sin eliminarlo.

    Parámetros:
    - **symbol**: Símbolo del stock

    Retorna:
    - El stock con su nuevo estado

    Errores:
    - **404**: Si el stock no existe
    """
    # Obtener stock actual
    stock = db.get_stock_by_symbol(symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock con símbolo '{symbol.upper()}' no encontrado"
        )

    # Cambiar estado (toggle)
    new_state = not stock.is_active
    updated_stock = db.update_stock(symbol, is_active=new_state)

    return updated_stock
