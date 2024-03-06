from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, DateTime, Time, Boolean

Base = declarative_base()


from ..config import main_config


engine = create_engine(main_config.get('data', 'db_url'), echo=True)


#currency
## Currency

class Currency(Base):
    __tablename__ = 'thstore_currencies'

    id = Column(Integer, primary_key=True)
    currency_code = Column(String(3), nullable=False, comment="3-letter code of the currency (ISO 4217).")
    currency_name = Column(String, nullable=False, comment="English name of the currency.")
    country_code = Column(String(2), nullable=False, comment="2-letter country code for the currency's country.")
    central_bank = Column(String, nullable=True, comment="Name of the central bank for the currency.")
    financial_capital = Column(String, nullable=True, comment="City where the central bank is located.")
    financial_capital_timezone = Column(String, nullable=True, comment="Timezone Olson timezone identifier format.")
    weekend_definition = Column(String, nullable=True, comment="Weekend definition. Most markets are Sat-Sun.")

## CurrencyHoliday
class CurrencyHoliday(Base):
    __tablename__ = 'thstore_currency_holidays'

    id = Column(Integer, primary_key=True)
    currency_code = Column(String(3), nullable=False)
    date = Column(Date, nullable=False)
    holiday_name = Column(String, nullable=False)
    settlement = Column(String, nullable=True)
    observed = Column(Boolean, nullable=False)
    memo = Column(String, nullable=True)


#market
## Market
class Market(Base):
    __tablename__ = 'thstore_markets'

    id = Column(Integer, primary_key=True)
    fin_id = Column(String, nullable=False)
    exchange_name = Column(String, nullable=False)
    market_name = Column(String, nullable=False)
    security_group = Column(String, nullable=True)
    mic = Column(String, nullable=True)
    acronym = Column(String, nullable=True)
    asset_type = Column(String, nullable=True)
    memo = Column(String, nullable=True)
    permanently_closed = Column(Date, nullable=True)
    timezone = Column(String, nullable=True)
    weekend_definition = Column(String, nullable=True)
    replaced_by = Column(String, nullable=True)

## MarketHoliday
class MarketHoliday(Base):
    __tablename__ = 'thstore_market_holidays'

    id = Column(Integer, primary_key=True)
    fin_id = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    holiday_name = Column(String, nullable=False)
    schedule = Column(String, nullable=True)
    settlement = Column(String, nullable=True)
    observed = Column(Boolean, nullable=False)
    memo = Column(String, nullable=True)
    status = Column(String, nullable=True)

## MicMapping
class MicMapping(Base):
    __tablename__ = 'thstore_mic_mappings'

    id = Column(Integer, primary_key=True)
    mic = Column(String, nullable=False)
    fin_id = Column(String, nullable=False)

#schedule
## PhaseType
class PhaseType(Base):
    __tablename__ = 'thstore_phase_types'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    settlement = Column(String, nullable=False)

## Phase (GENERATED)
class Phase(Base):
    __tablename__ = 'thstore_phases'

    id = Column(Integer, primary_key=True)
    phase_type = Column(String, nullable=False)
    phase_name = Column(String, nullable=False)
    phase_memo = Column(String, nullable=True)
    status = Column(String, nullable=False)
    settlement = Column(String, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)

## Schedule

class Schedule(Base):
    __tablename__ = 'thstore_schedules'

    id = Column(Integer, primary_key=True)
    fin_id = Column(String, nullable=False)
    schedule_group = Column(String, nullable=False)
    schedule_group_memo = Column(String, nullable=True)
    timezone = Column(String, nullable=False)
    phase_type = Column(String, nullable=False)
    phase_name = Column(String, nullable=False)
    phase_memo = Column(String, nullable=True)
    days = Column(String, nullable=False)
    start = Column(Time, nullable=False)
    end = Column(Time, nullable=False)
    offset_days = Column(Integer, nullable=False)
    duration = Column(String, nullable=False)
    min_start = Column(Time, nullable=True)
    max_start = Column(Time, nullable=True)
    min_end = Column(Time, nullable=True)
    max_end = Column(Time, nullable=True)
    in_force_start_date = Column(Date, nullable=False)
    in_force_end_date = Column(Date, nullable=True)
    season_start = Column(String, nullable=True)
    season_end = Column(String, nullable=True)

#season
## SeasonDefinition

class SeasonDefinition(Base):
    __tablename__ = 'thstore_season_definitions'

    id = Column(Integer, primary_key=True)
    season = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)

