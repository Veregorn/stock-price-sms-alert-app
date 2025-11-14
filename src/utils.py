"""
Utility functions module.

Contains helper functions for CSV loading, report generation, and logging setup.
"""

import os
import csv
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import List, Dict, Any

from .config import config

logger = logging.getLogger(__name__)


def setup_logging() -> logging.Logger:
    """
    Configure logging system with file rotation and console output.

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(config.LOG_DIR):
        os.makedirs(config.LOG_DIR)

    # Log file name with timestamp
    log_file = os.path.join(
        config.LOG_DIR,
        f"stock_monitor_{datetime.now().strftime('%Y%m%d')}.log"
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    root_logger.handlers = []

    # File formatter (detailed)
    file_formatter = logging.Formatter(
        config.LOG_FORMAT_FILE,
        datefmt=config.LOG_DATE_FORMAT
    )

    # Console formatter (compact)
    console_formatter = logging.Formatter(config.LOG_FORMAT_CONSOLE)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


def load_stocks_from_csv(csv_file: str) -> List[Dict[str, Any]]:
    """
    Load list of stocks to monitor from a CSV file.

    Args:
        csv_file: Path to CSV file

    Returns:
        List of stock dictionaries with keys: symbol, company_name, threshold
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

        logger.info(
            f"Successfully loaded {len(stocks)} stocks: "
            f"{[s['symbol'] for s in stocks]}"
        )
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


def generate_stock_report(
    stock_info: Dict[str, Any],
    percentage_change: float,
    articles: List[Dict[str, str]]
) -> str:
    """
    Generate a formatted report for a stock with alerts.

    Args:
        stock_info: Stock information dictionary
        percentage_change: Percentage change value
        articles: List of news articles

    Returns:
        Formatted report string
    """
    up_down = "🔺" if percentage_change > 0 else "🔻"

    report = f"\n{'='*50}\n"
    report += f"📊 {stock_info['symbol']} - {stock_info['company_name']}\n"
    report += f"{'='*50}\n"
    report += f"Cambio: {up_down} {abs(percentage_change):.2f}%\n"
    report += f"Umbral configurado: {stock_info['threshold']}%\n\n"

    if articles:
        report += "📰 Noticias principales:\n\n"
        for i, article in enumerate(articles[:3], 1):
            report += f"{i}. {article['title']}\n"
            if article['description']:
                report += f"   {article['description'][:100]}...\n"
            report += f"   🔗 {article['url']}\n\n"
    else:
        report += "ℹ️  No se encontraron noticias recientes.\n"

    return report
