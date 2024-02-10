import asyncio
import time
from datetime import datetime, timedelta
import pytz

def get_utc_plus_7_time():
    # Get the UTC+7 timezone
    utc_plus_7 = pytz.timezone('Asia/Bangkok')
    # Get the current time in UTC+7 timezone
    utc_plus_7_time = datetime.now(utc_plus_7)
    return utc_plus_7_time

async def do_daily():
    print("zzz")

async def daily(do_daily_func):
    while True:
        # Get current UTC+7 datetime
        utc_plus_7_now = get_utc_plus_7_time()

        # Get the current date in UTC+7 timezone
        current_date_utc_plus_7 = datetime(utc_plus_7_now.year, utc_plus_7_now.month, utc_plus_7_now.day, tzinfo=utc_plus_7_now.tzinfo)
        
        # Calculate the next 12:05 AM UTC+7 datetime
        next_run_time = current_date_utc_plus_7 + timedelta(days=1, hours=0, minutes=5)  # 12:05 AM UTC+7 is equivalent to 5:05 PM UTC
        
        # Calculate the time difference between current time and next run time
        time_difference = next_run_time - utc_plus_7_now
        
        # Convert the time difference to seconds
        sleep_seconds = time_difference.total_seconds()

        # Sleep until the next run time
        print("Next daily run in:", next_run_time)
        await asyncio.sleep(sleep_seconds)
        await do_daily_func()

async def main():
    asyncio.create_task(daily(do_daily))
    while True:
        print("5s")
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())