<div align="center">
  <img src="https://www.tradinghours.com/img/logo-512x512.png" alt="TradingHours API Docs" height="100">
  <h1>TradingHours.com Python Library</h1>

  <p>
    <a href="https://pypi.org/project/tradinghours/">
      <img src="https://img.shields.io/pypi/v/tradinghours?color=green" alt="PyPI version">
    </a>
    <img src="https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-green" alt="Python versions">
    <img src="https://github.com/tradinghours/tradinghours-python/actions/workflows/release.yml/badge.svg?branch=main" alt="GitHub Actions">
  </p>
</div>

Official Python library for [TradingHours.com](https://www.tradinghours.com). Download market holidays and trading hours data locally for **fast, offline access** to 1,000+ exchanges worldwide.

## About the Data

We support over **1,000 exchanges and trading venues** around the world, including all major currencies. [See all supported markets →](https://www.tradinghours.com/data/coverage)

**Data Coverage:**
- Market holidays and non-settlement dates
- Trading hours with detailed phase information
- Half-days and irregular schedules
- Currency holidays for FX markets
- Pre-trading, post-trading, and auction times

**Data Quality:**

Our global research team collects and verifies trading hours and market holidays using **primary sources exclusively**. Manual and automated checks ensure the highest degree of accuracy and reliability. Data updates occur **daily**.

---

## Why Use the Python Library?

- ⚡ **Blazing fast** - No network latency, instant queries from local database
- 🚫 **No rate limits** - Run unlimited queries without throttling
- 💾 **Offline access** - Works completely offline after initial download
- 🔧 **Simple integration** - Simple and user-friendly interface handles all complexity

**[View complete documentation →](https://docs.tradinghours.com/python-library/)**

## Two Modes of Operation

### 📦 Package Mode
**Use as a Python package**
```bash
pip install tradinghours
tradinghours import
```
```python
from tradinghours import Market
Market.get('US.NYSE')
```

Perfect for:
- Python applications & scripts
- Data analysis & backtesting  
- Trading algorithms

**[📖 Documentation →](https://docs.tradinghours.com/python-library/package-mode/getting-started)**

---

### 🚀 Server Mode
**Run as REST API server**
```bash
pip install tradinghours[server]
tradinghours serve
```
```bash
>> curl http://127.0.0.1:8000/markets/US.NYSE
{"fin_id":"US.NYSE","exchange_name":"New York...
```

Perfect for:
- Microservice and multi-language infrastructure
- Low latency and no rate limits
- Fully private and on-premise hosting

**[📖 Documentation →](https://docs.tradinghours.com/python-library/server-mode/getting-started)**

## Requirements

- **Python**: 3.9 or higher
- **Subscription**: Active TradingHours.com subscription ([get a quote](https://www.tradinghours.com/data))
- **API Token**: Available from [your account page](https://www.tradinghours.com/user/api-tokens)

## Alternative: Web API

Prefer not to install a Python library? Use our [REST API](https://docs.tradinghours.com/3.x/introduction), access the data on the [Snowflake Marketplace](https://app.snowflake.com/marketplace/listing/GZTSZ1CSMLC), or [get in touch](https://www.tradinghours.com/contact) with us for more information.

## License

Commercial - See [TradingHours.com](https://www.tradinghours.com/data) for licensing details.
