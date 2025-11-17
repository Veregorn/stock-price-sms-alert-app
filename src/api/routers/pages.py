"""
Router para servir páginas HTML del frontend.

Este módulo contiene los endpoints que sirven las páginas HTML
utilizando templates Jinja2.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from pathlib import Path

from ..dependencies import get_db
from ...database.service import DatabaseService

# Configurar templates
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["Pages"])


@router.get("/dashboard", response_class=HTMLResponse)
async def home_page(request: Request):
    """
    Página principal - Dashboard.

    Muestra el dashboard con estadísticas generales del sistema.
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "page": "dashboard"}
    )


@router.get("/stocks", response_class=HTMLResponse)
async def stocks_page(request: Request):
    """
    Página de gestión de stocks.

    Permite visualizar, crear, editar y eliminar stocks.
    """
    return templates.TemplateResponse(
        "stocks.html",
        {"request": request, "page": "stocks"}
    )


@router.get("/stocks/{symbol}/prices", response_class=HTMLResponse)
async def price_history_page(request: Request, symbol: str):
    """
    Página de histórico de precios.

    Muestra el histórico de precios de un stock con gráficos.
    """
    return templates.TemplateResponse(
        "price_history.html",
        {"request": request, "page": "prices", "symbol": symbol.upper()}
    )


@router.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    """
    Página de alertas.

    Muestra el listado de alertas generadas por el sistema.
    """
    return templates.TemplateResponse(
        "alerts.html",
        {"request": request, "page": "alerts"}
    )


@router.get("/news", response_class=HTMLResponse)
async def news_page(request: Request):
    """
    Página de noticias.

    Muestra las noticias archivadas de los stocks.
    """
    return templates.TemplateResponse(
        "news.html",
        {"request": request, "page": "news"}
    )
