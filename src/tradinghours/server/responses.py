from typing import List, Optional, Union, Any, Dict
from datetime import date, datetime, time
from pydantic import BaseModel, Field, ConfigDict, field_serializer

class BaseResponseModel(BaseModel):
    # Pydantic v2 configuration
    model_config = ConfigDict(
        extra="allow",         # Allows additional fields not defined in schema
    )

class MarketResponse(BaseResponseModel):
    fin_id: str
    exchange_name: Optional[str] = None
    market_name: Optional[str] = None
    security_group: Optional[str] = None
    timezone: Optional[str] = None
    weekend_definition: Optional[str] = None
    mic: Optional[str] = None
    acronym: Optional[str] = None
    asset_type: Optional[str] = None
    memo: Optional[str] = None
    permanently_closed: Optional[date] = None
    replaced_by: Optional[str] = None   
    country_code: Optional[str] = None
    holidays_min_date: Optional[date] = None
    holidays_max_date: Optional[date] = None
    
class MarketHolidayResponse(BaseResponseModel):
    fin_id: str
    date: date
    holiday_name: Optional[str] = None
    schedule: Optional[str] = None
    settlement: Optional[str] = None
    observed: bool
    memo: Optional[str] = None
    status: Optional[str] = None
    has_settlement: bool
    is_open: bool

class PhaseResponse(BaseResponseModel):
    phase_type: str
    start: datetime
    end: datetime
    phase_name: Optional[str] = None
    phase_memo: Optional[str] = None
    status: Optional[str] = None
    settlement: Optional[str] = None
    timezone: Optional[str] = None
    has_settlement: bool
    is_open: bool

class ScheduleResponse(BaseResponseModel):
    fin_id: str
    schedule_group: Optional[str] = None
    schedule_group_memo: Optional[str] = None
    timezone: Optional[str] = None
    phase_type: Optional[str] = None
    phase_name: Optional[str] = None
    phase_memo: Optional[str] = None
    days: Optional[str] = None
    start: Optional[time] = None
    end: Optional[time] = None
    offset_days: Optional[int] = None
    duration: Optional[int] = None  
    min_start: Optional[time] = None
    max_start: Optional[time] = None
    min_end: Optional[time] = None
    max_end: Optional[time] = None
    in_force_start_date: Optional[date] = None
    in_force_end_date: Optional[date] = None
    season_start: Optional[str] = None
    season_end: Optional[str] = None
    has_season: bool

class MarketStatusResponse(BaseResponseModel):
    status: str
    reason: Optional[str] = None
    until: Optional[datetime] = None
    next_bell: Optional[datetime] = None
    phase: Optional[PhaseResponse] = None
    market: Optional[MarketResponse] = None

class CurrencyResponse(BaseResponseModel):
    currency_code: str
    currency_name: Optional[str] = None
    country_code: Optional[str] = None
    central_bank: Optional[str] = None
    financial_capital: Optional[str] = None
    financial_capital_timezone: Optional[str] = None
    weekend_definition: Optional[str] = None

class CurrencyHolidayResponse(BaseResponseModel):
    currency_code: str
    date: date
    holiday_name: Optional[str] = None
    settlement: Optional[str] = None
    observed: bool
    memo: Optional[str] = None
    

class IsAvailableResponse(BaseResponseModel):
    is_available: bool

