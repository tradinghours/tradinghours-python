import pytz
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta


def pmake_timezone_obj(tz):
    return pytz.timezone(tz)

def pconvert_to_timezone(naive_dt, timezone_str):
    tz_obj = pmake_timezone_obj(timezone_str)
    return tz_obj.localize(naive_dt)


def zmake_timezone_obj(tz):
    return ZoneInfo(tz)

def zconvert_to_timezone(naive_dt, timezone_str):
    tz_obj = zmake_timezone_obj(timezone_str)
    return naive_dt.replace(tzinfo=tz_obj)

ny = zmake_timezone_obj("America/New_York")

dst_start = datetime(2022, 3, 13, 1, 59)
zconverted = zconvert_to_timezone(dst_start, "America/New_York")
print(zconverted, zconverted.tzname())
zconverted_add = zconverted + timedelta(hours=1)
print(zconverted_add, zconverted_add.tzname())
print(zconverted_add.astimezone(ny), zconverted_add.tzname())

print()
dst_start = datetime(2022, 3, 13, 2)
zconverted = zconvert_to_timezone(dst_start, "America/New_York")
print(zconverted, zconverted.tzname())
zconverted_add = zconverted + timedelta(hours=1)
print(zconverted_add, zconverted_add.tzname())
print(zconverted_add.astimezone(ny), zconverted_add.tzname())

print()
dst_start = datetime(2022, 3, 13, 2, 1)
zconverted = zconvert_to_timezone(dst_start, "America/New_York")
print(zconverted, zconverted.tzname())
zconverted_add = zconverted + timedelta(hours=1)
print(zconverted_add, zconverted_add.tzname())
print(zconverted_add.astimezone(ny), zconverted_add.tzname())

print()
dst_start = datetime(2022, 3, 14, 2, 1)
zconverted = zconvert_to_timezone(dst_start, "America/New_York")
print(zconverted, zconverted.tzname())
zconverted_add = zconverted + timedelta(hours=1)
print(zconverted_add, zconverted_add.tzname())
print(zconverted_add.astimezone(ny), zconverted_add.tzname())

exit()
print()
pconverted = pconvert_to_timezone(dst_start, "America/New_York")
print(pconverted, pconverted.tzname())
pconverted_add = pconverted + timedelta(hours=1)
print(pconverted_add, pconverted_add.tzname())



print()
print()
from datetime import datetime

# Create a datetime object representing the DST to standard time transition
# Here, we're creating a datetime that falls within the overlap period (1:30 AM)
dt_overlap = datetime(2022, 11, 6, 1, 30)

# Specify which occurrence of the datetime you want to work with using the fold parameter
# fold=0 represents the first occurrence (before the clock is set back)
# fold=1 represents the second occurrence (after the clock is set back)
dt_fold_0 = datetime(2022, 3, 13, 2, 1, fold=0, tzinfo=zmake_timezone_obj("America/New_York"))
dt_fold_1 = datetime(2022, 3, 13, 2, 1, fold=1, tzinfo=zmake_timezone_obj("America/New_York"))

# Print the datetimes and their fold values
print("Datetime with fold=0:", dt_fold_0, "Fold:", dt_fold_0.fold)
print("Datetime with fold=1:", dt_fold_1, "Fold:", dt_fold_1.fold)


