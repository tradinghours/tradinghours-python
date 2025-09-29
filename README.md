<div align="center">
  <img src="https://www.tradinghours.com/img/logo-512x512.png" alt="TradingHours API Docs" height="100">
  <h1>TradingHours.com Python Library</h1>

  <!-- Badges centered -->
  <p>
    <a href="https://badge.fury.io/py/tradinghours">
      <img src="https://badge.fury.io/py/tradinghours.svg" alt="PyPI version">
    </a>
    <img src="https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-green" alt="Python versions">
    <img src="https://github.com/tradinghours/tradinghours-python/actions/workflows/release.yml/badge.svg?branch=main" alt="GitHub Actions">
  </p>
</div>

[TradingHours.com](https://www.tradinghours.com) licenses **Market Holidays and Trading Hours data** for over **1,000** exchanges and trading venues around the world. This library allows clients to easily integrate market holidays and trading hours data into existing applications. This package downloads all available data from TradingHours.com, allowing you to work with the data locally.

### About the Data
We support over 1,000 exchanges and trading venues, including all major currencies. [See all supported markets.](https://www.tradinghours.com/coverage)

Our comprehensive data covers:

- Market holidays
- Trading hours
- Half-days / Irregular schedules
- Non-settlement dates
- Currency holidays
- Detailed trading phases

### How is the data collected?
Our global research team collects and verifies trading hours and market holidays using primary sources exclusively. Manual and automated checks ensure the highest degree of accuracy and reliability.

Once data is collected, we continually monitor for changes to ensure the data is always up-to-date. Data updates occur daily.

### Getting Started

To get started, you'll need an active subscription. [Learn more »](https://www.tradinghours.com/data)

1. Install the `tradinghours` package
   
   ```sh
   pip install tradinghours
   ```
   
2. Set your API Key ([Click here to get your key](https://www.tradinghours.com/user/api-tokens))

   ```sh
   export TRADINGHOURS_TOKEN=<your-key-goes-here>
   ```

You can also install with mysql, postgres, or server dependencies, if you wish to use one of these. You can read more about this in [advanced configuration options](#optional-advanced-configuration).
```sh
pip install tradinghours[mysql] 
# or 
pip install tradinghours[postgres]
# or
pip install tradinghours[server]
```

### Alternatives

Instead of using this Python Library, clients can also use the web-based [Trading Hours API](https://docs.tradinghours.com/).
The web-based API is programming language agnostic.

### Contents
- [Importing Data](#importing-data)
- [Markets](#markets)
  - [View Available Markets](#view-available-markets)
  - [Get a Specific Market](#get-a-specific-market)
  - [Market Status](#market-status)
  - [Market Holidays](#market-holidays)
  - [Trading Hours](#trading-hours)
- [Currencies](#currencies)
  - [List Currencies](#list-currencies)
  - [Currency Holidays](#currency-holidays)
- [Advanced](#advanced)
  - [Optional Advanced Configuration](#optional-advanced-configuration)
  - [Package Mode](#package-mode)
  - [Server Mode](#server-mode)
  - [Time Zones](#time-zones)
  - [Model Configuration](#model-configuration)
    - [Change String Format](#change-string-format)

---
## Importing Data

Run the following command to download and import official data. Ensure you have set the **TRADINGHOURS_TOKEN** environment variable.

```console
$ tradinghours import
Downloading..... (0.824s)
Ingesting.......................... (12.066s)
```

You can check the current data status with the following subcommand:

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

You can also use an `*` to filter the list of markets based on their `fin_id`:

```python
from tradinghours import Market

for market in Market.list_all("US.*")[:3]:
  print(market)

>>> Market: US.BTEC.ACTIVES.ASIA BrokerTec America/New_York
    Market: US.BTEC.ACTIVES.LDN BrokerTec America/New_York
    Market: US.BTEC.ACTIVES.US BrokerTec America/New_York
```

### Get a Specific Market

```python
from tradinghours import Market

# Get by either FinID or MIC
market = Market.get('US.NYSE')
market = Market.get('XNYS')

# Easily see what attributes an object has
# (You can call this on any object)
market.pprint() # same as pprint(market.to_dict())
>>> {'exchange_name': 'New York Stock Exchange',
     'market_name': 'Canonical',
     'security_group': None,
     'timezone': 'America/New_York',
     'weekend_definition': 'Sat-Sun',
     'fin_id': 'US.NYSE',
     'mic': 'XNYS',
     'acronym': 'NYSE',
     'asset_type': 'Securities',
     'memo': 'Canonical',
     'permanently_closed': None,
     'replaced_by': None,
     'country_code': 'US',
     'first_available_date': '2000-01-01',
     'last_available_date': '2033-12-31'}
```

If a market is marked "permanently closed," it may be replaced or superseded by another market. By default, the newer market will be returned automatically. You can retrieve the older market object for historical analysis by using the `follow=False` parameter.

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

### Market Status
The `Market.status` method will return a `MarketStatus` representing the status of the market at a specific datetime.

```python
from tradinghours import Market
import datetime as dt

market = Market.get("US.NYSE")
status = market.status()
# The default datetime is the current time.
now = dt.datetime.now(dt.timezone.utc)
print(
  status.status == market.status(now).status
)
>>> True
```
To use a different datetime, create a timezone-aware datetime object.

```python
from tradinghours import Market
from zoneinfo import ZoneInfo
import datetime as dt

christmas_noon = dt.datetime(2024,12,25,12,tzinfo=ZoneInfo("America/New_York"))
status = Market.get("US.NYSE").status(christmas_noon)

status.pprint() # same as pprint(status.to_dict())
>>> {'status': 'Closed',
     'reason': 'Christmas',
     'until': '2024-12-26 04:00:00-05:00',
     'next_bell': '2024-12-26 09:30:00-05:00',
     'phase': None,
     'market': 'Market: US.NYSE New York Stock Exchange America/New_York'}
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
To get opening and closing times for a particular date range, use the `Market.generate_phases` method. This will return a generator yielding `tradinghours.models.Phase` objects, representing specific datetimes based on the "general schedule" of a market, considering holidays and potential schedule changes.

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
To get the "general schedule" that phases are based on, use `Market.list_schedules()`. This will provide a list of `tradinghours.models.Schedule` objects, representing the schedule without consideration of holidays. The schedule will include 'Regular,' 'Partial,' and potentially other irregular schedules. Interpreting these schedule objects can be difficult. In most cases, you will want to use the `Market.generate_phases` method above.

`US.NYSE` is one of the simplest examples for schedules:
```python
from tradinghours import Market

market = Market.get('XNYS')
for schedule in market.list_schedules()[:10]:
    print(schedule)

>>> Schedule: US.NYSE (Partial) 06:30:00 - 09:30:00    Mon-Fri Pre-Trading Session
    Schedule: US.NYSE (Partial) 09:30:00 - 13:00:00    Mon-Fri Primary Trading Session
    Schedule: US.NYSE (Partial) 13:00:00 - 13:30:00    Mon-Fri Post-Trading Session
    Schedule: US.NYSE (Partial) 06:30:00 - 09:30:00    Mon-Fri Pre-Trading Session
    Schedule: US.NYSE (Partial) 09:30:00 - 13:00:00    Mon-Fri Primary Trading Session
    Schedule: US.NYSE (Regular) 04:00:00 - 09:30:00    Mon-Fri Pre-Trading Session
    Schedule: US.NYSE (Regular) 06:30:00 - 09:30:00    Mon-Fri Pre-Open
    Schedule: US.NYSE (Regular) 09:30:00 - 09:30:00    Mon-Fri Call Auction
    Schedule: US.NYSE (Regular) 09:30:00 - 16:00:00    Mon-Fri Primary Trading Session
    Schedule: US.NYSE (Regular) 15:45:00 - 16:00:00    Mon-Fri Pre-Close
```

`US.MGEX` is a more complex example, which has multiple irregular schedules and overnight trading sessions:

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
     'start': '16:45:00', # start time of the phase
     'end': '08:30:00', # end time of the phase
     'offset_days': 2, # number of days that need to be added to the end time
     'duration': 143100, # total length of this phase in seconds
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
As mentioned earlier, it can be very error-prone to interpret these schedules yourself, so we recommend sticking to the `generate_phases` method as much as possible.

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

Configuration can be changed by creating a `tradinghours.ini` file in the current directory.

These are possible and optional values, for which explanations follow:

```ini
[auth]
token = YOUR-TOKEN

[package-mode]
db_url = postgresql://postgres:password@localhost:5432/your_database
table_prefix = thstore_

[server-mode]
allowed_hosts = *
allowed_origins = *
log_folder = tradinghours_server_logs
log_level = DEBUG
log_days_to_keep = 7

[extra]
check_tzdata = True
```

## Package Mode
When using this package the regular way (i.e as a python import), it is possible to make `tradinghours import` load data into a database of your choice and allowing other team members to use the same database.
* `[package-mode]`
  * `db_url`
    * A connection string to a database. Please read the [caveats](#caveats) before using this setting.
    * This allows you to download the data once and let your team members use the same database.
    * If not specified, uses SQLite by default.
  * `table_prefix`
    * Every table created in the database will be prefixed with this. `'thstore_'` is the default.
    * This can be used to avoid conflicts with existing tables.

#### Caveats
* The `[package-mode]` setting cannot be used with `tradinghours serve`
* This package has been tested with MySQL 8.4 and PostgreSQL 15.8
* Dependencies:
  * Running `pip install tradinghours[mysql]` or `pip install tradinghours[postgres]` installs `pymysql` or `psycopg2-binary`, respectively.
  * You can install any other package (e.g. `mysqlclient`), as long as it allows `sqlalchemy` to communicate with the chosen database.
* Data ingestion:
  * Tables used by this package (identified by the `table_prefix`) are dropped and recreated every time `tradinghours import` is run. 
  * To avoid any complications with existing data, we recommend creating a separate database for the `tradinghours` data, and making this the only database the `db_url` user has access to.

##### Schema
* The tables are named after the CSV files, with `_` instead of `-` and prefixed with the `table_prefix` setting.
* To allow flexibility with updates to the raw data, where columns might be added in the future, tables are created dynamically, based on the content of the CSV files.
* Columns of the tables are named after the columns of the CSV files, although in lower case and with underscores instead of spaces.

## Server Mode
This package can also be used to run a server by running `tradinghours serve`, for which you need to install the server dependencies with `pip install tradinghours[server]`. When running a server, you cannot have `[package-mode]` settings in your tradinghours.ini file to make it clear that the server will only use the default database settings.

Keeping all default settings, the server will run on `http://127.0.0.1:8000`. You can visit the Swagger UI at `http://127.0.0.1:8000/docs` to explore the API, which is a very close replica of the main interface of this package.

The server is a FastAPI application, using gunicorn to run uvicorn worker processes. By default, every minute, the server will check if data needs to be updated and import it if needed  (i.e `tradinghours import`). With the `[server-mode]` section, the following settings can be overridden:

* `[server-mode]`
  * `allowed_hosts`
    * Comma-separated list of hosts allowed to access the API server. Use `*` for all hosts.
  * `allowed_origins`
    * Comma-separated list of origins allowed for CORS requests. Use `*` for all origins.
  * `log_folder`
    * The folder in which to keep logs with daily rotation
  * `log_level`
    * The level at which to log
  * `log_days_to_keep`
    * The number of log files to keep in `log_folder`
  * **Important**: Server mode cannot use custom `[package-mode]` settings and must use the default SQLite database.

To launch the server, run `tradinghours serve`, which takes these otional command line arguments:
* `--host`
  * The host to bind to. (default: `127.0.0.1`)
* `--port`
  * The port to bind to. (default: `8000`)
* `--uds`
  * The Unix domain socket path to bind to. (overrides host/port for faster local communication)
* `--no-auto-update`
  * Disable the minute-by-minute check and potential update of data.


### Time Zones
This package employs `zoneinfo` for timezone management, utilizing the IANA Time Zone Database, 
which is routinely updated. In certain environments, it's essential to update the `tzdata` package accordingly. 
`tradinghours` automatically checks your `tzdata` version against PyPI via HTTP request, issuing a warning 
if an update is needed.

To update `tzdata` run this command: `pip install tzdata --upgrade`

To disable this verification and prevent the request, add this section to your tradinghours.ini file:
```ini
[extra]
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
