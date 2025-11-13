import os
import csv
import time
import requests
from dotenv import load_dotenv
from twilio.rest import Client

# Cargar variables de entorno desde el archivo .env
load_dotenv()

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
        print(f"✅ Cargadas {len(stocks)} acciones desde {csv_file}")
        return stocks
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {csv_file}")
        return []
    except Exception as e:
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
    parameters = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(ALPHA_VANTAGE_ENDPOINT, params=parameters, timeout=10)
        stock_data = response.json()

        if "Time Series (Daily)" not in stock_data:
            return None, None, None, None

        # Obtener los dos últimos días de datos
        daily_data = stock_data["Time Series (Daily)"]
        recent_dates = list(daily_data.keys())[:2]

        yesterday_close = float(daily_data[recent_dates[0]]["4. close"])
        day_before_yesterday_close = float(daily_data[recent_dates[1]]["4. close"])

        # Calcular el cambio porcentual
        difference = yesterday_close - day_before_yesterday_close
        percentage_change = (difference / day_before_yesterday_close) * 100

        return percentage_change, yesterday_close, day_before_yesterday_close, recent_dates

    except Exception as e:
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
    parameters = {
        "q": company_name,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": limit
    }

    try:
        response = requests.get(NEWS_API_ENDPOINT, params=parameters, timeout=10)
        news_data = response.json()

        if news_data.get("status") == "ok":
            return news_data.get("articles", [])
        else:
            return []
    except Exception as e:
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
        return False

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Preparar números según el tipo de mensaje
        if USE_WHATSAPP:
            from_number = f"whatsapp:{TWILIO_PHONE_NUMBER}"
            to_number = f"whatsapp:{MY_PHONE_NUMBER}"
        else:
            from_number = TWILIO_PHONE_NUMBER
            to_number = MY_PHONE_NUMBER

        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        return True
    except Exception as e:
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
        print(f"\n🚨 Se encontraron {len(alerts)} alertas!")

        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
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
        print("\n✓ No se encontraron cambios significativos en ninguna acción.")

    print("\n" + "=" * 70)
    print("✅ Monitoreo completado")
    print("=" * 70)


if __name__ == "__main__":
    main()
