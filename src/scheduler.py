"""
Servicio de Scheduler para actualizaciones automáticas de precios.

Este módulo configura APScheduler para ejecutar tareas periódicas como
la actualización automática de precios de stocks cada 15 minutos.
"""

import logging
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from .database.service import DatabaseService
from .stock_fetcher import StockFetcher

logger = logging.getLogger(__name__)


class PriceUpdateScheduler:
    """
    Scheduler para actualizaciones automáticas de precios.

    Utiliza APScheduler en modo background para ejecutar actualizaciones
    periódicas sin bloquear la aplicación FastAPI.
    """

    def __init__(self, db_service: DatabaseService, hour: int = 18, minute: int = 0):
        """
        Inicializa el scheduler.

        Args:
            db_service: Instancia del servicio de base de datos
            hour: Hora del día para ejecutar actualización (0-23, default: 18 = 6 PM)
            minute: Minuto de la hora para ejecutar (0-59, default: 0)
        """
        self.db_service = db_service
        self.hour = hour
        self.minute = minute
        self.scheduler: Optional[BackgroundScheduler] = None
        self.stock_fetcher = StockFetcher()

    def start(self):
        """
        Inicia el scheduler en modo background.

        Configura un trigger diario para ejecutar update_all_prices()
        una vez al día a la hora especificada (después del cierre de mercado).
        """
        if self.scheduler is not None:
            logger.warning("Scheduler already started")
            return

        self.scheduler = BackgroundScheduler(
            timezone="UTC",
            job_defaults={
                'coalesce': True,  # Combinar ejecuciones perdidas
                'max_instances': 1,  # Solo una instancia del job a la vez
                'misfire_grace_time': 3600  # 1 hora de gracia para ejecuciones perdidas
            }
        )

        # Añadir job de actualización de precios (diario)
        self.scheduler.add_job(
            func=self._update_all_prices_job,
            trigger=CronTrigger(hour=self.hour, minute=self.minute, timezone="UTC"),
            id='update_stock_prices',
            name='Update all stock prices',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"Scheduler started - will update prices daily at {self.hour:02d}:{self.minute:02d} UTC")

    def stop(self):
        """
        Detiene el scheduler de forma segura.

        Espera a que terminen los jobs en ejecución antes de apagar.
        """
        if self.scheduler is None:
            logger.warning("Scheduler not started")
            return

        self.scheduler.shutdown(wait=True)
        self.scheduler = None
        logger.info("Scheduler stopped")

    def _update_all_prices_job(self):
        """
        Job que actualiza precios de todos los stocks activos.

        Esta función se ejecuta periódicamente según el intervalo configurado.
        Obtiene todos los stocks activos y actualiza sus precios usando
        Alpha Vantage API.
        """
        try:
            logger.info("=" * 70)
            logger.info(f"SCHEDULED PRICE UPDATE - {datetime.utcnow().isoformat()}")
            logger.info("=" * 70)

            # Obtener stocks activos
            stocks = self.db_service.get_all_stocks(only_active=True)

            if not stocks:
                logger.info("No active stocks to update")
                return

            logger.info(f"Updating prices for {len(stocks)} active stocks")

            updated = 0
            failed = 0
            alerts_triggered = 0

            # Actualizar cada stock
            for stock in stocks:
                try:
                    # Obtener cambio porcentual y precios usando StockFetcher
                    percentage_change, yesterday_close, day_before_close, dates = \
                        self.stock_fetcher.get_percentage_change(stock.symbol)

                    if percentage_change is None or yesterday_close is None:
                        logger.error(f"Failed to get price for {stock.symbol}")
                        failed += 1
                        continue

                    current_price = yesterday_close
                    previous_price = day_before_close if day_before_close else yesterday_close

                    # Guardar precio en histórico
                    self.db_service.add_price_to_history(
                        symbol=stock.symbol,
                        close_price=current_price,
                        previous_close=previous_price,
                        percentage_change=percentage_change
                    )

                    logger.info(f"✓ {stock.symbol}: ${current_price:.2f} ({percentage_change:+.2f}%)")
                    updated += 1

                    # Verificar si se debe crear alerta
                    if abs(percentage_change) >= stock.threshold:
                        # Verificar si ya existe alerta similar reciente
                        existing_alert = self.db_service.check_existing_alert(
                            stock_id=stock.id,
                            price_before=previous_price,
                            price_after=current_price,
                            hours=24
                        )

                        if not existing_alert:
                            # Crear nueva alerta
                            self.db_service.create_alert(
                                stock_id=stock.id,
                                threshold_at_time=stock.threshold,
                                percentage_change=percentage_change,
                                price_before=previous_price,
                                price_after=current_price
                            )

                            logger.warning(
                                f"🚨 ALERT: {stock.symbol} changed {percentage_change:+.2f}% "
                                f"(threshold: {stock.threshold}%)"
                            )
                            alerts_triggered += 1
                        else:
                            logger.info(f"  Alert already exists for {stock.symbol}")

                except Exception as e:
                    logger.error(f"Error updating {stock.symbol}: {str(e)}")
                    failed += 1
                    continue

            # Log resumen
            logger.info("=" * 70)
            logger.info(f"UPDATE COMPLETE - Updated: {updated}, Failed: {failed}, Alerts: {alerts_triggered}")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Error in scheduled price update: {str(e)}", exc_info=True)


# Instancia global del scheduler (se inicializa en startup de FastAPI)
_scheduler_instance: Optional[PriceUpdateScheduler] = None


def get_scheduler() -> Optional[PriceUpdateScheduler]:
    """Obtiene la instancia global del scheduler."""
    return _scheduler_instance


def set_scheduler(scheduler: PriceUpdateScheduler):
    """Establece la instancia global del scheduler."""
    global _scheduler_instance
    _scheduler_instance = scheduler
