"""
Multi-Stock Price Alert App - Main Entry Point

A professional Python application that monitors multiple stock prices
and sends real-time alerts via WhatsApp or SMS when significant price
changes occur.

Author: Raúl Jiménez Barco
"""

import time
import logging

from src.config import config
from src.utils import setup_logging, load_stocks_from_csv, generate_stock_report
from src.stock_fetcher import StockFetcher
from src.news_fetcher import NewsFetcher
from src.notifier import Notifier

# Initialize logging
logger = setup_logging()


def main():
    """Main application logic."""
    logger.info("=" * 70)
    logger.info("STARTING MULTI-STOCK PRICE ALERT APP")
    logger.info(f"Notification mode: {'WhatsApp' if config.USE_WHATSAPP else 'SMS'}")
    logger.info(f"Configuration file: {config.STOCKS_CSV_FILE}")
    logger.info("=" * 70)

    print("=" * 70)
    print("🚀 MULTI-STOCK PRICE ALERT APP")
    print("=" * 70)
    print(f"Modo de notificación: {'WhatsApp' if config.USE_WHATSAPP else 'SMS'}")
    print(f"Archivo de configuración: {config.STOCKS_CSV_FILE}")
    print("=" * 70)
    print()

    # Load stocks from CSV
    stocks = load_stocks_from_csv(config.STOCKS_CSV_FILE)

    if not stocks:
        logger.error("Failed to load stocks. Exiting.")
        print("❌ No se pudieron cargar acciones. Finalizando.")
        return

    print(f"\n📈 Monitoreando {len(stocks)} acciones...\n")

    # Initialize services
    stock_fetcher = StockFetcher()
    news_fetcher = NewsFetcher()
    notifier = Notifier(use_whatsapp=config.USE_WHATSAPP)

    # Store alerts for consolidated sending
    alerts = []
    summary_lines = []

    # Process each stock
    for i, stock in enumerate(stocks, 1):
        print(f"[{i}/{len(stocks)}] Procesando {stock['symbol']} ({stock['company_name']})...")

        # Get percentage change
        percentage_change, yesterday_close, day_before_close, dates = \
            stock_fetcher.get_percentage_change(stock['symbol'])

        if percentage_change is None:
            print("   ⚠️  No se pudo obtener información")
            summary_lines.append(f"❌ {stock['symbol']}: Error al obtener datos")
            continue

        # Display information
        print(f"   Precio actual: ${yesterday_close:.2f}")
        print(f"   Cambio: {percentage_change:+.2f}%")

        # Check if exceeds threshold
        if abs(percentage_change) >= stock['threshold']:
            print(f"   🚨 ¡ALERTA! Supera el umbral de {stock['threshold']}%")

            # Get news articles
            articles = news_fetcher.get_articles(stock['company_name'], limit=3)
            print(f"   📰 Noticias encontradas: {len(articles)}")

            # Generate report
            report = generate_stock_report(stock, percentage_change, articles)
            alerts.append({
                'stock': stock,
                'percentage_change': percentage_change,
                'articles': articles,
                'report': report
            })

            # Add to summary
            up_down = "🔺" if percentage_change > 0 else "🔻"
            summary_lines.append(f"{up_down} {stock['symbol']}: {percentage_change:+.2f}%")
        else:
            print(f"   ✓ Sin alerta (cambio menor a {stock['threshold']}%)")
            summary_lines.append(f"✓ {stock['symbol']}: {percentage_change:+.2f}%")

        # Delay between requests to avoid saturating the API
        if i < len(stocks):
            time.sleep(config.REQUEST_DELAY)

        print()

    # Display summary
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE MONITOREO")
    print("=" * 70)
    for line in summary_lines:
        print(line)
    print("=" * 70)

    # Send alerts if any exist
    if alerts:
        logger.warning(f"ALERTS TRIGGERED: {len(alerts)} stocks exceeded thresholds")
        print(f"\n🚨 Se encontraron {len(alerts)} alertas!")

        if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN:
            logger.info(f"Sending notifications via {'WhatsApp' if config.USE_WHATSAPP else 'SMS'}")
            print(f"📱 Enviando notificaciones por {'WhatsApp' if config.USE_WHATSAPP else 'SMS'}...")

            # Create summary message
            summary_message = f"🚨 STOCK ALERTS - {len(alerts)} acciones con cambios significativos:\n\n"
            summary_message += "\n".join(summary_lines[:10])  # Limit to avoid character limit

            # Send summary
            if notifier.send_message(summary_message):
                print("   ✅ Mensaje resumen enviado")

            # Send detail for each alert
            for i, alert in enumerate(alerts, 1):
                time.sleep(2)  # Wait between messages

                # Create detailed message
                up_down = "🔺" if alert['percentage_change'] > 0 else "🔻"
                detail_message = f"{alert['stock']['symbol']}: {up_down}{abs(alert['percentage_change']):.2f}%\n\n"

                if alert['articles']:
                    article = alert['articles'][0]  # Send only the first news
                    detail_message += f"Headline: {article['title']}\n"
                    detail_message += f"Brief: {article['description'] or 'No description available'}"

                if notifier.send_message(detail_message):
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

    logger.info("=" * 70)
    logger.info("MONITORING SESSION COMPLETED")
    logger.info("=" * 70)

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
