<div align="center">
<img src="https://www.tradinghours.com/img/logo-512x512.png" alt="TradingHours API Docs" height="100">
<h1>TradingHours.com Python Library</h1>
</div>

[TradingHours.com](https://www.tradinghours.com) licenses **Market Holidays and Trading Hours data** for over **1,000** exchanges and trading venues around the world.
This library allows clients to easily integrate market holidays and trading hours data into existing applications.
This packages downlods all available data from TradingHours.com and then allows you to work with the data locally.

### About the Data
We support over 1,000 exchanges and trading venues, including all major currencies.
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

[Learn more »](https://www.tradinghours.com/data)

### Getting Started

Just install `tradinghours` with pip and set your API key. [Click here to get your key](https://www.tradinghours.com/user/api-tokens).
```
pip install tradinghours

export TRADINGHOURS_TOKEN=<your-key-goes-here>
```
See [advanced configuration options](#optional-advanced-configuration). 

### Alternatives

Instead of using this Python Library, clients can also use the web-based [Trading Hours API](https://docs.tradinghours.com/). 
The web-based API is programming language agnostic.

---
### Contents
- [Importing Data](#importing-data)
- [Markets](#markets)
  - [View Available Markets](#view-available-markets)
  - [Get A Specific Market](#get-a-specific-market)
  - [Market Holidays](#market-holidays)
  - [Trading Hours](#trading-hours)
- [Currencies](#currencies)
  - [List Currencies](#list-currencies)
  - [Currency Holidays](#currency-holidays)
- [Advanced](#advanced)
  - [Optional Advanced Configuration](#optional-advanced-configuration)
  - [Database Schema](#database-schema)
  - [Time Zone Database](#time-zone-database)
  - [Model Configuration](#model-configuration)
    - [Change String Format](#change-string-format)

---
## Importing Data

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

## Markets

### View Available Markets
```python
from tradinghours import Market

for market in Market.list_all()[:3]:
    print(market)
    
>>> Market: AE.ADX Abu Dhabi Securities Exchange Asia/Dubai
    Market: AE.DFM Dubai Financial Market Asia/Dubai
    Market: AE.DGCX Dubai Gold & Commodities Exchange Asia/Dubai
```

### Get A Specific Market   

```python
from tradinghours import Market

# Get by either FinID or MIC
market = Market.get('US.NYSE')
market = Market.get('XNYS')

# Easily see what attributes an object has
# (You can call this on any object)
market.pprint() # same as pprint(market.to_dict())
>>> {'fin_id': 'US.NYSE',
     'exchange_name': 'New York Stock Exchange',
     'market_name': 'Canonical',
     'security_group': None,
     'mic': 'XNYS',
     'acronym': 'NYSE',
     'asset_type': 'Securities',
     'memo': 'Canonical',
     'permanently_closed': None,
     'timezone': 'America/New_York',
     'weekend_definition': 'Sat-Sun',
     'replaced_by': None,
     'country_code': 'US'}
```

If a market is marked "permanently closed" it may be replaced or superseded by another market. 
By default, the newer market will be returned automatically. You can still retrieve the 
older market object for historical analysis by using the `follow=False` parameter.

```python
from tradinghours import Market

# AR.BCBA is permanently closed and replaced by AR.BYMA
market = Market.get('AR.BCBA')
original = Market.get('AR.BCBA', follow=False)

print(f'{market.fin_id} replaced by {market.replaced_by} on {market.permanently_closed}')
print(f'{original.fin_id} replaced by {original.replaced_by} on {original.permanently_closed}')

>>> AR.BYMA replaced by None on None
    AR.BCBA replaced by AR.BYMA on 2017-04-17
```

### Market Holidays

```python
from tradinghours import Market

market = Market.get('US.NYSE')
holidays = market.list_holidays("2024-01-01", "2024-12-31")
for holiday in holidays[:3]:
    print(holiday)

>>> MarketHoliday: US.NYSE 2024-01-01 New Year's Day
    MarketHoliday: US.NYSE 2024-01-15 Birthday of Martin Luther King, Jr
    MarketHoliday: US.NYSE 2024-02-19 Washington's Birthday
```
### Trading Hours
#### Phases
To get open and closing times for a particular date range, use the `Market.generate_phases` method.
This will return a generator yielding `tradinghours.models.Phase` objects, representing specific datetimes. These are based on the "general schedule" of a market (see next section) but consider the impact of holidays and potential changes in the schedule.
```python
from tradinghours import Market

market = Market.get('XNYS')
for phase in list(market.generate_phases("2023-09-01", "2023-09-30"))[:3]:
    print(phase)

>>> Phase: 2023-09-01 04:00:00-04:00 - 2023-09-01 09:30:00-04:00 Pre-Trading Session
    Phase: 2023-09-01 06:30:00-04:00 - 2023-09-01 09:30:00-04:00 Pre-Open
    Phase: 2023-09-01 09:30:00-04:00 - 2023-09-01 09:30:00-04:00 Call Auction
```
#### Schedules
To get the "general schedule" that phases are based on, use `Market.list_schedules()`. This will provide a list of `tradinghours.models.Schedule` objects, representing the schedule without consideration of holidays. The schedule will include 'Regular,' 'Partial,' and potentially other irregular schedules. Interpreting the general schedule objects can be difficult. In most cases, you will want to use the `Market.generate_phases` method above.

`US.NYSE` is one of the simplest examples for schedules:
```python
from tradinghours import Market

market = Market.get('XNYS')
for schedule in market.list_schedules():
    print(schedule)

>>> Schedule: US.NYSE (Partial) 06:30:00 - 09:30:00    Mon-Fri Pre-Trading Session
    Schedule: US.NYSE (Partial) 09:30:00 - 13:00:00    Mon-Fri Primary Trading Session
    Schedule: US.NYSE (Partial) 13:00:00 - 13:30:00    Mon-Fri Post-Trading Session
    Schedule: US.NYSE (Regular) 04:00:00 - 09:30:00    Mon-Fri Pre-Trading Session
    Schedule: US.NYSE (Regular) 06:30:00 - 09:30:00    Mon-Fri Pre-Open
    Schedule: US.NYSE (Regular) 09:30:00 - 09:30:00    Mon-Fri Call Auction
    Schedule: US.NYSE (Regular) 09:30:00 - 16:00:00    Mon-Fri Primary Trading Session
    Schedule: US.NYSE (Regular) 15:50:00 - 16:00:00    Mon-Fri Pre-Close
    Schedule: US.NYSE (Regular) 16:00:00 - 20:00:00    Mon-Fri Post-Trading Session
```

`US.MGEX` is a more complex example, which has multiple irregular schedules and overnight trading sessions. (More on these fields in the next paragraph)
```python
from tradinghours import Market

market = Market.get('US.MGEX')
for schedule in market.list_schedules()[-11:-5]:
    print(schedule)

# US.MGEX has multiple irregular schedules and overnight trading sessions
>>> Schedule: US.MGEX (Regular) 19:00:00 - 07:45:00 +1 Sun-Thu Primary Trading Session
    Schedule: US.MGEX (Thanksgiving2022) 08:00:00 - 08:30:00    Wed Pre-Open
    Schedule: US.MGEX (Thanksgiving2022) 08:30:00 - 12:15:00    Fri Primary Trading Session
    Schedule: US.MGEX (Thanksgiving2022) 08:30:00 - 13:30:00    Wed Primary Trading Session
    Schedule: US.MGEX (Thanksgiving2022) 14:30:00 - 16:00:00    Wed Post-Trading Session
    Schedule: US.MGEX (Thanksgiving2022) 16:45:00 - 08:30:00 +2 Wed Pre-Open
```
The string representation created by `print(schedule)` is using the format shown below. Other available fields are also listed. These fields are based on the data that is returned from the API's `download` endpoint described [here](https://docs.tradinghours.com/3.x/enterprise/download.html).
```python
from tradinghours import Market
schedule = Market.get('US.MGEX').list_schedules()[-6]

print(schedule.get_string_format())
schedule.pprint() # same as pprint(schedule.to_dict())

>>> Schedule: {fin_id} ({schedule_group}) {start} - {end_with_offset} {days} {phase_type}
    {'fin_id': 'US.MGEX', # Fin ID of the market of this schedule
     'schedule_group': 'Thanksgiving2022', # Used to group phases together. If there is no holiday then the “Regular” phase applies.
     'schedule_group_memo': None, # additional description for the schedule_group
     'timezone': 'America/Chicago', # timezone of the market
     'phase_type': 'Pre-Open', # normalized name for the phase
     'phase_name': 'Pre-Open', # name for the phase as it is used by the market
     'phase_memo': None, # additional description for the phase_name
     'days': 'Wed', # days of the week that this schedule applies to
     'start': datetime.time(16, 45), # start time of the phase
     'end': datetime.time(8, 30), # end time of the phase
     'offset_days': 2, # number of days that need to be added to the end time
     'duration': '143100', # total length of this phase in seconds
     'min_start': None, # earliest possible start when random start/stop times apply
     'max_start': None, # latest possible start when random start/stop times apply
     'min_end': None, # earliest possible end when random start/stop times apply
     'max_end': None, # latest possible end when random start/stop times apply
     'in_force_start_date': None, # date that this schedule starts being in effect
     'in_force_end_date': None, # date that this schedule stops being in effect
     'season_start': None, # the start of the season, if this is seasonal
     'season_end': None, # the end of the season
     'end_with_offset': '08:30:00 +2', # string representation of the end time with offset_days concatenated
     'has_season': False} # Indicator whether this schedule only applies to a specific season
```
As mentioned previously, it can be very error-prone to interpret these schedules yourself, so we recommend sticking to the `generate_phases` method as much as possible.


## Currencies
### List Currencies

```python
from tradinghours import Currency

for currency in Currency.list_all()[:3]:
    print(currency)

>>> Currency: AUD Australian Dollar
    Currency: BRL Brazilian Real
    Currency: CAD Canadian Dollar
```

### Currency Holidays

```python
from tradinghours import Currency

currency = Currency.get('AUD')
for holiday in currency.list_holidays("2023-06-01", "2023-12-31")[:3]:
    print(holiday)

>>> CurrencyHoliday: AUD 2023-06-12 King's Birthday
    CurrencyHoliday: AUD 2023-10-02 Labor Day
    CurrencyHoliday: AUD 2023-12-25 Christmas Day
```

## Advanced
### Optional Advanced Configuration

By default, the library uses local file storage. Optionally you can 
configure the library to use an SQL store. You can adjust settings
using a **tradinghours.ini** file on the current working directory.

Here is a sample configuration file using file system storage:

```ini
[api]
token = YOUR-TOKEN-HERE

[data]
use_db = False
local_dir = /srv/tradinghours/local
remote_dir = /srv/tradinghours/remote
```

And here you can see one using a local SQL Alchemy database. Note that
you can use any valid [Database URL](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls):

```ini
[api]
token = YOUR-TOKEN-HERE

[data]
use_db = True
db_url = sqlite:///tradinghours.db
```

### Database Schema

In case you would like to directly access the tables for the SQL mode, you
can see that they all follow a very simple structure with keys for stored data
and the data with actual JSON. The library uses this simple structure that
should be compatible with nearly all database engines around.

Here is the DDL for the tables currently in use:

```sql
CREATE TABLE thstore_currencies (id INTEGER NOT NULL, slug VARCHAR, "key" VARCHAR, data JSON, PRIMARY KEY (id));
CREATE TABLE thstore_currency_holidays (id INTEGER NOT NULL, slug VARCHAR, "key" VARCHAR, data JSON, PRIMARY KEY (id));
CREATE TABLE thstore_holidays (id INTEGER NOT NULL, slug VARCHAR, "key" VARCHAR, data JSON, PRIMARY KEY (id));
CREATE TABLE thstore_markets (id INTEGER NOT NULL, slug VARCHAR, "key" VARCHAR, data JSON, PRIMARY KEY (id));
CREATE TABLE thstore_mic_mapping (id INTEGER NOT NULL, slug VARCHAR, "key" VARCHAR, data JSON, PRIMARY KEY (id));
CREATE TABLE thstore_schedules (id INTEGER NOT NULL, slug VARCHAR, "key" VARCHAR, data JSON, PRIMARY KEY (id));
CREATE TABLE thstore_season_definitions (id INTEGER NOT NULL, slug VARCHAR, "key" VARCHAR, data JSON, PRIMARY KEY (id));
```

### Time Zone Database 
This package employs `zoneinfo` for timezone management, utilizing the IANA Time Zone Database, 
which is routinely updated. In certain environments, it's essential to update the `tzdata` package accordingly. 
`tradinghours` automatically checks your `tzdata` version against PyPI via HTTP request, issuing a warning 
if an update is needed.

To update `tzdata` run this command: `pip install tzdata --upgrade`

To disable this verification and prevent the request, add this section to your tradinghours.ini file:
```ini
[control]
check_tzdata = False
```

## Model Configuration
### Change String Format
```python
from tradinghours import Currency

Currency.set_string_format("{currency_code}: {financial_capital} - {financial_capital_timezone}")
currency = Currency.get("EUR")
print(currency)

Currency.reset_string_format()
print(currency)

>>> EUR: Frankfurt - Europe/Berlin
    Currency: EUR Euro
```
