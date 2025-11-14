import os
import csv
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import requests
from dotenv import load_dotenv
from twilio.rest import Client

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# ==================== CONFIGURACIÓN DE LOGGING ====================

def setup_logging():
    """
    Configura el sistema de logging con rotación de archivos.
    Logs van tanto a archivo como a consola con diferentes formatos.
    """
    # Crear directorio de logs si no existe
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Nombre del archivo de log con timestamp
    log_file = os.path.join(log_dir, f"stock_monitor_{datetime.now().strftime('%Y%m%d')}.log")

    # Configurar el logger raíz
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Limpiar handlers existentes
    logger.handlers = []

    # Formato para archivo (más detallado)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Formato para consola (más compacto)
    console_formatter = logging.Formatter(
        '%(levelname)-8s | %(message)s'
    )

    # Handler para archivo con rotación (máx 10MB, mantener 5 archivos)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Handler para consola (solo INFO y superior)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Añadir handlers al logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Inicializar logging
logger = setup_logging()

# ==================== CONFIGURACIÓN ====================

# API Keys
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Twilio Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER")

# Configuración
USE_WHATSAPP = True  # True para WhatsApp, False para SMS
STOCKS_CSV_FILE = "stocks.csv"  # Archivo CSV con las acciones a monitorear

# URLs de las APIs
ALPHA_VANTAGE_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_API_ENDPOINT = "https://newsapi.org/v2/everything"


# ==================== FUNCIONES ====================

def load_stocks_from_csv(csv_file):
    """
    Carga la lista de acciones a monitorear desde un archivo CSV.
    Args:
        csv_file: Ruta al archivo CSV
    Returns:
        list: Lista de diccionarios con información de cada acción
    """
    logger.info(f"Loading stocks from {csv_file}")
    stocks = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                stocks.append({
                    'symbol': row['symbol'].strip(),
                    'company_name': row['company_name'].strip(),
                    'threshold': float(row['threshold'])
                })
        logger.info(f"Successfully loaded {len(stocks)} stocks: {[s['symbol'] for s in stocks]}")
        print(f"✅ Cargadas {len(stocks)} acciones desde {csv_file}")
        return stocks
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        print(f"❌ Error: No se encontró el archivo {csv_file}")
        return []
    except Exception as e:
        logger.error(f"Error reading CSV: {str(e)}", exc_info=True)
        print(f"❌ Error al leer CSV: {str(e)}")
        return []


def get_stock_percentage_change(symbol):
    """
    Obtiene el cambio porcentual de una acción entre ayer y anteayer.
    Args:
        symbol: Símbolo de la acción (ej: TSLA)
    Returns:
        tuple: (percentage_change, yesterday_close, day_before_yesterday_close, dates)
    """
    logger.debug(f"Fetching stock data for {symbol}")
    parameters = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(ALPHA_VANTAGE_ENDPOINT, params=parameters, timeout=10)
        response.raise_for_status()
        stock_data = response.json()

        if "Time Series (Daily)" not in stock_data:
            logger.warning(f"No time series data for {symbol}. Response: {stock_data}")
            return None, None, None, None

        # Obtener los dos últimos días de datos
        daily_data = stock_data["Time Series (Daily)"]
        recent_dates = list(daily_data.keys())[:2]

        yesterday_close = float(daily_data[recent_dates[0]]["4. close"])
        day_before_yesterday_close = float(daily_data[recent_dates[1]]["4. close"])

        # Calcular el cambio porcentual
        difference = yesterday_close - day_before_yesterday_close
        percentage_change = (difference / day_before_yesterday_close) * 100

        logger.info(f"{symbol}: ${yesterday_close:.2f} ({percentage_change:+.2f}%)")
        return percentage_change, yesterday_close, day_before_yesterday_close, recent_dates

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching data for {symbol}")
        print(f"   ❌ Error al obtener datos de {symbol}: Timeout")
        return None, None, None, None
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}", exc_info=True)
        print(f"   ❌ Error al obtener datos de {symbol}: {str(e)}")
        return None, None, None, None


def get_news_articles(company_name, limit=3):
    """
    Obtiene noticias más recientes sobre la compañía.
    Args:
        company_name: Nombre de la compañía
        limit: Número de noticias a obtener
    Returns:
        list: Lista de artículos de noticias
    """
    logger.debug(f"Fetching news for {company_name}")
    parameters = {
        "q": company_name,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": limit
    }

    try:
        response = requests.get(NEWS_API_ENDPOINT, params=parameters, timeout=10)
        response.raise_for_status()
        news_data = response.json()

        if news_data.get("status") == "ok":
            articles = news_data.get("articles", [])
            logger.info(f"Found {len(articles)} news articles for {company_name}")
            return articles
        else:
            logger.warning(f"News API returned non-ok status for {company_name}: {news_data.get('message')}")
            return []
    except Exception as e:
        logger.error(f"Error fetching news for {company_name}: {str(e)}", exc_info=True)
        print(f"   ❌ Error al obtener noticias: {str(e)}")
        return []


def send_alert_message(message_body):
    """
    Envía un mensaje de alerta por WhatsApp/SMS.
    Args:
        message_body: Contenido del mensaje
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        logger.warning("Twilio credentials not configured, skipping message send")
        return False

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Preparar números según el tipo de mensaje
        if USE_WHATSAPP:
            from_number = f"whatsapp:{TWILIO_PHONE_NUMBER}"
            to_number = f"whatsapp:{MY_PHONE_NUMBER}"
            msg_type = "WhatsApp"
        else:
            from_number = TWILIO_PHONE_NUMBER
            to_number = MY_PHONE_NUMBER
            msg_type = "SMS"

        logger.debug(f"Sending {msg_type} message to {to_number}")
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        logger.info(f"{msg_type} message sent successfully (SID: {message.sid})")
        return True
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}", exc_info=True)
        print(f"   ❌ Error al enviar mensaje: {str(e)}")
        return False


def generate_stock_report(stock_info, percentage_change, articles):
    """
    Genera un reporte formateado para una acción con alertas.
    Args:
        stock_info: Diccionario con información de la acción
        percentage_change: Porcentaje de cambio
        articles: Lista de artículos de noticias
    Returns:
        str: Reporte formateado
    """
    up_down = "🔺" if percentage_change > 0 else "🔻"

    report = f"\n{'='*50}\n"
    report += f"📊 {stock_info['symbol']} - {stock_info['company_name']}\n"
    report += f"{'='*50}\n"
    report += f"Cambio: {up_down} {abs(percentage_change):.2f}%\n"
    report += f"Umbral configurado: {stock_info['threshold']}%\n\n"

    if articles:
        report += f"📰 Noticias principales:\n\n"
        for i, article in enumerate(articles[:3], 1):
            report += f"{i}. {article['title']}\n"
            if article['description']:
                report += f"   {article['description'][:100]}...\n"
            report += f"   🔗 {article['url']}\n\n"
    else:
        report += "ℹ️  No se encontraron noticias recientes.\n"

    return report


# ==================== PROGRAMA PRINCIPAL ====================

def main():
    logger.info("="*70)
    logger.info("STARTING MULTI-STOCK PRICE ALERT APP")
    logger.info(f"Notification mode: {'WhatsApp' if USE_WHATSAPP else 'SMS'}")
    logger.info(f"Configuration file: {STOCKS_CSV_FILE}")
    logger.info("="*70)

    print("=" * 70)
    print("🚀 MULTI-STOCK PRICE ALERT APP")
    print("=" * 70)
    print(f"Modo de notificación: {'WhatsApp' if USE_WHATSAPP else 'SMS'}")
    print(f"Archivo de configuración: {STOCKS_CSV_FILE}")
    print("=" * 70)
    print()

    # Cargar acciones desde CSV
    stocks = load_stocks_from_csv(STOCKS_CSV_FILE)

    if not stocks:
        logger.error("Failed to load stocks. Exiting.")
        print("❌ No se pudieron cargar acciones. Finalizando.")
        return

    print(f"\n📈 Monitoreando {len(stocks)} acciones...\n")

    # Almacenar alertas para envío consolidado
    alerts = []
    summary_lines = []

    # Procesar cada acción
    for i, stock in enumerate(stocks, 1):
        print(f"[{i}/{len(stocks)}] Procesando {stock['symbol']} ({stock['company_name']})...")

        # Obtener cambio porcentual
        percentage_change, yesterday_close, day_before_close, dates = get_stock_percentage_change(stock['symbol'])

        if percentage_change is None:
            print(f"   ⚠️  No se pudo obtener información")
            summary_lines.append(f"❌ {stock['symbol']}: Error al obtener datos")
            continue

        # Mostrar información
        print(f"   Precio actual: ${yesterday_close:.2f}")
        print(f"   Cambio: {percentage_change:+.2f}%")

        # Verificar si supera el umbral
        if abs(percentage_change) >= stock['threshold']:
            print(f"   🚨 ¡ALERTA! Supera el umbral de {stock['threshold']}%")

            # Obtener noticias
            articles = get_news_articles(stock['company_name'], limit=3)
            print(f"   📰 Noticias encontradas: {len(articles)}")

            # Generar reporte
            report = generate_stock_report(stock, percentage_change, articles)
            alerts.append({
                'stock': stock,
                'percentage_change': percentage_change,
                'articles': articles,
                'report': report
            })

            # Agregar a resumen
            up_down = "🔺" if percentage_change > 0 else "🔻"
            summary_lines.append(f"{up_down} {stock['symbol']}: {percentage_change:+.2f}%")
        else:
            print(f"   ✓ Sin alerta (cambio menor a {stock['threshold']}%)")
            summary_lines.append(f"✓ {stock['symbol']}: {percentage_change:+.2f}%")

        # Delay entre peticiones para no saturar la API
        if i < len(stocks):
            time.sleep(1)  # Esperar 1 segundo entre peticiones

        print()

    # Mostrar resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE MONITOREO")
    print("=" * 70)
    for line in summary_lines:
        print(line)
    print("=" * 70)

    # Enviar alertas si existen
    if alerts:
        logger.warning(f"ALERTS TRIGGERED: {len(alerts)} stocks exceeded thresholds")
        print(f"\n🚨 Se encontraron {len(alerts)} alertas!")

        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            logger.info(f"Sending notifications via {'WhatsApp' if USE_WHATSAPP else 'SMS'}")
            print(f"📱 Enviando notificaciones por {'WhatsApp' if USE_WHATSAPP else 'SMS'}...")

            # Crear mensaje resumen
            summary_message = f"🚨 STOCK ALERTS - {len(alerts)} acciones con cambios significativos:\n\n"
            summary_message += "\n".join(summary_lines[:10])  # Limitar para no exceder límite de caracteres

            # Enviar resumen
            if send_alert_message(summary_message):
                print("   ✅ Mensaje resumen enviado")

            # Enviar detalle de cada alerta
            for i, alert in enumerate(alerts, 1):
                time.sleep(2)  # Esperar entre mensajes

                # Crear mensaje detallado
                up_down = "🔺" if alert['percentage_change'] > 0 else "🔻"
                detail_message = f"{alert['stock']['symbol']}: {up_down}{abs(alert['percentage_change']):.2f}%\n\n"

                if alert['articles']:
                    article = alert['articles'][0]  # Enviar solo la primera noticia
                    detail_message += f"Headline: {article['title']}\n"
                    detail_message += f"Brief: {article['description'] or 'No description available'}"

                if send_alert_message(detail_message):
                    print(f"   ✅ Alerta {i}/{len(alerts)} enviada ({alert['stock']['symbol']})")

            print("\n✅ Todas las notificaciones enviadas!")
        else:
            print("⚠️  Credenciales de Twilio no configuradas.")
            print("\nReportes detallados:")
            for alert in alerts:
                print(alert['report'])
    else:
        logger.info("No alerts triggered - all stocks below thresholds")
        print("\n✓ No se encontraron cambios significativos en ninguna acción.")

    logger.info("="*70)
    logger.info("MONITORING SESSION COMPLETED")
    logger.info("="*70)

    print("\n" + "=" * 70)
    print("✅ Monitoreo completado")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Program interrupted by user")
        print("\n\n⚠️  Programa interrumpido por el usuario")
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"\n\n❌ Error crítico: {str(e)}")
        raise
