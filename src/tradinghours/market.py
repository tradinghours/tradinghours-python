import datetime as dt
from typing import Iterable, Generator, Union

from .typing import StrOrDate
from .dynamic_models import BaseModel, Schedule, Phase, PhaseType, MarketHoliday, MicMapping
from .validate import validate_range_args, validate_date_arg, validate_finid_arg, validate_str_arg
from .store import db

# Arbitrary max offset days for TradingHours data
MAX_OFFSET_DAYS = 2

class Market(BaseModel):
    _table = "markets"

    @property
    def country_code(self):
        """Two-letter country code."""
        return self.fin_id_obj.country

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
            if current.schedule_group.lower() == schedule_group:
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
            if current.match_season(some_date):
                yield current

    def _filter_weekdays(
        self, some_date: dt.date, schedules: Iterable[Schedule]
    ) -> Iterable[Schedule]:
        for current in schedules:
            if current.days_obj.matches(some_date):
                yield current

    def _build_keyed_holidays(
        self, start: StrOrDate, end: StrOrDate
    ) -> dict[dt.date, "MarketHoliday"]:

        holidays = self.list_holidays(start, end)
        keyed = {}
        for current in holidays:
            keyed[current.date] = current
        return keyed

    def generate_phases(
        self, start: StrOrDate, end: StrOrDate
    ) -> Generator[Phase, None, None]:
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        catalog = self.get_catalog(catalog)
        phase_types_dict = PhaseType.as_dict()
        # pprint(phase_types_dict)

        # Get required global data
        offset_start = start - dt.timedelta(days=MAX_OFFSET_DAYS)
        all_schedules = self.list_schedules()
        holidays = self._build_keyed_holidays(offset_start, end)

        # Iterate through all dates generating phases
        current_date = offset_start
        while current_date <= end:
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
            found_schedules = list(self._filter_weekdays(current_date, before_weekdays))

            # Consider fallback if needed
            if not found_schedules and fallback:
                initial_weekday = current_date.weekday()
                fallback_weekday = 6 if initial_weekday == 0 else initial_weekday - 1
                fallback_schedules = []
                while not fallback_schedules and fallback_weekday != initial_weekday:
                    fallback_schedules = list(
                        filter(
                            lambda s: s.days_obj.matches(fallback_weekday),
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
                    start_datetime = dt.datetime.combine(
                        start_date, current_schedule.start
                    )
                    end_datetime = dt.datetime.combine(
                        end_date, current_schedule.end
                    )
                    # start_datetime = current_schedule.timezone_obj.localize(start_datetime)
                    # end_datetime = current_schedule.timezone_obj.localize(end_datetime)
                    start_datetime = start_datetime.replace(tzinfo=current_schedule.timezone_obj)
                    end_datetime = end_datetime.replace(tzinfo=current_schedule.timezone_obj)

                    phase_type = phase_types_dict[current_schedule.phase_type]
                    yield Phase(
                        dict(
                            phase_type=current_schedule.phase_type,
                            phase_name=current_schedule.phase_name,
                            phase_memo=current_schedule.phase_memo,
                            status=phase_type.status,
                            settlement=phase_type.settlement,
                            start=start_datetime.isoformat(),
                            end=end_datetime.isoformat(),
                        )
                    )

            # Next date, please
            current_date += dt.timedelta(days=1)

    @classmethod
    def list_all(cls) -> list["Market"]:
        return [cls(r) for r in db.query(cls.table)]


    def list_holidays(
        self, start: StrOrDate, end: StrOrDate
    ) -> list["MarketHoliday"]:
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        table = MarketHoliday.table
        result = db.query(table).filter(
            table.c["fin_id"] == self.fin_id,
            table.c["date"] >= start.isoformat(),
            table.c["date"] <= end.isoformat()
        )
        return [MarketHoliday(r) for r in result]

    def list_schedules(self) -> list["Schedule"]:
        schedules = db.query(Schedule.table).filter(
            Schedule.table.c["fin_id"] == self.fin_id
        ).order_by(
            Schedule.table.c["schedule_group"].asc().nullsfirst(),
            Schedule.table.c["in_force_start_date"].asc().nullsfirst(),
            Schedule.table.c["season_start"].asc().nullsfirst(),
            Schedule.table.c["start"].asc(),
            Schedule.table.c["end"].asc()
        )
        return [Schedule(r) for r in schedules]

    @classmethod
    def get_by_finid(cls, finid: str, follow=True) -> Union[None, "Market"]:
        finid = validate_finid_arg("finid", finid)
        found = db.query(cls.table).filter(
            cls.table.c["fin_id"] == finid
        ).one_or_none()

        if found and found.replaced_by and follow:
            found = db.query(cls.table).filter(
                cls.table.c["fin_id"] == found.replaced_by
            ).one_or_none()

        if found:
            return cls(found)

    @classmethod
    def get_by_mic(cls, mic: str, follow=True) -> Union[None, "Market"]:
        mic = validate_str_arg("mic", mic)
        mapping = db.query(MicMapping.table).filter(
            MicMapping.table.c["mic"] == mic
        ).one_or_none()
        if mapping:
            return cls.get_by_finid(mapping.fin_id, follow=follow)
        return None

    @classmethod
    def get(cls, identifier: str, follow=True) -> Union[None, "Market"]:
        identifier = validate_str_arg("identifier", identifier)
        if "." in identifier:
            found = cls.get_by_finid(identifier, follow=follow)
        else:
            found = cls.get_by_mic(identifier, follow=follow)
        return found
