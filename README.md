# 📈 Stock Price Alert Web Application

[![CI](https://github.com/Veregorn/stock-price-sms-alert-app/actions/workflows/ci.yml/badge.svg)](https://github.com/Veregorn/stock-price-sms-alert-app/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Veregorn/stock-price-sms-alert-app/branch/main/graph/badge.svg)](https://codecov.io/gh/Veregorn/stock-price-sms-alert-app)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A modern, full-stack web application for monitoring multiple stock prices with real-time alerts, interactive charts, and news integration. Built with FastAPI, SQLAlchemy, and a responsive web interface.

## ✨ Features

### 🎯 Core Functionality
- **📊 Multi-Stock Monitoring**: Track unlimited stocks with customizable alert thresholds
- **🚨 Smart Alerts**: Percentage-based alerts with historical tracking and duplicate prevention
- **📱 WhatsApp/SMS Notifications**: Receive instant alerts via Twilio with delivery status tracking
- **📰 News Integration**: Automatic news fetching from News API with Unsplash fallback images
- **📈 Real-Time Price Updates**: Fetch live stock prices from Alpha Vantage API
- **🖼️ Professional Images**: Beautiful stock images from Unsplash API with proper attribution
- **📊 Interactive Price Charts**: Visual 30-day price trends with Chart.js
- **💾 Persistent Storage**: SQLite for local development, PostgreSQL for production
- **🤖 Automated Scheduler**: Daily price updates at 18:00 UTC (after market close)
- **🔘 Manual Updates**: One-click price refresh from dashboard for demos and testing

### 🖥️ Web Interface
- **📱 Responsive Design**: Beautiful Tailwind CSS interface that works on all devices
- **🎨 Modern UI**: Clean, professional design with smooth animations
- **📊 Interactive Dashboard**: Real-time statistics, recent alerts, and monitored stocks overview
- **📈 Price History Pages**: Individual chart pages for each stock with detailed price data
- **🔍 Stock Management**: Full CRUD operations via intuitive web interface
- **📰 News Browser**: Browse and filter news articles by stock with professional images
- **🔔 Alerts Page**: View and filter all triggered alerts with comprehensive details

### 🔧 Technical Features
- **⚡ REST API**: Complete FastAPI backend with automatic OpenAPI documentation
- **🗄️ SQLAlchemy ORM**: Clean database abstraction with models and relationships
- **✅ Data Validation**: Pydantic schemas for request/response validation
- **🎯 Repository Pattern**: Clean architecture with database service layer
- **📝 Professional Logging**: Detailed logging for debugging and monitoring
- **🧪 Test Ready**: Modular structure designed for comprehensive testing
- **🏗️ Modular Architecture**: Separation of concerns with clear boundaries
- **🔄 CI/CD Ready**: GitHub Actions integration for automated testing
- **⏰ APScheduler**: Background task scheduler for automated daily price updates
- **🐘 PostgreSQL Ready**: Seamless transition from SQLite to PostgreSQL for production

## 🎬 Live Demo

Visit the application at `https://stock-price-alert-fnrm.onrender.com`.

### Available Pages

- **Dashboard** (`/dashboard`) - Overview with statistics and recent alerts
- **Stocks** (`/stocks`) - Manage your monitored stocks (add, edit, delete)
- **Price History** (`/stocks/{symbol}/prices`) - Interactive charts for each stock
- **Alerts** (`/alerts`) - View all triggered alerts with filtering options
- **News** (`/news`) - Browse latest news articles with images
- **API Docs** (`/api/docs`) - Interactive Swagger API documentation
- **ReDoc** (`/api/redoc`) - Alternative API documentation

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- SQLite (included with Python) for local development
- PostgreSQL 12+ (optional, for production deployment)
- Twilio account (free tier available) - **Required for WhatsApp/SMS notifications**
- Alpha Vantage API key (free) - **Required for real-time stock prices**
- News API key (free) - **Required for news articles**
- Unsplash Access Key (free) - **Required for fallback images**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/stock-price-sms-alert-app.git
   cd stock-price-sms-alert-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Copy the example environment file and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your API keys:
   ```env
   # Stock Price API (Alpha Vantage) - Required
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

   # News API - Required
   NEWS_API_KEY=your_news_api_key

   # Unsplash API - Required for fallback images
   UNSPLASH_ACCESS_KEY=your_unsplash_access_key

   # Twilio (WhatsApp/SMS) - Required
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=+14155238886  # Twilio WhatsApp Sandbox number
   MY_PHONE_NUMBER=+1234567890  # Your phone number with country code

   # Database Configuration
   # For local development (default):
   DATABASE_URL=sqlite:///stock_monitor.db

   # For production (PostgreSQL - Railway/Render will provide this automatically):
   # DATABASE_URL=postgresql://user:password@host:port/database

   DATABASE_ECHO=False
   ```

4. **Start the web application**
   ```bash
   python -m uvicorn src.api.main:app --reload --port 8000
   ```

   For production:
   ```bash
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```

5. **Open your browser**

   Navigate to: http://localhost:8000

   API documentation available at: http://localhost:8000/api/docs

**Note**: The application automatically starts a scheduler that updates stock prices daily at 18:00 UTC (after US market close). You can also manually trigger updates from the dashboard.

## 📋 Usage Guide

### Updating Stock Prices

The application provides two ways to update stock prices:

1. **Automatic Daily Updates** (Production):
   - Scheduler runs automatically at 18:00 UTC daily
   - Updates all active stocks after US market close
   - Creates alerts when thresholds are exceeded
   - Check scheduler status at `/scheduler/status`

2. **Manual Updates** (Demo/Testing):
   - Go to Dashboard (`/dashboard`)
   - Click "Update All Prices" button in the header
   - All active stocks are updated immediately
   - Useful for demos or when you need fresh data

### Managing Stocks via Web Interface

1. **Go to Stocks page** (`/stocks`)
2. **Add a new stock**:
   - Click "Add Stock" button
   - Fill in: Symbol (e.g., AAPL), Company Name (e.g., Apple Inc), Threshold (e.g., 5)
   - Click "Create Stock"
3. **Edit existing stock**: Click edit icon, modify fields, save
4. **Delete stock**: Click delete icon, confirm deletion
5. **View prices**: Click on stock row or chart icon to see price history

### Viewing Price History

1. Navigate to any stock's price page
2. View interactive Chart.js visualization showing:
   - 30-day closing prices
   - Daily percentage changes
   - Price trend over time
3. Data updates automatically from database

### Managing Alerts

1. Go to **Alerts** page (`/alerts`)
2. Filter alerts by date range: 7, 30, 90 days, or all time
3. View alert details:
   - Stock symbol and percentage change
   - Threshold that triggered the alert
   - Price before and after
   - Notification status and type
   - Timestamp

### Browsing News

1. Navigate to **News** page (`/news`)
2. **Filter by stock**: Use dropdown to filter news for specific stock
3. **View all news**: Select "All Stocks" to see all articles
4. Each article displays:
   - Professional image (Unsplash or placeholder)
   - Stock badge (clickable to view prices)
   - Source attribution (Bloomberg, Reuters, etc.)
   - Publication and fetch dates
   - Link to original article

### Using the REST API

Access interactive API documentation at `/api/docs` to:
- Test all endpoints directly from browser
- View request/response schemas
- Generate code snippets
- Explore available operations

## 🏗️ Project Structure

```
stock-price-sms-alert-app/
├── src/
│   ├── api/                      # FastAPI application
│   │   ├── main.py               # App initialization, CORS, routing
│   │   ├── dependencies.py       # Dependency injection (DB sessions)
│   │   ├── routers/              # API route handlers
│   │   │   ├── stocks.py         # Stock CRUD endpoints
│   │   │   ├── prices.py         # Price history endpoints
│   │   │   ├── alerts.py         # Alert management endpoints
│   │   │   ├── news.py           # News article endpoints
│   │   │   ├── dashboard.py      # Dashboard statistics endpoint
│   │   │   ├── stock_updates.py  # Stock price update endpoints
│   │   │   ├── news_updates.py   # News fetch and save endpoints
│   │   │   ├── notifications.py  # WhatsApp/SMS notification endpoints
│   │   │   └── pages.py          # HTML page routes
│   │   └── schemas.py            # Pydantic models (validation)
│   │
│   ├── database/                 # Database layer
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   │                         # (Stock, PriceHistory, Alert, NewsArticle)
│   │   └── service.py            # Database service (Repository pattern)
│   │                             # All CRUD operations
│   │
│   ├── config.py                 # Centralized configuration
│   ├── scheduler.py              # APScheduler for automated price updates
│   ├── stock_fetcher.py          # Alpha Vantage API integration
│   ├── news_fetcher.py           # News API integration
│   ├── image_fetcher.py          # Unsplash API integration
│   ├── notifier.py               # Twilio WhatsApp/SMS integration
│   └── utils.py                  # Utility functions
│
├── templates/                    # Jinja2 HTML templates
│   ├── base.html                 # Base template with navigation
│   ├── dashboard.html            # Dashboard with statistics
│   ├── stocks.html               # Stock management (CRUD)
│   ├── price_history.html        # Price charts with Chart.js
│   ├── alerts.html               # Alerts listing and filtering
│   └── news.html                 # News browsing with images
│
├── static/                       # Static assets
│   ├── css/
│   │   └── styles.css            # Custom styles
│   └── js/
│       └── main.js               # Shared JavaScript utilities
│
├── tests/                        # Comprehensive test suite
│   ├── test_main.py              # Integration tests
│   ├── test_stock_fetcher.py     # Stock fetcher tests
│   ├── test_news_fetcher.py      # News fetcher tests
│   ├── test_notifier.py          # Notifier tests
│   └── test_utils.py             # Utilities tests
│
├── logs/                         # Application logs (auto-created)
│   └── stock_monitor_YYYYMMDD.log
│
├── stocks.db                     # SQLite database (auto-created)
├── stocks.csv                    # Legacy stock configuration (Phase 1)
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Development dependencies
├── pytest.ini                    # Pytest configuration
├── .coveragerc                   # Coverage configuration
├── .env                          # Environment variables (not in git)
├── .env.example                  # Example environment file
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

### Architecture Highlights

The application follows **clean architecture principles**:

- **FastAPI Application Layer** (`src/api/`): HTTP handlers, routing, validation
- **Business Logic Layer** (`src/database/service.py`): Repository pattern, database operations
- **Data Layer** (`src/database/models.py`): SQLAlchemy ORM models
- **External Integrations** (`src/stock_fetcher.py`, `news_fetcher.py`, `notifier.py`): API clients
- **Presentation Layer** (`templates/`): Jinja2 templates with Tailwind CSS

This design ensures:
- **Maintainability**: Clear separation of concerns
- **Testability**: Each layer can be tested independently
- **Scalability**: Easy to add features or swap implementations
- **Professional Quality**: Industry-standard patterns

## 🗄️ Database Schema

### Tables

#### `stocks`
- `id` (INTEGER, PK): Unique stock identifier
- `symbol` (VARCHAR, UNIQUE): Stock ticker (e.g., AAPL, TSLA)
- `company_name` (VARCHAR): Full company name
- `threshold` (FLOAT): Alert threshold percentage (0-100)
- `is_active` (BOOLEAN): Whether monitoring is enabled
- `created_at`, `updated_at` (DATETIME): Timestamps

#### `price_history`
- `id` (INTEGER, PK): Unique price record identifier
- `stock_id` (INTEGER, FK → stocks.id): Reference to stock
- `date` (DATETIME): Price date
- `close_price` (FLOAT): Closing price
- `previous_close` (FLOAT, nullable): Previous day's close
- `percentage_change` (FLOAT, nullable): Calculated % change
- `created_at` (DATETIME): Record creation timestamp

#### `alerts`
- `id` (INTEGER, PK): Unique alert identifier
- `stock_id` (INTEGER, FK → stocks.id): Reference to stock
- `percentage_change` (FLOAT): Change that triggered alert
- `threshold_at_time` (FLOAT): Threshold when alert fired
- `price_before` (FLOAT, nullable): Previous price
- `price_after` (FLOAT, nullable): New price
- `message_sent` (BOOLEAN): Notification delivery status
- `notification_type` (VARCHAR, nullable): 'whatsapp' or 'sms'
- `error_message` (TEXT, nullable): Error if notification failed
- `triggered_at` (DATETIME): Alert timestamp

#### `news_articles`
- `id` (INTEGER, PK): Unique article identifier
- `stock_id` (INTEGER, FK → stocks.id): Reference to stock
- `title` (VARCHAR): Article title
- `description` (TEXT, nullable): Article summary
- `url` (VARCHAR, nullable): Link to original article
- `image_url` (VARCHAR, nullable): Article/fallback image URL
- `source` (VARCHAR, nullable): News source (e.g., Bloomberg)
- `published_at` (DATETIME, nullable): Publication date
- `fetched_at` (DATETIME): When article was saved
- `photographer_name` (VARCHAR, nullable): Unsplash photographer name
- `photographer_username` (VARCHAR, nullable): Unsplash username
- `photographer_url` (VARCHAR, nullable): Unsplash profile URL
- `unsplash_download_location` (VARCHAR, nullable): Download tracking URL

### Relationships

- `Stock` → `PriceHistory` (one-to-many, cascade delete)
- `Stock` → `Alert` (one-to-many, cascade delete)
- `Stock` → `NewsArticle` (one-to-many, cascade delete)

## 🔌 API Endpoints

### Stocks

- `GET /api/stocks` - List all stocks
  - Query params: `?only_active=true` (filter active stocks)
  - Response: `{ total: int, stocks: Stock[] }`
- `GET /api/stocks/{symbol}` - Get stock by symbol
  - Response: `Stock` object
- `POST /api/stocks` - Create new stock
  - Body: `{ symbol, company_name, threshold, is_active? }`
  - Response: Created `Stock` with ID and timestamps
- `PUT /api/stocks/{symbol}` - Update stock
  - Body: `{ company_name?, threshold?, is_active? }`
  - Response: Updated `Stock`
- `DELETE /api/stocks/{symbol}` - Delete stock (cascades to prices/alerts/news)
  - Response: `{ message: string }`

### Price History

- `GET /api/stocks/{symbol}/prices` - Get price history
  - Query params: `?days=30` (number of days, default 30)
  - Response: `{ symbol, total, prices: PriceHistory[] }`
- `POST /api/stocks/{symbol}/prices` - Add price record
  - Body: `{ date, close_price }`
  - Response: Created `PriceHistory` with calculated changes
- `GET /api/stocks/{symbol}/latest-price` - Get most recent price
  - Response: Latest `PriceHistory` record

### Alerts

- `GET /api/alerts` - List alerts
  - Query params: `?symbol=AAPL&days=7`
  - Response: `{ total, alerts: Alert[] }`

### News

- `GET /api/stocks/{symbol}/news` - Get news articles for stock
  - Query params: `?limit=10` (max articles, default 10)
  - Response: `{ symbol, total, news: NewsArticle[] }`
- `POST /api/stocks/{symbol}/news` - Save news article
  - Body: `{ title, description?, url?, image_url?, source?, published_at? }`
  - Response: Created `NewsArticle`

### Dashboard

- `GET /api/dashboard/summary` - Get dashboard statistics
  - Response: `{ total_stocks, active_stocks, recent_alerts_24h, last_price_update }`

### Documentation

- `GET /api/docs` - Interactive Swagger UI
- `GET /api/redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI 3.0 schema

## 🛠️ Built With

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** (0.104.1) - Modern web framework with automatic OpenAPI docs
- **[SQLAlchemy](https://www.sqlalchemy.org/)** (2.0.23) - SQL toolkit and ORM
- **[Pydantic](https://docs.pydantic.dev/)** (2.5.0) - Data validation using type annotations
- **[Uvicorn](https://www.uvicorn.org/)** (0.24.0) - Lightning-fast ASGI server
- **[APScheduler](https://apscheduler.readthedocs.io/)** (3.10.4) - Background task scheduler
- **[psycopg2-binary](https://pypi.org/project/psycopg2-binary/)** (2.9.9) - PostgreSQL database adapter
- **[Python-dotenv](https://pypi.org/project/python-dotenv/)** (0.21.0) - Environment variable management

### Frontend
- **[Jinja2](https://jinja.palletsprojects.com/)** (3.1.2) - Template engine
- **[Tailwind CSS](https://tailwindcss.com/)** (3.x via CDN) - Utility-first CSS framework
- **[Chart.js](https://www.chartjs.org/)** (4.x via CDN) - Interactive charts
- **[Font Awesome](https://fontawesome.com/)** (6.x via CDN) - Icon library

### External APIs
- **[Alpha Vantage API](https://www.alphavantage.co/)** - Real-time stock prices
- **[News API](https://newsapi.org/)** - Financial news aggregation
- **[Unsplash API](https://unsplash.com/developers)** - High-quality stock images
- **[Twilio](https://www.twilio.com/)** - SMS and WhatsApp messaging

### Development Tools
- **pytest** - Testing framework
- **httpx** - Async HTTP client for testing
- **black** - Code formatter
- **flake8** - Linter

## 🔑 API Setup Guide

### 1. Alpha Vantage (Stock Prices)
- Visit: https://www.alphavantage.co/support/#api-key
- Free tier: 25 requests/day, 5 requests/minute
- Copy your API key to `.env` → `ALPHA_VANTAGE_API_KEY`

### 2. News API (News Articles)
- Visit: https://newsapi.org/register
- Free tier: 100 requests/day
- Copy your API key to `.env` → `NEWS_API_KEY`

### 3. Unsplash (Stock Images)
- Visit: https://unsplash.com/developers
- Create an app to get your Access Key
- Free tier: 50 requests/hour
- Copy your Access Key to `.env` → `UNSPLASH_ACCESS_KEY`
- **Important**: The app triggers download events as required by Unsplash API Guidelines

### 4. Twilio (WhatsApp/SMS)
- Visit: https://www.twilio.com/try-twilio
- Free trial includes credit for testing
- **For WhatsApp**: Join the Twilio Sandbox
  1. Go to https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
  2. Send the activation message from your WhatsApp to the Twilio number (e.g., `join finish-swimming`)
  3. Wait for confirmation message from Twilio
  4. **Important**: You need to re-join the sandbox if it expires after inactivity
- Copy credentials to `.env`:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_PHONE_NUMBER` (Use sandbox number: +14155238886)
  - `MY_PHONE_NUMBER` (Your phone with country code, e.g., +1234567890)

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | Yes | - |
| `NEWS_API_KEY` | News API key | Yes | - |
| `UNSPLASH_ACCESS_KEY` | Unsplash Access Key | Yes | - |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | Yes | - |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | Yes | - |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | Yes | - |
| `MY_PHONE_NUMBER` | Your phone number | Yes | - |
| `DATABASE_URL` | Database connection string | No | `sqlite:///stock_monitor.db` |
| `DATABASE_ECHO` | Log SQL queries (True/False) | No | `False` |

**Database Configuration**:
- **Local Development**: Use default SQLite (`sqlite:///stock_monitor.db`)
- **Production (Railway/Render)**: Set to PostgreSQL connection string
  - Format: `postgresql://user:password@host:port/database`
  - Most platforms auto-inject this variable

### Application Settings (`src/config.py`)

```python
# Notification preferences
USE_WHATSAPP = True  # Set to False for SMS instead

# Database
DATABASE_URL = "sqlite:///./stocks.db"
DATABASE_ECHO = False  # True to see SQL queries

# API settings
API_TIMEOUT = 10  # Seconds
REQUEST_DELAY = 1  # Seconds between API calls

# Logging
LOG_DIR = "logs"
LOG_LEVEL = "INFO"
```

## 🧪 Testing

The project includes a comprehensive test suite with **98% code coverage**.

### Test Structure

```
tests/
├── test_main.py           # 7 integration tests
├── test_stock_fetcher.py  # 8 unit tests
├── test_news_fetcher.py   # 10 unit tests
├── test_notifier.py       # 10 unit tests
└── test_utils.py          # 8 unit tests
```

**Total: 43 tests** covering all core functionality.

### Running Tests

**Install development dependencies:**
```bash
pip install -r requirements-dev.txt
```

**Run all tests:**
```bash
pytest
```

**Run with verbose output:**
```bash
pytest -v
```

**Run with coverage report:**
```bash
pytest --cov=src --cov=main --cov-report=html
```

**View coverage report:**
```bash
open htmlcov/index.html  # macOS
```

### Continuous Integration

All tests run automatically via GitHub Actions on every push and pull request:
- **Code Linting**: flake8
- **Unit Tests**: Full pytest suite
- **Coverage Reporting**: Automatic upload to Codecov
- **Multi-Python Support**: Tests on Python 3.7+

Check the CI status badge at the top!

## 📈 Development Roadmap

### ✅ Completed Phases

- [x] **Phase 1**: Core Backend
  - [x] Database models (SQLAlchemy)
  - [x] Database service layer (Repository pattern)
  - [x] Configuration management
  - [x] Logging infrastructure

- [x] **Phase 2**: REST API
  - [x] FastAPI application setup
  - [x] Stock CRUD endpoints
  - [x] Price history endpoints
  - [x] Alert management endpoints
  - [x] News endpoints
  - [x] Dashboard statistics endpoint
  - [x] Pydantic schemas for validation
  - [x] Automatic OpenAPI documentation

- [x] **Phase 3**: Web Frontend
  - [x] Responsive Tailwind CSS layout
  - [x] Dashboard with statistics and charts
  - [x] Stock management interface (CRUD)
  - [x] Interactive price history charts (Chart.js)
  - [x] Alerts browsing and filtering
  - [x] News browsing with images and filtering
  - [x] Client-side JavaScript utilities
  - [x] Error handling and user feedback

- [x] **Phase 4**: External Integrations ✅
  - [x] Stock Price API integration (Alpha Vantage)
    - [x] Fetch real-time prices with percentage changes
    - [x] Update price history automatically
    - [x] Automatic alert creation when thresholds exceeded
    - [x] Duplicate alert prevention
    - [x] Batch update all stocks endpoint
  - [x] News API integration
    - [x] Fetch real news articles by company name
    - [x] Store with images and metadata
    - [x] Duplicate detection by URL
    - [x] Individual and batch fetch endpoints
  - [x] Unsplash API integration
    - [x] Fallback images when News API has no image
    - [x] Photographer attribution (required by Unsplash)
    - [x] Download event tracking
  - [x] WhatsApp/SMS Notifications (Twilio)
    - [x] Send alerts when thresholds exceeded
    - [x] Delivery status tracking in database
    - [x] Individual and batch notification endpoints
    - [x] Error handling and logging

- [x] **Phase 5**: Deployment & Automation ✅
  - [x] Manual price update button in dashboard
    - [x] "Update All Prices" button with loading states
    - [x] Toast notifications for success/error feedback
    - [x] Instant updates for demos and testing
  - [x] Automated scheduler implementation
    - [x] APScheduler with daily cron trigger
    - [x] Executes at 18:00 UTC (after US market close)
    - [x] Background task processing
    - [x] Scheduler status endpoint (`/scheduler/status`)
  - [x] PostgreSQL production support
    - [x] Conditional database engine configuration
    - [x] SQLite for local development
    - [x] PostgreSQL driver (`psycopg2-binary`)
    - [x] Seamless dev-to-prod transition via DATABASE_URL

### 🔮 Future Enhancements

- [x] Cloud deployment (Railway, Render, Heroku)
- [ ] User authentication and authorization
- [ ] Multi-user support with portfolios
- [ ] Real-time price updates (WebSockets)
- [ ] Email notifications
- [ ] Cryptocurrency support
- [ ] Advanced charting (candlestick, volume, technical indicators)
- [ ] Price prediction with machine learning
- [ ] Mobile app (React Native or Flutter)
- [ ] Export data (CSV, Excel, PDF reports)
- [ ] Docker containerization
- [ ] GraphQL API alternative

## ⚠️ Disclaimer

This tool is for educational and informational purposes only. It is not financial advice. Always conduct your own research and consult with qualified financial professionals before making investment decisions. Past performance does not guarantee future results.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Raúl Jiménez Barco**
- GitHub: [@Veregorn](https://github.com/Veregorn)
- LinkedIn: [rjbarco](https://linkedin.com/in/rjbarco)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the incredible web framework
- [Tailwind CSS](https://tailwindcss.com/) for beautiful, responsive styling
- [Chart.js](https://www.chartjs.org/) for interactive data visualization
- [Alpha Vantage](https://www.alphavantage.co/) for providing free stock market data
- [News API](https://newsapi.org/) for financial news aggregation
- [Unsplash](https://unsplash.com/) for beautiful, free stock images
- [Twilio](https://www.twilio.com/) for WhatsApp and SMS messaging infrastructure
- The Python community for amazing open-source tools

---

⭐ **Star this repo if you found it helpful!**

📧 Questions or suggestions? Open an issue or reach out on LinkedIn!
