"""
Router para endpoints del dashboard.

Este módulo contiene endpoints que proporcionan estadísticas y resúmenes
generales del sistema para mostrar en el dashboard principal.
"""

from fastapi import APIRouter, Depends

from ...database import DatabaseService
from ..dependencies import get_db
from ..schemas import DashboardSummaryResponse

# Crear router
router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# =============================================================================
# GET /api/dashboard/summary - Resumen general del dashboard
# =============================================================================

@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Obtener resumen del dashboard",
    description="Obtiene estadísticas generales del sistema para el dashboard principal.",
    responses={
        200: {
            "description": "Resumen obtenido exitosamente",
            "model": DashboardSummaryResponse
        }
    }
)
async def get_dashboard_summary(
    db: DatabaseService = Depends(get_db)
):
    """
    Obtiene estadísticas generales del sistema.

    Retorna:
    - **total_stocks**: Número total de stocks configurados
    - **active_stocks**: Número de stocks activos para monitoreo
    - **recent_alerts_24h**: Alertas generadas en las últimas 24 horas
    - **last_price_update**: Fecha de la última actualización de precios

    Este endpoint es útil para:
    - Pantalla principal del dashboard
    - Widgets de estadísticas
    - Monitoreo general del sistema
    """
    summary = db.get_dashboard_summary()

    return DashboardSummaryResponse(
        total_stocks=summary['total_stocks'],
        active_stocks=summary['active_stocks'],
        recent_alerts_24h=summary['recent_alerts_24h'],
        last_price_update=summary['last_price_update']
    )
