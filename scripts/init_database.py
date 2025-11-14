#!/usr/bin/env python3
"""
Script de inicialización de base de datos.

Este script permite:
1. Crear las tablas de la base de datos
2. Cargar stocks desde CSV existente
3. Poblar con datos de demostración
4. Resetear la base de datos completamente

Uso:
    python scripts/init_database.py --help
    python scripts/init_database.py --create-tables
    python scripts/init_database.py --load-csv stocks.csv
    python scripts/init_database.py --demo
    python scripts/init_database.py --reset --demo
"""

import argparse
import sys
import csv
from pathlib import Path

# Añadir el directorio raíz al path para poder importar src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseService
from src.config import config


def create_tables(db_service: DatabaseService) -> None:
    """
    Crea todas las tablas en la base de datos.

    Args:
        db_service: Instancia del servicio de base de datos
    """
    print("📊 Creando tablas en la base de datos...")
    db_service.create_tables()
    print("   ✅ Tablas creadas correctamente\n")


def drop_tables(db_service: DatabaseService) -> None:
    """
    Elimina todas las tablas de la base de datos.

    ⚠️  CUIDADO: Esta operación elimina todos los datos.

    Args:
        db_service: Instancia del servicio de base de datos
    """
    print("⚠️  ELIMINANDO TODAS LAS TABLAS...")
    confirm = input("   ¿Estás seguro? Escribe 'SI' para confirmar: ")

    if confirm.upper() == 'SI':
        db_service.drop_tables()
        print("   ✅ Tablas eliminadas\n")
    else:
        print("   ❌ Operación cancelada\n")


def load_from_csv(db_service: DatabaseService, csv_path: str) -> None:
    """
    Carga stocks desde un archivo CSV.

    El CSV debe tener las columnas: symbol, company_name, threshold

    Args:
        db_service: Instancia del servicio de base de datos
        csv_path: Ruta al archivo CSV
    """
    print(f"📥 Cargando stocks desde {csv_path}...")

    csv_file = Path(csv_path)
    if not csv_file.exists():
        print(f"   ❌ Error: El archivo {csv_path} no existe\n")
        return

    stocks_loaded = 0
    stocks_skipped = 0

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            symbol = row.get('symbol', '').strip().upper()
            company_name = row.get('company_name', '').strip()
            threshold = float(row.get('threshold', 5.0))

            # Verificar si ya existe
            existing = db_service.get_stock_by_symbol(symbol)
            if existing:
                print(f"   ⚠️  {symbol} ya existe, saltando...")
                stocks_skipped += 1
                continue

            # Crear el stock
            stock = db_service.create_stock(symbol, company_name, threshold)
            print(f"   ✅ {stock.symbol}: {stock.company_name} (umbral: {stock.threshold}%)")
            stocks_loaded += 1

    print(f"\n📊 Resumen:")
    print(f"   - Stocks cargados: {stocks_loaded}")
    print(f"   - Stocks saltados (ya existían): {stocks_skipped}\n")


def populate_demo_data(db_service: DatabaseService) -> None:
    """
    Puebla la base de datos con datos de demostración.

    Crea algunos stocks de ejemplo con diferentes umbrales.

    Args:
        db_service: Instancia del servicio de base de datos
    """
    print("🎬 Poblando base de datos con datos de demostración...\n")

    demo_stocks = [
        ('TSLA', 'Tesla Inc', 5.0),
        ('AAPL', 'Apple Inc', 3.0),
        ('GOOGL', 'Alphabet Inc', 4.0),
        ('MSFT', 'Microsoft Corporation', 3.5),
        ('AMZN', 'Amazon.com Inc', 4.5),
        ('META', 'Meta Platforms Inc', 5.0),
        ('NVDA', 'NVIDIA Corporation', 6.0),
        ('NFLX', 'Netflix Inc', 4.0),
    ]

    stocks_created = 0
    stocks_skipped = 0

    for symbol, company, threshold in demo_stocks:
        # Verificar si ya existe
        existing = db_service.get_stock_by_symbol(symbol)
        if existing:
            print(f"   ⚠️  {symbol} ya existe, saltando...")
            stocks_skipped += 1
            continue

        # Crear el stock
        stock = db_service.create_stock(symbol, company, threshold)
        print(f"   ✅ {stock.symbol}: {stock.company_name} (umbral: {stock.threshold}%)")
        stocks_created += 1

    print(f"\n📊 Resumen:")
    print(f"   - Stocks creados: {stocks_created}")
    print(f"   - Stocks saltados: {stocks_skipped}\n")


def show_database_info(db_service: DatabaseService) -> None:
    """
    Muestra información sobre la base de datos actual.

    Args:
        db_service: Instancia del servicio de base de datos
    """
    print("📊 INFORMACIÓN DE LA BASE DE DATOS")
    print("=" * 70)
    print(f"URL: {db_service.database_url}\n")

    # Obtener estadísticas
    summary = db_service.get_dashboard_summary()

    print(f"Stocks totales:    {summary['total_stocks']}")
    print(f"Stocks activos:    {summary['active_stocks']}")
    print(f"Alertas (24h):     {summary['recent_alerts_24h']}")

    if summary['last_price_update']:
        print(f"Última actualización: {summary['last_price_update']}")
    else:
        print("Última actualización: Nunca")

    # Listar stocks
    stocks = db_service.get_all_stocks()
    if stocks:
        print(f"\n📈 STOCKS CONFIGURADOS:")
        print("-" * 70)
        for stock in stocks:
            status = "🟢" if stock.is_active else "🔴"
            print(f"{status} {stock.symbol:8} | {stock.company_name:30} | {stock.threshold:5.1f}%")
    else:
        print("\n⚠️  No hay stocks configurados en la base de datos")

    print("=" * 70 + "\n")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Script de inicialización de base de datos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Crear tablas
  python scripts/init_database.py --create-tables

  # Cargar desde CSV
  python scripts/init_database.py --load-csv stocks.csv

  # Poblar con datos de demo
  python scripts/init_database.py --demo

  # Resetear y poblar con demo
  python scripts/init_database.py --reset --demo

  # Ver información de la BD
  python scripts/init_database.py --info
        """
    )

    parser.add_argument(
        '--create-tables',
        action='store_true',
        help='Crear las tablas en la base de datos'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='⚠️  Eliminar todas las tablas antes de continuar (DESTRUCTIVO)'
    )

    parser.add_argument(
        '--load-csv',
        type=str,
        metavar='FILE',
        help='Cargar stocks desde un archivo CSV'
    )

    parser.add_argument(
        '--demo',
        action='store_true',
        help='Poblar con datos de demostración'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='Mostrar información de la base de datos'
    )

    parser.add_argument(
        '--database-url',
        type=str,
        help='URL de la base de datos (por defecto usa config.DATABASE_URL)'
    )

    args = parser.parse_args()

    # Si no se proporciona ningún argumento, mostrar ayuda
    if not any(vars(args).values()):
        parser.print_help()
        return

    # Banner
    print("\n" + "=" * 70)
    print("🗄️  STOCK PRICE ALERT - DATABASE INITIALIZATION")
    print("=" * 70 + "\n")

    # Crear servicio de base de datos
    database_url = args.database_url or config.DATABASE_URL
    db_service = DatabaseService(database_url=database_url)

    try:
        # 1. Reset (si se solicita)
        if args.reset:
            drop_tables(db_service)
            # Después de reset, siempre crear tablas
            create_tables(db_service)

        # 2. Crear tablas (si se solicita y no hubo reset)
        if args.create_tables and not args.reset:
            create_tables(db_service)

        # 3. Cargar desde CSV
        if args.load_csv:
            load_from_csv(db_service, args.load_csv)

        # 4. Datos de demostración
        if args.demo:
            populate_demo_data(db_service)

        # 5. Mostrar información
        if args.info or args.create_tables or args.load_csv or args.demo or args.reset:
            show_database_info(db_service)

        print("✅ Operación completada exitosamente\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db_service.close()


if __name__ == '__main__':
    main()
