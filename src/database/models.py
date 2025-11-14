"""
Modelos de base de datos SQLAlchemy.

Define las tablas y relaciones para almacenar:
- Configuración de stocks
- Histórico de precios
- Alertas enviadas
- Noticias archivadas
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Base declarativa para todos los modelos
# Todos los modelos heredarán de esta clase
Base = declarative_base()


class Stock(Base):
    """
    Modelo para almacenar la configuración de stocks monitoreados.

    Representa un stock que queremos monitorear con su símbolo,
    nombre de compañía y umbral de alerta configurado.
    """
    __tablename__ = 'stocks'

    # Columnas de la tabla
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)  # Ej: TSLA, AAPL
    company_name = Column(String(100), nullable=False)  # Ej: Tesla Inc
    threshold = Column(Float, nullable=False)  # Umbral de alerta en porcentaje
    is_active = Column(Boolean, default=True)  # Si está activo para monitoreo
    created_at = Column(DateTime, default=datetime.utcnow)  # Fecha de creación
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones: Un stock tiene muchos precios históricos
    price_history = relationship('PriceHistory', back_populates='stock', cascade='all, delete-orphan')

    # Relaciones: Un stock tiene muchas alertas
    alerts = relationship('Alert', back_populates='stock', cascade='all, delete-orphan')

    # Relaciones: Un stock tiene muchas noticias
    news_articles = relationship('NewsArticle', back_populates='stock', cascade='all, delete-orphan')

    def __repr__(self):
        """Representación legible del objeto Stock."""
        return f"<Stock(symbol='{self.symbol}', company='{self.company_name}', threshold={self.threshold}%)>"


class PriceHistory(Base):
    """
    Modelo para almacenar el histórico de precios de cada stock.

    Guarda el precio de cierre, cambio porcentual y metadatos
    para cada día que se consulta el stock.
    """
    __tablename__ = 'price_history'

    # Columnas de la tabla
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)  # Referencia al stock
    date = Column(DateTime, nullable=False, index=True)  # Fecha del precio
    close_price = Column(Float, nullable=False)  # Precio de cierre
    previous_close = Column(Float)  # Precio de cierre anterior
    percentage_change = Column(Float)  # Cambio porcentual calculado
    created_at = Column(DateTime, default=datetime.utcnow)  # Cuándo se guardó este registro

    # Relación inversa: Este precio pertenece a un stock
    stock = relationship('Stock', back_populates='price_history')

    def __repr__(self):
        """Representación legible del objeto PriceHistory."""
        return (f"<PriceHistory(stock_id={self.stock_id}, date={self.date.date()}, "
                f"price=${self.close_price:.2f}, change={self.percentage_change:+.2f}%)>")


class Alert(Base):
    """
    Modelo para registrar las alertas enviadas.

    Almacena un registro de cada vez que se envía una alerta,
    incluyendo el motivo, el cambio detectado y si se envió exitosamente.
    """
    __tablename__ = 'alerts'

    # Columnas de la tabla
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)  # Cuándo se disparó
    percentage_change = Column(Float, nullable=False)  # Cambio que causó la alerta
    threshold_at_time = Column(Float, nullable=False)  # Umbral configurado en ese momento
    price_before = Column(Float)  # Precio anterior
    price_after = Column(Float)  # Precio nuevo
    message_sent = Column(Boolean, default=False)  # Si se envió el mensaje
    notification_type = Column(String(20))  # 'whatsapp' o 'sms'
    error_message = Column(Text)  # Si hubo error al enviar

    # Relación inversa: Esta alerta pertenece a un stock
    stock = relationship('Stock', back_populates='alerts')

    def __repr__(self):
        """Representación legible del objeto Alert."""
        sent = "✓" if self.message_sent else "✗"
        return (f"<Alert({sent} stock_id={self.stock_id}, "
                f"change={self.percentage_change:+.2f}%, at={self.triggered_at.date()})>")


class NewsArticle(Base):
    """
    Modelo para archivar noticias relacionadas con los stocks.

    Guarda las noticias obtenidas cuando se dispara una alerta,
    permitiendo consultar el contexto histórico.
    """
    __tablename__ = 'news_articles'

    # Columnas de la tabla
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    title = Column(String(500), nullable=False)  # Título de la noticia
    description = Column(Text)  # Descripción o resumen
    url = Column(String(1000))  # URL a la noticia original
    published_at = Column(DateTime)  # Fecha de publicación de la noticia
    fetched_at = Column(DateTime, default=datetime.utcnow)  # Cuándo la obtuvimos

    # Relación inversa: Esta noticia pertenece a un stock
    stock = relationship('Stock', back_populates='news_articles')

    def __repr__(self):
        """Representación legible del objeto NewsArticle."""
        return f"<NewsArticle(stock_id={self.stock_id}, title='{self.title[:50]}...')>"


# Función helper para crear todas las tablas
def create_tables(engine):
    """
    Crea todas las tablas definidas en los modelos.

    Args:
        engine: Engine de SQLAlchemy conectado a la base de datos
    """
    Base.metadata.create_all(engine)


# Función helper para borrar todas las tablas (útil para testing)
def drop_tables(engine):
    """
    Elimina todas las tablas definidas en los modelos.

    Args:
        engine: Engine de SQLAlchemy conectado a la base de datos
    """
    Base.metadata.drop_all(engine)
