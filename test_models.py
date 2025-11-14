"""
Script de prueba para verificar que los modelos de base de datos funcionan.

Este script:
1. Crea una base de datos temporal
2. Crea las tablas
3. Inserta datos de prueba
4. Realiza consultas básicas
5. Limpia todo al finalizar
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from src.database.models import Base, Stock, PriceHistory, Alert, NewsArticle

print("=" * 70)
print("🧪 TEST DE MODELOS DE BASE DE DATOS")
print("=" * 70)

# 1. Crear engine de base de datos en memoria (temporal)
print("\n1. Creando base de datos temporal en memoria...")
engine = create_engine('sqlite:///:memory:', echo=False)
print("   ✅ Engine creado")

# 2. Crear todas las tablas
print("\n2. Creando tablas...")
Base.metadata.create_all(engine)
print("   ✅ Tablas creadas:")
for table_name in Base.metadata.tables.keys():
    print(f"      - {table_name}")

# 3. Crear sesión para interactuar con la BD
print("\n3. Creando sesión de base de datos...")
Session = sessionmaker(bind=engine)
session = Session()
print("   ✅ Sesión creada")

# 4. Insertar datos de prueba
print("\n4. Insertando datos de prueba...")

# Crear un stock
stock_tsla = Stock(
    symbol='TSLA',
    company_name='Tesla Inc',
    threshold=5.0,
    is_active=True
)
session.add(stock_tsla)
session.commit()
print(f"   ✅ Stock creado: {stock_tsla}")

# Crear histórico de precios
price1 = PriceHistory(
    stock_id=stock_tsla.id,
    date=datetime.now() - timedelta(days=1),
    close_price=250.00,
    previous_close=240.00,
    percentage_change=4.17
)
price2 = PriceHistory(
    stock_id=stock_tsla.id,
    date=datetime.now(),
    close_price=265.00,
    previous_close=250.00,
    percentage_change=6.0
)
session.add_all([price1, price2])
session.commit()
print(f"   ✅ Precios históricos creados: {len([price1, price2])}")

# Crear una alerta
alert = Alert(
    stock_id=stock_tsla.id,
    percentage_change=6.0,
    threshold_at_time=5.0,
    price_before=250.00,
    price_after=265.00,
    message_sent=True,
    notification_type='whatsapp'
)
session.add(alert)
session.commit()
print(f"   ✅ Alerta creada: {alert}")

# Crear una noticia
news = NewsArticle(
    stock_id=stock_tsla.id,
    title='Tesla Stock Surges to New Highs',
    description='Tesla shares reached record levels today...',
    url='https://example.com/news/1',
    published_at=datetime.now()
)
session.add(news)
session.commit()
print(f"   ✅ Noticia creada: {news}")

# 5. Realizar consultas de prueba
print("\n5. Realizando consultas de prueba...")

# Consulta 1: Todos los stocks activos
active_stocks = session.query(Stock).filter(Stock.is_active == True).all()
print(f"   ✅ Stocks activos encontrados: {len(active_stocks)}")
for stock in active_stocks:
    print(f"      {stock}")

# Consulta 2: Histórico de precios de TSLA
tsla_prices = session.query(PriceHistory).filter(
    PriceHistory.stock_id == stock_tsla.id
).order_by(PriceHistory.date).all()
print(f"   ✅ Precios históricos de TSLA: {len(tsla_prices)}")
for price in tsla_prices:
    print(f"      {price}")

# Consulta 3: Alertas enviadas
sent_alerts = session.query(Alert).filter(Alert.message_sent == True).all()
print(f"   ✅ Alertas enviadas: {len(sent_alerts)}")
for alert in sent_alerts:
    print(f"      {alert}")

# Consulta 4: Usar relaciones (de stock a precios)
print(f"\n   ✅ Usando relaciones ORM:")
print(f"      Stock TSLA tiene {len(stock_tsla.price_history)} precios históricos")
print(f"      Stock TSLA tiene {len(stock_tsla.alerts)} alertas")
print(f"      Stock TSLA tiene {len(stock_tsla.news_articles)} noticias")

# 6. Limpiar
print("\n6. Limpiando...")
session.close()
print("   ✅ Sesión cerrada")

print("\n" + "=" * 70)
print("✅ TODOS LOS TESTS PASARON CORRECTAMENTE")
print("=" * 70)
