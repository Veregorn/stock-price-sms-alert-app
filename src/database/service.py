"""
Servicio de base de datos (Repository Pattern).

Encapsula todas las operaciones CRUD para los modelos de la base de datos.
Proporciona una interfaz limpia para interactuar con la persistencia de datos.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Stock, PriceHistory, Alert, NewsArticle
from ..config import config

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Servicio de acceso a base de datos.

    Implementa el patrón Repository para centralizar todas las operaciones
    de base de datos. Maneja la conexión, sesiones y transacciones.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Inicializa el servicio de base de datos.

        Args:
            database_url: URL de conexión a la base de datos.
                         Si no se proporciona, usa la configuración por defecto.
        """
        # Usar URL proporcionada o la de configuración
        self.database_url = database_url or config.DATABASE_URL

        # Crear engine de SQLAlchemy
        # echo=False desactiva el logging de SQL (para producción)
        self.engine = create_engine(
            self.database_url,
            echo=config.DATABASE_ECHO
        )

        # Crear fábrica de sesiones
        # Las sesiones son la forma de interactuar con la BD en SQLAlchemy
        self.SessionLocal = sessionmaker(
            autocommit=False,  # Las transacciones se controlan manualmente
            autoflush=False,   # No hacer flush automático
            bind=self.engine
        )

        logger.info(f"DatabaseService inicializado con: {self.database_url}")

    def create_tables(self):
        """
        Crea todas las tablas definidas en los modelos.

        Este método es idempotente: si las tablas ya existen, no hace nada.
        """
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Tablas de base de datos creadas/verificadas correctamente")
        except SQLAlchemyError as e:
            logger.error(f"Error al crear tablas: {str(e)}")
            raise

    def drop_tables(self):
        """
        Elimina todas las tablas de la base de datos.

        ⚠️  CUIDADO: Esta operación es destructiva e irreversible.
        Solo usar en desarrollo o tests.
        """
        try:
            Base.metadata.drop_all(self.engine)
            logger.warning("Todas las tablas han sido eliminadas")
        except SQLAlchemyError as e:
            logger.error(f"Error al eliminar tablas: {str(e)}")
            raise

    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager para obtener una sesión de base de datos.

        Garantiza que la sesión se cierre correctamente incluso si hay errores.

        Uso:
            with db_service.get_session() as session:
                stock = session.query(Stock).first()

        Yields:
            Session de SQLAlchemy
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()  # Commit automático si todo va bien
        except Exception as e:
            session.rollback()  # Rollback si hay error
            logger.error(f"Error en sesión de BD: {str(e)}")
            raise
        finally:
            session.close()  # Siempre cerrar la sesión

    # =========================================================================
    # OPERACIONES CRUD PARA STOCK
    # =========================================================================

    def create_stock(
        self,
        symbol: str,
        company_name: str,
        threshold: float,
        is_active: bool = True
    ) -> Stock:
        """
        Crea un nuevo stock en la base de datos.

        Args:
            symbol: Símbolo del stock (ej: 'TSLA')
            company_name: Nombre de la compañía
            threshold: Umbral de alerta en porcentaje
            is_active: Si el stock está activo para monitoreo

        Returns:
            Objeto Stock creado

        Raises:
            SQLAlchemyError: Si hay error al insertar
        """
        with self.get_session() as session:
            stock = Stock(
                symbol=symbol.upper(),  # Normalizar a mayúsculas
                company_name=company_name,
                threshold=threshold,
                is_active=is_active
            )
            session.add(stock)
            session.flush()  # Forzar el INSERT para obtener el ID

            # Forzar la carga de todos los atributos antes de hacer expunge
            session.refresh(stock)

            logger.info(f"Stock creado: {stock}")
            session.expunge(stock)  # Ahora sí podemos hacer expunge
            return stock

    def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """
        Obtiene un stock por su símbolo.

        Args:
            symbol: Símbolo del stock (ej: 'TSLA')

        Returns:
            Objeto Stock o None si no existe
        """
        with self.get_session() as session:
            stock = session.query(Stock).filter(
                Stock.symbol == symbol.upper()
            ).first()

            if stock:
                # Forzar la carga de todos los atributos antes de hacer expunge
                session.refresh(stock)
                # Hacer detach para poder usar fuera de la sesión
                session.expunge(stock)

            return stock

    def get_all_stocks(self, only_active: bool = False) -> List[Stock]:
        """
        Obtiene todos los stocks de la base de datos.

        Args:
            only_active: Si True, solo devuelve stocks activos

        Returns:
            Lista de objetos Stock
        """
        with self.get_session() as session:
            query = session.query(Stock)

            if only_active:
                query = query.filter(Stock.is_active == True)

            stocks = query.order_by(Stock.symbol).all()

            # Forzar la carga de todos los atributos antes de hacer expunge
            for stock in stocks:
                session.refresh(stock)
                session.expunge(stock)

            return stocks

    def update_stock(
        self,
        symbol: str,
        **kwargs
    ) -> Optional[Stock]:
        """
        Actualiza un stock existente.

        Args:
            symbol: Símbolo del stock a actualizar
            **kwargs: Campos a actualizar (company_name, threshold, is_active)

        Returns:
            Stock actualizado o None si no existe
        """
        with self.get_session() as session:
            stock = session.query(Stock).filter(
                Stock.symbol == symbol.upper()
            ).first()

            if not stock:
                logger.warning(f"Stock {symbol} no encontrado para actualizar")
                return None

            # Actualizar campos proporcionados
            for key, value in kwargs.items():
                if hasattr(stock, key):
                    setattr(stock, key, value)

            stock.updated_at = datetime.utcnow()
            session.flush()

            # Forzar la carga de todos los atributos antes de hacer expunge
            session.refresh(stock)

            logger.info(f"Stock actualizado: {stock}")
            session.expunge(stock)
            return stock

    def delete_stock(self, symbol: str) -> bool:
        """
        Elimina un stock de la base de datos.

        ⚠️  También eliminará todos los datos relacionados (precios, alertas, noticias)
        debido a las cascadas definidas en los modelos.

        Args:
            symbol: Símbolo del stock a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        with self.get_session() as session:
            stock = session.query(Stock).filter(
                Stock.symbol == symbol.upper()
            ).first()

            if not stock:
                logger.warning(f"Stock {symbol} no encontrado para eliminar")
                return False

            session.delete(stock)
            logger.info(f"Stock eliminado: {symbol}")
            return True

    # =========================================================================
    # OPERACIONES PARA PRICE HISTORY
    # =========================================================================

    def add_price_history(
        self,
        symbol: str,
        date: datetime,
        close_price: float,
        previous_close: Optional[float] = None,
        percentage_change: Optional[float] = None
    ) -> Optional[PriceHistory]:
        """
        Añade un registro de precio histórico.

        Args:
            symbol: Símbolo del stock
            date: Fecha del precio
            close_price: Precio de cierre
            previous_close: Precio de cierre anterior
            percentage_change: Cambio porcentual

        Returns:
            Objeto PriceHistory creado o None si el stock no existe
        """
        stock = self.get_stock_by_symbol(symbol)
        if not stock:
            logger.error(f"No se puede añadir precio: stock {symbol} no existe")
            return None

        with self.get_session() as session:
            price = PriceHistory(
                stock_id=stock.id,
                date=date,
                close_price=close_price,
                previous_close=previous_close,
                percentage_change=percentage_change
            )
            session.add(price)
            session.flush()

            # Forzar la carga de todos los atributos antes de hacer expunge
            session.refresh(price)

            logger.debug(f"Precio histórico añadido: {price}")
            session.expunge(price)
            return price

    def get_price_history(
        self,
        symbol: str,
        days: int = 30
    ) -> List[PriceHistory]:
        """
        Obtiene el histórico de precios de un stock.

        Args:
            symbol: Símbolo del stock
            days: Número de días hacia atrás

        Returns:
            Lista de PriceHistory ordenada por fecha (más reciente primero)
        """
        stock = self.get_stock_by_symbol(symbol)
        if not stock:
            return []

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with self.get_session() as session:
            prices = session.query(PriceHistory).filter(
                PriceHistory.stock_id == stock.id,
                PriceHistory.date >= cutoff_date
            ).order_by(desc(PriceHistory.date)).all()

            # Forzar la carga de todos los atributos antes de hacer expunge
            for price in prices:
                session.refresh(price)
                session.expunge(price)

            return prices

    # =========================================================================
    # OPERACIONES PARA ALERTS
    # =========================================================================

    def create_alert(
        self,
        symbol: str,
        percentage_change: float,
        threshold_at_time: float,
        price_before: Optional[float] = None,
        price_after: Optional[float] = None,
        message_sent: bool = False,
        notification_type: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[Alert]:
        """
        Registra una alerta disparada.

        Args:
            symbol: Símbolo del stock
            percentage_change: Cambio porcentual que disparó la alerta
            threshold_at_time: Umbral configurado en ese momento
            price_before: Precio anterior
            price_after: Precio nuevo
            message_sent: Si se envió el mensaje exitosamente
            notification_type: 'whatsapp' o 'sms'
            error_message: Mensaje de error si falló el envío

        Returns:
            Objeto Alert creado o None si el stock no existe
        """
        stock = self.get_stock_by_symbol(symbol)
        if not stock:
            logger.error(f"No se puede crear alerta: stock {symbol} no existe")
            return None

        with self.get_session() as session:
            alert = Alert(
                stock_id=stock.id,
                percentage_change=percentage_change,
                threshold_at_time=threshold_at_time,
                price_before=price_before,
                price_after=price_after,
                message_sent=message_sent,
                notification_type=notification_type,
                error_message=error_message
            )
            session.add(alert)
            session.flush()

            # Forzar la carga de todos los atributos antes de hacer expunge
            session.refresh(alert)

            logger.info(f"Alerta registrada: {alert}")
            session.expunge(alert)
            return alert

    def has_alert_for_price_date(
        self,
        symbol: str,
        price_date: datetime,
        price_before: float,
        price_after: float
    ) -> bool:
        """
        Verifica si ya existe una alerta para un stock con los mismos precios.

        Como Alpha Vantage retorna datos diarios (no por hora), queremos evitar
        crear alertas duplicadas si el endpoint se ejecuta varias veces el mismo día.
        Comparamos por los precios before/after que son únicos para cada cierre diario.

        Args:
            symbol: Símbolo del stock
            price_date: Fecha del precio (para logging/debugging)
            price_before: Precio anterior (cierre del día previo)
            price_after: Precio nuevo (cierre del día)

        Returns:
            True si existe una alerta con esos precios, False en caso contrario
        """
        stock = self.get_stock_by_symbol(symbol)
        if not stock:
            return False

        with self.get_session() as session:
            # Buscar alertas del stock con los mismos precios
            # Usamos tolerancia para comparación de floats
            tolerance = 0.001

            alert = session.query(Alert).filter(
                Alert.stock_id == stock.id,
                Alert.price_before.between(price_before - tolerance, price_before + tolerance),
                Alert.price_after.between(price_after - tolerance, price_after + tolerance)
            ).first()

            return alert is not None

    def get_recent_alerts(
        self,
        symbol: Optional[str] = None,
        days: int = 7
    ) -> List[Alert]:
        """
        Obtiene alertas recientes.

        Args:
            symbol: Si se proporciona, filtra por ese stock
            days: Número de días hacia atrás

        Returns:
            Lista de Alert ordenada por fecha (más reciente primero)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with self.get_session() as session:
            query = session.query(Alert).filter(
                Alert.triggered_at >= cutoff_date
            )

            if symbol:
                stock = self.get_stock_by_symbol(symbol)
                if stock:
                    query = query.filter(Alert.stock_id == stock.id)

            alerts = query.order_by(desc(Alert.triggered_at)).all()

            # Forzar la carga de todos los atributos antes de hacer expunge
            for alert in alerts:
                session.refresh(alert)
                session.expunge(alert)

            return alerts

    # =========================================================================
    # OPERACIONES PARA NEWS ARTICLES
    # =========================================================================

    def has_news_article_by_url(
        self,
        symbol: str,
        url: str
    ) -> bool:
        """
        Verifica si ya existe una noticia con la misma URL para un stock.

        La URL es el identificador único más confiable para detectar duplicados,
        ya que no cambia aunque el título o descripción se actualicen.

        Args:
            symbol: Símbolo del stock
            url: URL de la noticia

        Returns:
            True si existe una noticia con esa URL, False en caso contrario
        """
        if not url:
            # Si no hay URL, no podemos verificar duplicados de forma confiable
            return False

        stock = self.get_stock_by_symbol(symbol)
        if not stock:
            return False

        with self.get_session() as session:
            article = session.query(NewsArticle).filter(
                NewsArticle.stock_id == stock.id,
                NewsArticle.url == url
            ).first()

            return article is not None

    def save_news_article(
        self,
        symbol: str,
        title: str,
        description: Optional[str] = None,
        url: Optional[str] = None,
        image_url: Optional[str] = None,
        source: Optional[str] = None,
        published_at: Optional[datetime] = None,
        photographer_name: Optional[str] = None,
        photographer_username: Optional[str] = None,
        photographer_url: Optional[str] = None,
        unsplash_download_location: Optional[str] = None
    ) -> Optional[NewsArticle]:
        """
        Guarda una noticia relacionada con un stock.

        Args:
            symbol: Símbolo del stock
            title: Título de la noticia
            description: Descripción o resumen
            url: URL de la noticia
            image_url: URL de la imagen de la noticia
            source: Fuente de la noticia
            published_at: Fecha de publicación
            photographer_name: Nombre del fotógrafo (Unsplash)
            photographer_username: Username del fotógrafo (Unsplash)
            photographer_url: URL del perfil del fotógrafo (Unsplash)
            unsplash_download_location: Endpoint para trigger download event (Unsplash)

        Returns:
            Objeto NewsArticle creado o None si el stock no existe
        """
        stock = self.get_stock_by_symbol(symbol)
        if not stock:
            logger.error(f"No se puede guardar noticia: stock {symbol} no existe")
            return None

        with self.get_session() as session:
            article = NewsArticle(
                stock_id=stock.id,
                title=title,
                description=description,
                url=url,
                image_url=image_url,
                source=source,
                published_at=published_at,
                photographer_name=photographer_name,
                photographer_username=photographer_username,
                photographer_url=photographer_url,
                unsplash_download_location=unsplash_download_location
            )
            session.add(article)
            session.flush()

            # Forzar la carga de todos los atributos antes de hacer expunge
            session.refresh(article)

            logger.debug(f"Noticia guardada para {symbol}: {title[:50]}...")
            session.expunge(article)
            return article

    def get_news_for_stock(
        self,
        symbol: str,
        limit: int = 10
    ) -> List[NewsArticle]:
        """
        Obtiene noticias archivadas de un stock.

        Args:
            symbol: Símbolo del stock
            limit: Número máximo de noticias a devolver

        Returns:
            Lista de NewsArticle ordenada por fecha de obtención (más reciente primero)
        """
        stock = self.get_stock_by_symbol(symbol)
        if not stock:
            return []

        with self.get_session() as session:
            articles = session.query(NewsArticle).filter(
                NewsArticle.stock_id == stock.id
            ).order_by(desc(NewsArticle.fetched_at)).limit(limit).all()

            # Forzar la carga de todos los atributos antes de hacer expunge
            for article in articles:
                session.refresh(article)
                session.expunge(article)

            return articles

    # =========================================================================
    # UTILIDADES Y ESTADÍSTICAS
    # =========================================================================

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen para el dashboard.

        Returns:
            Diccionario con estadísticas generales
        """
        with self.get_session() as session:
            total_stocks = session.query(Stock).count()
            active_stocks = session.query(Stock).filter(Stock.is_active == True).count()

            # Alertas en las últimas 24 horas
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_alerts = session.query(Alert).filter(
                Alert.triggered_at >= yesterday
            ).count()

            # Última actualización de precios
            last_price = session.query(PriceHistory).order_by(
                desc(PriceHistory.created_at)
            ).first()

            return {
                'total_stocks': total_stocks,
                'active_stocks': active_stocks,
                'recent_alerts_24h': recent_alerts,
                'last_price_update': last_price.created_at if last_price else None
            }

    def close(self):
        """
        Cierra el engine de la base de datos.

        Solo necesario si se quiere cerrar explícitamente la conexión.
        """
        self.engine.dispose()
        logger.info("Conexión de base de datos cerrada")
