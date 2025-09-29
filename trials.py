import tradinghours as th
import datetime as dt


market = th.Market.get("AE.ADX")
schedules = market.list_schedules()
print(len(schedules))
for schedule in schedules:
    print(schedule.to_dict(), end=",\n")
    # print(schedule)