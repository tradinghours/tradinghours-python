<div align="center">
<img src="https://www.tradinghours.com/img/logo-512x512.png" alt="TradingHours API Docs" height="100">
<h1>TradingHours.com Python Library</h1>
</div>

[TradingHours.com](https://www.tradinghours.com) licenses **Market Holidays and Trading Hours data** for over 900 exchanges and trading venues around the world.
This library allows clients to easily integrate our market holidays and trading hours data into existing applications.
This packages downlods all available data from TradingHours.com and then allows you to work with the data locally. 

**A paid subscription is required to use this package**

[Learn more »](https://www.tradinghours.com/data)

## About the Data

### Market coverage

We supports over 900 exchanges and trading venues, including all major currencies.
[See all supported markets](https://www.tradinghours.com/coverage).

Our comprehensive data covers:

- Market holidays
- Trading hours
- Half-days / Irregular schedules
- Non-settlement dates
- Currency holidays
- Detailed trading phases

### How is data collected?

Our global research team collects and verifies trading hours and market holidays using exclusively primary sources.
Manual and automated checks ensure the highest degree of accuracy and reliability.

Once data is collected, we then continually monitor for changes to ensure the data is always up-to-date.
Data is updated daily.

## Installation

```console
pip install tradinghours
```

## Configuration

```console
export TRADINGHOURS_TOKEN=<your-token-goes-here>
```

If you have an active subscription, [click here to get your API key](https://www.tradinghours.com/user/api-tokens).

## Usage

### Importing Data

You just need to run the following command to download and import official data. Remember that you need to have a valid **TRADINGHOURS_TOKEN** environment variable.

```console
$ tradinghours import
Downloading..... (0.824s)
Ingesting.......................... (12.066s)
```

You can then check current data status with the following subcommand:

```console
$ tradinghours status --extended
Collecting timestamps.... (0.213s)
TradingHours Data Status:
  Remote Timestamp:   Thu Oct 26 02:08:17 2023
  Local Timestamp:    Thu Oct 26 03:12:40 2023

Reading local data.... (0.426s)
Extended Information:
  Currencies count:   30
  Markets count:      1012
```

### List Markets

```python
from tradinghours.market import Market

for market in Market.list_all():
    print(market)
```

### Get Market

```python
from tradinghours.market imort Market

# Get by either FinID or MIC
market = Market.get('US.IEX')
market = Market.get('IEXG')
```

### Market Holidays

```python
from tradinghours.market imort Market

market = Market.get('US.IEX')
for holiday in market.list_holidays("2023-06-01", "2023-12-31"):
    print(holiday)
```

### Trading Hours

```python
from tradinghours.market imort Market

market = Market.get('IEXG')
for concrete_phase in market.generate_schedules("2023-09-01", "2023-09-30"):
    print(concrete_phase)
```

### List Currencies

```python
from tradinghours.currency import Currency

for currency in Currency.list_all():
    print(currency)
```

### Currency Holidays

```python
from tradinghours.currency import Currency

currency = Currency.get('AUD')
for holiday in currency.list_holidays("2023-06-01", "2023-12-31"):
    print(currency)
```
