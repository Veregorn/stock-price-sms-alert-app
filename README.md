# 📈 Multi-Stock Price Alert App

[![CI](https://github.com/Veregorn/stock-price-sms-alert-app/actions/workflows/ci.yml/badge.svg)](https://github.com/Veregorn/stock-price-sms-alert-app/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Veregorn/stock-price-sms-alert-app/branch/main/graph/badge.svg)](https://codecov.io/gh/Veregorn/stock-price-sms-alert-app)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A professional Python application that monitors multiple stock prices and sends real-time alerts via WhatsApp or SMS when significant price changes occur. Perfect for staying informed about your investment portfolio without constantly checking the market.

## ✨ Features

- 📊 **Multi-Stock Monitoring**: Track multiple stocks simultaneously from a CSV configuration file
- 🚨 **Smart Alerts**: Customizable threshold per stock (e.g., 3% for stable stocks, 5% for volatile ones)
- 📱 **WhatsApp/SMS Notifications**: Receive instant alerts via Twilio
- 📰 **News Integration**: Get the latest news articles about stocks with significant price changes
- 🎯 **Consolidated Reports**: Receive a summary message plus detailed alerts for each stock
- ⚡ **Rate Limiting**: Built-in delays to respect API rate limits
- 🛡️ **Error Handling**: Robust error handling - one failed stock doesn't stop the entire monitoring
- 📝 **Professional Logging**: Rotating log files with detailed debugging information and console output
- 🏗️ **Modular Architecture**: Clean, maintainable codebase with separation of concerns
- 🧪 **Comprehensive Tests**: 98% code coverage with 43 unit and integration tests
- 🔄 **CI/CD Pipeline**: Automated testing, linting, and coverage reporting via GitHub Actions

## 🎬 Demo

```
======================================================================
🚀 MULTI-STOCK PRICE ALERT APP
======================================================================

[1/6] Processing TSLA (Tesla Inc)...
   Current Price: $439.62
   Change: -1.26%
   ✓ No alert (below 5% threshold)

[2/6] Processing AAPL (Apple Inc)...
   Current Price: $225.77
   Change: +3.45%
   🚨 ALERT! Exceeds 3% threshold
   �� News found: 3

======================================================================
📊 MONITORING SUMMARY
======================================================================
✓ TSLA: -1.26%
🔺 AAPL: +3.45%
✓ GOOGL: +0.89%
...
======================================================================

📱 Sending notifications via WhatsApp...
   ✅ Summary message sent
   ✅ Alert 1/1 sent (AAPL)

✅ Monitoring completed
```

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Twilio account (free tier available)
- Alpha Vantage API key (free)
- News API key (free)

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
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
   NEWS_API_KEY=your_news_api_key
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=+1234567890
   MY_PHONE_NUMBER=+1234567890
   ```

4. **Configure stocks to monitor**

   Edit `stocks.csv` to add or remove stocks:
   ```csv
   symbol,company_name,threshold
   TSLA,Tesla Inc,5
   AAPL,Apple Inc,3
   GOOGL,Alphabet Inc,4
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

## 📋 Configuration

### Stock Configuration (`stocks.csv`)

| Column | Description | Example |
|--------|-------------|---------|
| `symbol` | Stock ticker symbol | `TSLA` |
| `company_name` | Full company name (for news search) | `Tesla Inc` |
| `threshold` | Alert threshold percentage | `5` (means ≥5% change) |

### Application Settings (`src/config.py`)

```python
# Notification preferences
USE_WHATSAPP = True  # Set to False for SMS instead of WhatsApp

# File paths
STOCKS_CSV_FILE = "stocks.csv"  # Path to your stocks configuration

# API timeouts and delays
API_TIMEOUT = 10  # Seconds
REQUEST_DELAY = 1  # Seconds between API calls
```

## 🔑 API Setup Guide

### 1. Alpha Vantage (Stock Prices)
- Visit: https://www.alphavantage.co/support/#api-key
- Free tier: 25 requests/day, 5 requests/minute
- Copy your API key to `.env`

### 2. News API (News Articles)
- Visit: https://newsapi.org/register
- Free tier: 100 requests/day
- Copy your API key to `.env`

### 3. Twilio (WhatsApp/SMS)
- Visit: https://www.twilio.com/try-twilio
- Free trial includes credit for testing
- **For WhatsApp**: Join the Twilio Sandbox
  1. Go to https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
  2. Send the activation message from your WhatsApp to the Twilio number
- Copy your Account SID, Auth Token, and phone number to `.env`

## 📊 How It Works

1. **Load Configuration**: Reads stocks and thresholds from `stocks.csv`
2. **Fetch Stock Data**: Queries Alpha Vantage API for daily prices
3. **Calculate Changes**: Compares yesterday's close with the previous day
4. **Check Thresholds**: Identifies stocks exceeding their alert thresholds
5. **Gather News**: Fetches latest news articles for alerted stocks
6. **Send Notifications**:
   - One summary message with all alerts
   - Individual detailed messages with news for each stock
7. **Display Report**: Shows complete monitoring summary in console

## 🏗️ Project Structure

```
stock-price-sms-alert-app/
├── main.py                    # Main application entry point
├── src/                       # Source code package
│   ├── __init__.py            # Package initialization
│   ├── config.py              # Centralized configuration management
│   ├── stock_fetcher.py       # Stock data fetching from Alpha Vantage
│   ├── news_fetcher.py        # News retrieval from News API
│   ├── notifier.py            # WhatsApp/SMS notifications via Twilio
│   └── utils.py               # Utility functions (CSV, logging, reports)
├── tests/                     # Comprehensive test suite (98% coverage)
│   ├── __init__.py
│   ├── test_main.py           # Integration tests
│   ├── test_stock_fetcher.py  # Stock fetcher unit tests
│   ├── test_news_fetcher.py   # News fetcher unit tests
│   ├── test_notifier.py       # Notifier unit tests
│   └── test_utils.py          # Utils unit tests
├── logs/                      # Log files directory (auto-created)
│   └── stock_monitor_YYYYMMDD.log
├── stocks.csv                 # Stock configuration
├── .env                       # Environment variables (not in git)
├── .env.example               # Example environment file
├── .gitignore                 # Git ignore rules
├── pytest.ini                 # Pytest configuration
├── .coveragerc                # Coverage configuration
├── .github/                   # GitHub Actions workflows
│   └── workflows/
│       └── ci.yml             # CI/CD pipeline
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development dependencies
├── LICENSE                    # MIT License
└── README.md                  # This file
```

### Architecture Highlights

The application follows **clean architecture principles** with clear separation of concerns:

- **`main.py`**: Orchestrates the application flow, coordinates between modules
- **`src/config.py`**: Single source of truth for all configuration (API keys, settings)
- **`src/stock_fetcher.py`**: Encapsulates all stock price API interactions
- **`src/news_fetcher.py`**: Handles news article retrieval
- **`src/notifier.py`**: Manages messaging through Twilio with lazy client initialization
- **`src/utils.py`**: Provides reusable utilities (CSV parsing, logging, report formatting)

This modular design makes the codebase:
- **Maintainable**: Each module has a single, well-defined responsibility
- **Testable**: Modules can be tested independently (43 unit tests, 98% coverage)
- **Extensible**: Easy to add new features or swap implementations
- **Professional**: Industry-standard structure suitable for portfolios and production use

## 🛠️ Built With

- **Python 3** - Core programming language
- **Requests** - HTTP library for API calls
- **Twilio** - SMS and WhatsApp messaging
- **Alpha Vantage API** - Real-time stock data
- **News API** - Latest financial news
- **python-dotenv** - Environment variable management

## ⚙️ Advanced Usage

### Running on a Schedule

Use cron (Linux/Mac) or Task Scheduler (Windows) to run automatically:

**Cron example (runs every weekday at 5 PM):**
```bash
0 17 * * 1-5 cd /path/to/project && python main.py
```

### Monitoring More Stocks

Simply add more rows to `stocks.csv`:
```csv
symbol,company_name,threshold
NFLX,Netflix Inc,4
META,Meta Platforms Inc,5
AMD,Advanced Micro Devices Inc,6
```

### Adjusting Notification Preferences

In `src/config.py`, you can customize:
- `USE_WHATSAPP`: Toggle between WhatsApp and SMS
- `API_TIMEOUT`: Request timeout in seconds
- `REQUEST_DELAY`: Delay between API calls (default: 1 second)
- `LOG_DIR`: Location for log files
- Number of news articles per stock (in `src/news_fetcher.py`, default: 3)

### Viewing Logs

The application maintains detailed logs for debugging and monitoring:

**Log Files Location**: `logs/stock_monitor_YYYYMMDD.log`

**Log Features**:
- Automatic daily rotation
- Maximum 10MB per file
- Keeps last 5 backup files
- Detailed timestamps and function names
- Full error stack traces

**View today's logs**:
```bash
cat logs/stock_monitor_$(date +%Y%m%d).log
```

**Tail logs in real-time**:
```bash
tail -f logs/stock_monitor_$(date +%Y%m%d).log
```

**Log Levels**:
- `DEBUG`: API requests and technical details
- `INFO`: Normal operations (stocks loaded, prices fetched)
- `WARNING`: Alerts triggered, missing credentials
- `ERROR`: API failures, timeouts
- `CRITICAL`: Fatal errors

## 🧪 Testing

The project includes a comprehensive test suite with **98% code coverage** to ensure reliability and maintainability.

### Test Structure

```
tests/
├── test_main.py           # 7 integration tests - main application flow
├── test_stock_fetcher.py  # 8 unit tests - stock data fetching
├── test_news_fetcher.py   # 10 unit tests - news retrieval
├── test_notifier.py       # 10 unit tests - notifications
└── test_utils.py          # 8 unit tests - utilities
```

**Total: 43 tests** covering all core functionality.

### Running Tests

**Install development dependencies first:**
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

**Run specific test file:**
```bash
pytest tests/test_stock_fetcher.py -v
```

**Run specific test class:**
```bash
pytest tests/test_notifier.py::TestNotifier -v
```

### Test Coverage

The test suite achieves **98% coverage** and includes:

- ✅ **Config Management**: Environment variable loading and defaults
- ✅ **Stock Fetcher**:
  - API interactions with Alpha Vantage
  - Percentage change calculations (positive/negative)
  - Error handling (timeouts, API errors, invalid responses)
- ✅ **News Fetcher**:
  - Article retrieval from News API
  - Query parameter validation
  - Error handling and edge cases
- ✅ **Notifier**:
  - WhatsApp and SMS message sending
  - Lazy client initialization
  - Credential validation
  - Twilio exception handling
- ✅ **Utils**:
  - CSV stock loading and validation
  - Report generation with various scenarios
  - Logging configuration
- ✅ **Integration**:
  - Complete application workflow
  - Multiple stock processing
  - Alert triggering logic
  - Error recovery

View detailed coverage report:
```bash
pytest --cov=src --cov=main --cov-report=html
open htmlcov/index.html  # Opens coverage report in browser
```

### Continuous Integration

All tests run automatically on every push and pull request via GitHub Actions. The CI pipeline includes:
- **Code Linting**: flake8 for code style enforcement
- **Unit Tests**: Full test suite with pytest
- **Coverage Reporting**: Automatic upload to Codecov
- **Multi-Python Support**: Tests run on Python 3.7+

Check the CI status badge at the top of this README!

## 🤝 Contributing

Contributions are welcome! Here are some ideas for future enhancements:

- [ ] Add support for cryptocurrency monitoring
- [ ] Implement email notifications
- [ ] Create a web dashboard
- [ ] Add historical price tracking with SQLite
- [ ] Generate price charts with matplotlib
- [x] Add unit tests and CI/CD ✅
- [x] Modularize codebase with clean architecture ✅
- [x] Achieve high test coverage (98%) ✅

### Development Setup

1. Fork and clone the repository
2. Install dependencies: `pip install -r requirements-dev.txt`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Make your changes and add tests
5. Run tests: `pytest --cov=src --cov=main`
6. Ensure linting passes: `flake8 .`
7. Commit and push: `git commit -m "Add amazing feature"`
8. Create a Pull Request

All PRs must:
- Include tests for new functionality
- Maintain or improve code coverage
- Pass all CI checks (tests, linting, coverage)

## ⚠️ Disclaimer

This tool is for informational purposes only. It is not financial advice. Always do your own research before making investment decisions.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Raúl Jiménez Barco**
- GitHub: [@Veregorn](https://github.com/Veregorn)
- LinkedIn: [rjbarco](https://linkedin.com/in/rjbarco)

## 🙏 Acknowledgments

- Alpha Vantage for providing free stock market data
- News API for financial news aggregation
- Twilio for messaging infrastructure

---

⭐ **Star this repo if you found it helpful!**
