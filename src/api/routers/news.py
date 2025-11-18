"""
Router para endpoints de noticias.

Este módulo contiene endpoints para gestionar noticias relacionadas con stocks.
Las noticias se pueden obtener de APIs externas y almacenar para consulta posterior.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query

from ...database import DatabaseService
from ..dependencies import get_db
from ..schemas import (
    NewsArticleCreate,
    NewsArticleResponse,
    NewsArticleListResponse,
    ErrorResponse
)

# Crear router sin prefijo (se añadirá en main.py)
router = APIRouter(
    tags=["News"],
)


# =============================================================================
# GET /api/stocks/{symbol}/news - Obtener noticias de un stock
# =============================================================================

@router.get(
    "/stocks/{symbol}/news",
    response_model=NewsArticleListResponse,
    summary="Obtener noticias de un stock",
    description="Obtiene las noticias archivadas relacionadas con un stock específico.",
    responses={
        200: {
            "description": "Noticias obtenidas exitosamente",
            "model": NewsArticleListResponse
        },
        404: {
            "description": "Stock no encontrado",
            "model": ErrorResponse
        }
    }
)
async def get_stock_news(
    symbol: str,
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Número máximo de noticias a devolver (1-100, default: 10)"
    ),
    db: DatabaseService = Depends(get_db)
):
    """
    Obtiene las noticias archivadas de un stock.

    Parámetros:
    - **symbol**: Símbolo del stock (ej: TSLA, AAPL)
    - **limit**: Número máximo de noticias (default: 10, máx: 100)

    Retorna:
    - **symbol**: Símbolo del stock
    - **total**: Número de noticias encontradas
    - **news**: Lista de noticias ordenadas por fecha de obtención (más reciente primero)

    Errores:
    - **404**: Si el stock no existe

    Las noticias incluyen:
    - Título y descripción
    - URL de la noticia original
    - Fecha de publicación
    - Fecha en que se guardó
    """
    # Verificar que el stock existe
    stock = db.get_stock_by_symbol(symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock con símbolo '{symbol.upper()}' no encontrado"
        )

    # Obtener noticias del stock
    news = db.get_news_for_stock(symbol, limit=limit)

    return NewsArticleListResponse(
        symbol=symbol.upper(),
        total=len(news),
        news=news
    )


# =============================================================================
# POST /api/stocks/{symbol}/news - Guardar noticia manualmente
# =============================================================================

@router.post(
    "/stocks/{symbol}/news",
    response_model=NewsArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Guardar noticia manualmente",
    description="Guarda una noticia relacionada con un stock. Útil para testing o integración manual.",
    responses={
        201: {
            "description": "Noticia guardada exitosamente",
            "model": NewsArticleResponse
        },
        404: {
            "description": "Stock no encontrado",
            "model": ErrorResponse
        },
        400: {
            "description": "Error al guardar la noticia",
            "model": ErrorResponse
        }
    }
)
async def save_news_article(
    symbol: str,
    news_data: NewsArticleCreate,
    db: DatabaseService = Depends(get_db)
):
    """
    Guarda una noticia relacionada con un stock.

    **⚠️ Nota**: En producción, las noticias se obtienen automáticamente de APIs
    como NewsAPI. Este endpoint es útil para:
    - Testing y desarrollo
    - Integración manual de noticias
    - Importación de datos históricos

    Parámetros:
    - **symbol**: Símbolo del stock

    Body (JSON):
    - **title**: Título de la noticia (obligatorio, 1-500 caracteres)
    - **description**: Descripción o resumen (opcional, máx 2000 caracteres)
    - **url**: URL de la noticia original (opcional, máx 1000 caracteres)
    - **image_url**: URL de la imagen de la noticia (opcional, máx 1000 caracteres)
    - **source**: Fuente de la noticia (opcional, máx 200 caracteres)
    - **published_at**: Fecha de publicación (opcional, ISO 8601)

    Retorna:
    - La noticia guardada con su ID y fecha de guardado

    Errores:
    - **404**: Si el stock no existe
    - **400**: Si hay error al guardar
    """
    # Verificar que el stock existe
    stock = db.get_stock_by_symbol(symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock con símbolo '{symbol.upper()}' no encontrado"
        )

    # Guardar la noticia
    try:
        article = db.save_news_article(
            symbol=symbol,
            title=news_data.title,
            description=news_data.description,
            url=news_data.url,
            image_url=news_data.image_url,
            source=news_data.source,
            published_at=news_data.published_at
        )

        if not article:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al guardar la noticia"
            )

        return article

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al guardar la noticia: {str(e)}"
        )
