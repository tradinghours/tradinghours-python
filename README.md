![tradinghours-client-banner](https://github.com/tradinghours/tradinghours-python/assets/2868028/839859a1-ff8c-48a3-8ed9-7e11a76ee446)

# TradingHours.com Python Library

[TradingHours.com](https://www.tradinghours.com) licenses Market Holidays and Trading Hours data for over 900 exchanges and trading venues around the world.
This package allows clients to easily integrate our market holidays and trading hours data into existing applications.
Using this package, data is downloaded from the TradingHours.com service and is then available for local, offline use.

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

## Usage

### Importing Data

```console
python -m tradinghours.import
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
from tradinghours.structure import FinId

fin_id = FinId(country='US', acronym='IEX')
market = Market.get_by_fin_id(fin_id)
```

### Market Holidays

```python
from tradinghours.market imort Market
from tradinghours.structure import FinId

fin_id = FinId(country='US', acronym='IEX')
market = Market.get_by_fin_id(fin_id)
for holiday in market.list_holidays("2023-06-01", "2023-12-31"):
    print(holiday)
```

### Trading Hours

```python
from tradinghours.market imort Market
from tradinghours.structure import FinId

fin_id = FinId(country='US', acronym='IEX')
market = Market.get_by_fin_id(fin_id)
for concrete_phase in market.generate_schedules(date(2023, 9, 1), date(2023, 9, 30)):
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
