import datetime as dt
from typing import Iterable, Generator, Union
from zoneinfo import ZoneInfo

from .typing import StrOrDate
from .dynamic_models import (
    BaseModel,
    Schedule,
    Phase,
    PhaseType,
    MarketHoliday,
    MicMapping,
    SeasonDefinition
)
from .validate import validate_range_args, validate_date_arg, validate_finid_arg, validate_str_arg
from .store import db
from .util import weekdays_match
from .exceptions import NoAccess, NotCovered, MICDoesNotExist

# Arbitrary max offset days for TradingHours data
MAX_OFFSET_DAYS = 2

class Market(BaseModel):
    _table = "markets"
    _original_string_format = "Market: {fin_id} {exchange_name} {timezone}"

    def __init__(self, data):
        super().__init__(data)
        self.exchange_name = self._data["exchange_name"]
        self.market_name = self._data["market_name"]
        self.security_group = self._data["security_group"]
        self.timezone = self._data["timezone"]
        self.weekend_definition = self._data["weekend_definition"]
        self.fin_id = self._data["fin_id"]
        self.mic = self._data["mic"]
        self.acronym = self._data["acronym"]
        self.asset_type = self._data["asset_type"]
        self.memo = self._data["memo"]
        self.permanently_closed = self._data["permanently_closed"]
        self.replaced_by = self._data["replaced_by"]

    @property
    def country_code(self):
        """Two-letter country code."""
        return self.fin_id.split(".")[0]

    def _pick_schedule_group(
        self,
        some_date: dt.date,
        holidays: dict[dt.date, "MarketHoliday"],
    ) -> tuple[str, bool]:

        if found := holidays.get(some_date):
            schedule_group = found.schedule.lower()
            fallback = Schedule.is_group_open(schedule_group)
        else:
            schedule_group = "regular"
            fallback = False
        return schedule_group, fallback

    def _filter_schedule_group(
        self, schedule_group: str, schedules: Iterable[Schedule]
    ) -> Iterable[Schedule]:
        for current in schedules:
            if current.schedule_group.lower() == schedule_group.lower():
                yield current


    def _filter_inforce(
        self, some_date: dt.date, schedules: Iterable[Schedule]
    ) -> Iterable[Schedule]:
        for current in schedules:
            if current.is_in_force(some_date, some_date):
                yield current

    def _filter_season(
        self, some_date: dt.date, schedules: Iterable[Schedule]
    ) -> Iterable[Schedule]:
        for current in schedules:
            # If there is no season, it means there is no restriction in terms
            # of the season when this schedule is valid, and as such it is valid,
            # from a season-perspective for any date
            if not current.has_season:
                yield current
            else:
                start_date = SeasonDefinition.get(current.season_start, some_date.year).date
                end_date = SeasonDefinition.get(current.season_end, some_date.year).date

                if end_date < start_date:
                    if some_date <= end_date or some_date >= start_date:
                        yield current

                if some_date >= start_date and some_date <= end_date:
                    yield current

    def _filter_weekdays(
        self, weekday: int, schedules: Iterable[Schedule]
    ) -> Iterable[Schedule]:
        for current in schedules:
            if weekdays_match(current.days, weekday):
                yield current

    @db.check_access
    def generate_phases(
        self, start: StrOrDate, end: StrOrDate
    ) -> Generator[Phase, None, None]:
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        # print(f"generating phases between {start} and {end}")

        phase_types_dict = PhaseType.as_dict()
        # pprint(phase_types_dict)

        # Get required global data
        offset_start = start - dt.timedelta(days=MAX_OFFSET_DAYS)
        all_schedules = self.list_schedules()
        holidays = self.list_holidays(offset_start, end, as_dict=True)

        # Iterate through all dates generating phases
        current_date = offset_start
        while current_date <= end:
            current_weekday = current_date.weekday()
            # Starts with all schedules
            schedules = all_schedules

            # Filter schedule group based on holiday if any
            schedule_group, fallback = self._pick_schedule_group(current_date, holidays)
            schedules = self._filter_schedule_group(schedule_group, schedules)

            # Filters what is in force or for expected season
            schedules = self._filter_inforce(current_date, schedules)
            schedules = self._filter_season(current_date, schedules)

            # Save for fallback and filter weekdays
            before_weekdays = list(schedules)
            found_schedules = list(self._filter_weekdays(current_weekday, before_weekdays))

            # Consider fallback if needed
            if not found_schedules and fallback:
                fallback_weekday = 6 if current_weekday == 0 else current_weekday - 1
                fallback_schedules = []
                while not fallback_schedules and fallback_weekday != current_weekday:
                    fallback_schedules = list(
                        filter(
                            lambda s: weekdays_match(s.days, fallback_weekday),
                            before_weekdays,
                        ),
                    )
                    fallback_weekday = (
                        6 if fallback_weekday == 0 else fallback_weekday - 1
                    )
                found_schedules = fallback_schedules

            # Sort based on start time and duration
            found_schedules = sorted(
                found_schedules,
                key=lambda s: (s.start, s.duration),
            )

            # Generate phases for current date
            for current_schedule in found_schedules:
                start_date = current_date
                end_date = current_date + dt.timedelta(days=current_schedule.offset_days)

                # Filter out phases not finishing after start because we
                # began looking a few days ago to cover offset days
                if end_date >= start:
                    start_datetime = dt.datetime.combine(start_date, current_schedule.start)
                    end_datetime = dt.datetime.combine(end_date, current_schedule.end)
                    # start_datetime = current_schedule.timezone_obj.localize(start_datetime)
                    # end_datetime = current_schedule.timezone_obj.localize(end_datetime)
                    zoneinfo_obj = ZoneInfo(current_schedule.timezone)
                    start_datetime = start_datetime.replace(tzinfo=zoneinfo_obj)
                    end_datetime = end_datetime.replace(tzinfo=zoneinfo_obj)

                    phase_type = phase_types_dict[current_schedule.phase_type]
                    yield Phase(
                        dict(
                            phase_type=current_schedule.phase_type,
                            phase_name=current_schedule.phase_name,
                            phase_memo=current_schedule.phase_memo,
                            status=phase_type.status,
                            settlement=phase_type.settlement,
                            start=start_datetime,
                            end=end_datetime,
                        )
                    )

            # Next date, please
            current_date += dt.timedelta(days=1)

    @classmethod
    def list_all(cls) -> list["Market"]:
        return [cls(r) for r in db.query(cls.table)]


    def list_holidays(
        self, start: StrOrDate, end: StrOrDate, as_dict: bool = False
    ) -> Union[list["MarketHoliday"], dict[dt.date, "MarketHoliday"]]:
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        table = MarketHoliday.table
        result = db.query(table).filter(
            table.c.fin_id == self.fin_id,
            table.c.date >= start,
            table.c.date <= end
        )
        if as_dict:
            dateix = list(table.c.keys()).index("date")
            return {
                r[dateix]: MarketHoliday(r) for r in result
            }

        return [MarketHoliday(r) for r in result]

    @db.check_access
    def list_schedules(self) -> list["Schedule"]:
        schedules = db.query(Schedule.table).filter(
            Schedule.table.c.fin_id == self.fin_id
        ).order_by(
            Schedule.table.c.schedule_group.asc(),
            Schedule.table.c.in_force_start_date.asc(),
            Schedule.table.c.season_start.asc(),
            Schedule.table.c.start.asc(),
            Schedule.table.c.end.asc()
        )
        return [Schedule(r) for r in schedules]

    @classmethod
    def is_available(cls, identifier: str) -> bool:
        """
        Return True or False to show if a mic or finid can be accessed
        under the current plan.
        """
        try:
            cls.get(identifier)
            return True
        except (NoAccess, NotCovered, MICDoesNotExist):
            return False

    @classmethod
    def is_covered(cls, finid: str) -> bool:
        """
        Returns True or False showing if tradinghours provides data for the Market.
        This differs from is_available because is_covered does not mean that the user
        has access to it under their current plan.
        """
        table = db.table("covered_markets")
        found = db.query(table).filter(
            table.c.fin_id == finid
        ).one_or_none()
        return found is not None

    @classmethod
    def _get_by_finid(cls, finid:str, following=None) -> Union[None, tuple]:
        found = db.query(cls.table).filter(
            cls.table.c.fin_id == finid
        ).one_or_none()
        if found is not None:
            return found

        # if not found, check if it is covered at all and raise appropriate Exception
        following = f" (replaced: '{following}')" if following else ""
        if cls.is_covered(finid):
            raise NoAccess(
                f"\n\nThe market '{finid}'{following} is supported but not available on your current plan."
                f"\nPlease learn more or contact sales at https://www.tradinghours.com/data"
            )
        raise NotCovered(
            f"The market '{finid}'{following} is currently not available."
        )

    @classmethod
    def get_by_finid(cls, finid: str, follow=True) -> Union[None, "Market"]:
        finid = finid.upper()
        finid = validate_finid_arg("finid", finid)
        found = cls._get_by_finid(finid)

        while found and (found_obj := cls(found)).replaced_by and follow:
            found = cls._get_by_finid(found_obj.replaced_by, following=finid)

        return found_obj


    @classmethod
    def get_by_mic(cls, mic: str, follow=True) -> "Market":
        mic = mic.upper()
        mic = validate_str_arg("mic", mic)
        mapping = db.query(MicMapping.table).filter(
            MicMapping.table.c.mic == mic
        ).one_or_none()
        if mapping:
            return cls.get_by_finid(mapping.fin_id, follow=follow)
        raise MICDoesNotExist(f"The MIC {mic} could not be matched with a FinID")

    @classmethod
    def get(cls, identifier: str, follow=True) -> "Market":
        identifier = validate_str_arg("identifier", identifier)
        if "." in identifier:
            found = cls.get_by_finid(identifier, follow=follow)
        else:
            found = cls.get_by_mic(identifier, follow=follow)
        return found
