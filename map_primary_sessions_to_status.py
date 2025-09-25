import datetime as dt
from zoneinfo import ZoneInfo
import tradinghours as th
from pprint import pprint

sample_markets = [
    "CHIA", "CXAW", "XBAH", "XWBO", "XCSX", "NGXC", "AU.ASX.INTERESTRATE.3YEARSBOND.FUT", "US.CME.CRYPTOBTIC.LON"
]

print("================================================")
print(f"All Possible Phases:\n")
for phase_type, phase_type_obj in th.models.PhaseType.as_dict().items():
    phase_type_obj.pprint()
print("================================================\n")


def get_phases_on(market: th.Market, date, only_primary_trading_sessions=False, convert_to_timezone=None):
    """
    This function gathers all phases that are active at any point on the given date.
    To keep only primary trading sessions, you can filter out by the is_open property.
    """
    phases = []
    for phase in market.generate_phases(date, date):
        # only primary trading sessions are ``is_open``
        if not only_primary_trading_sessions or phase.is_open: 
            if convert_to_timezone:
                phase.start = phase.start.astimezone(ZoneInfo(convert_to_timezone))
                phase.end = phase.end.astimezone(ZoneInfo(convert_to_timezone))

            phases.append(phase)
    return phases



# dtime = dt.datetime.now(dt.timezone.utc)
dtime = dt.datetime(2025, 9, 27, 21, 30, tzinfo=ZoneInfo("UTC")) # weekend
dtime = dt.datetime(2025, 9, 25, 21, 30, tzinfo=ZoneInfo("UTC"))
print(f"---> Using datetime: {dtime}\n")

# sample_markets = ["US.CME.CRYPTOBTIC.LON"]
for market in sample_markets:
    market = th.Market.get(market)
    print(market)

    status = market.status(dtime)
    if status.status != "Open":
        print("  > Closed")
        primary_trading_sessions = get_phases_on(
            market, 
            dtime.date(),
            only_primary_trading_sessions=True,
            convert_to_timezone="UTC"
        )
        if not primary_trading_sessions:
            print("   > No primary trading sessions")
        else:
            for phase in primary_trading_sessions:
                print(f"   > Primary Session: {phase.start} - {phase.end}")

    else:
        print("  > Open")



   


