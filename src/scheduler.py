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

        # Añadir job de actualización de noticias (diario a las 08:00 UTC)
        self.scheduler.add_job(
            func=self._update_all_news_job,
            trigger=CronTrigger(hour=8, minute=0, timezone="UTC"),
            id='update_stock_news',
            name='Update all stock news',
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

    def _update_all_news_job(self):
        """
        Job que actualiza noticias de todos los stocks activos.
        
        Esta función se ejecuta periódicamente (diariamente a las 08:00 UTC).
        Obtiene noticias recientes para cada stock activo y las guarda en la base de datos.
        """
        try:
            logger.info("=" * 70)
            logger.info(f"SCHEDULED NEWS UPDATE - {datetime.utcnow().isoformat()}")
            logger.info("=" * 70)

            # Obtener stocks activos
            stocks = self.db_service.get_all_stocks(only_active=True)

            if not stocks:
                logger.info("No active stocks to update news for")
                return

            logger.info(f"Updating news for {len(stocks)} active stocks")

            # Inicializar fetchers
            from .news_fetcher import NewsFetcher
            from .image_fetcher import ImageFetcher
            
            news_fetcher = NewsFetcher()
            image_fetcher = ImageFetcher()

            updated = 0
            failed = 0
            total_saved = 0

            # Actualizar cada stock
            for stock in stocks:
                try:
                    # Obtener noticias (limit 5 por stock para no saturar API)
                    articles = news_fetcher.get_articles(stock.company_name, limit=5)
                    
                    if not articles:
                        logger.info(f"No news found for {stock.symbol}")
                        continue

                    saved_count = 0
                    
                    for article in articles:
                        try:
                            title = article.get("title")
                            if not title:
                                continue

                            url = article.get("url")
                            
                            # Verificar duplicados por URL
                            if url and self.db_service.has_news_article_by_url(stock.symbol, url):
                                continue

                            # Parsear fecha
                            published_at_str = article.get("publishedAt")
                            published_at = None
                            if published_at_str:
                                try:
                                    published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                                except:
                                    pass

                            # Obtener imagen fallback si es necesario
                            image_url = article.get("urlToImage")
                            photographer_name = None
                            photographer_username = None
                            photographer_url = None
                            unsplash_download_location = None

                            if not image_url:
                                unsplash_data = image_fetcher.get_fallback_image(stock.company_name)
                                if unsplash_data:
                                    image_url = unsplash_data["image_url"]
                                    photographer_name = unsplash_data["photographer_name"]
                                    photographer_username = unsplash_data["photographer_username"]
                                    photographer_url = unsplash_data["photographer_url"]
                                    unsplash_download_location = unsplash_data["download_location"]
                                    
                                    # Trigger download event
                                    image_fetcher.trigger_download(unsplash_download_location)

                            # Guardar en BD
                            saved_article = self.db_service.save_news_article(
                                symbol=stock.symbol,
                                title=title,
                                description=article.get("description"),
                                url=url,
                                image_url=image_url,
                                source=article.get("source", {}).get("name"),
                                published_at=published_at,
                                photographer_name=photographer_name,
                                photographer_username=photographer_username,
                                photographer_url=photographer_url,
                                unsplash_download_location=unsplash_download_location
                            )

                            if saved_article:
                                saved_count += 1

                        except Exception as e:
                            logger.error(f"Error saving article for {stock.symbol}: {str(e)}")
                            continue
                    
                    if saved_count > 0:
                        logger.info(f"✓ {stock.symbol}: Saved {saved_count} new articles")
                        updated += 1
                        total_saved += saved_count
                    else:
                        logger.info(f"- {stock.symbol}: No new articles")

                except Exception as e:
                    logger.error(f"Error updating news for {stock.symbol}: {str(e)}")
                    failed += 1
                    continue

            # Log resumen
            logger.info("=" * 70)
            logger.info(f"NEWS UPDATE COMPLETE - Updated: {updated}, Failed: {failed}, Total Saved: {total_saved}")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Error in scheduled news update: {str(e)}", exc_info=True)


# Instancia global del scheduler (se inicializa en startup de FastAPI)
_scheduler_instance: Optional[PriceUpdateScheduler] = None


def get_scheduler() -> Optional[PriceUpdateScheduler]:
    """Obtiene la instancia global del scheduler."""
    return _scheduler_instance


def set_scheduler(scheduler: PriceUpdateScheduler):
    """Establece la instancia global del scheduler."""
    global _scheduler_instance
    _scheduler_instance = scheduler
