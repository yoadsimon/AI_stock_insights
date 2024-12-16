from datetime import datetime, timedelta, time

from common.utils.consts import MARKET_TIME_ZONE

MARKET_OPEN_TIME = time(9, 30)  # Market opens at 9:30 AM
MARKET_CLOSE_TIME = time(16, 0)  # Market closes at 4:00 PM
OPEN_DAYS = [0, 1, 2, 3, 4]  # Monday to Friday


class StockMarketTime:
    def __init__(self, now=None):
        if now:
            self.now = now.astimezone(MARKET_TIME_ZONE)
            self.is_mock = True
        else:
            self.now = datetime.now(MARKET_TIME_ZONE)
            self.is_mock = False
        self.is_market_open = self.is_market_currently_open()
        self.last_time_open = self.get_last_market_open_datetime()
        self.next_time_open = self.get_next_market_open_datetime()
        self.last_time_close = self.get_last_market_close_datetime()
        self.next_time_close = self.get_next_market_close_datetime()

    def is_market_currently_open(self):
        now_time = self.now.time()
        now_weekday = self.now.weekday()
        return (
                now_weekday in OPEN_DAYS and
                MARKET_OPEN_TIME <= now_time < MARKET_CLOSE_TIME
        )

    def get_previous_business_day(self, date):
        date -= timedelta(days=1)
        while date.weekday() not in OPEN_DAYS:
            date -= timedelta(days=1)
        return date

    def get_next_business_day(self, date):
        date += timedelta(days=1)
        while date.weekday() not in OPEN_DAYS:
            date += timedelta(days=1)
        return date

    def get_last_market_open_datetime(self):
        date = self.now
        while True:
            if date.weekday() in OPEN_DAYS:
                naive_open_time = datetime.combine(date.date(), MARKET_OPEN_TIME)
                open_time = MARKET_TIME_ZONE.localize(naive_open_time)
                if open_time <= self.now:
                    return open_time
            date -= timedelta(days=1)

    def get_next_market_open_datetime(self):
        date = self.now
        while True:
            if date.weekday() in OPEN_DAYS:
                naive_open_time = datetime.combine(date.date(), MARKET_OPEN_TIME)
                open_time = MARKET_TIME_ZONE.localize(naive_open_time)
                if open_time > self.now:
                    return open_time
            date += timedelta(days=1)

    def get_last_market_close_datetime(self):
        date = self.now
        while True:
            if date.weekday() in OPEN_DAYS:
                naive_close_time = datetime.combine(date.date(), MARKET_CLOSE_TIME)
                close_time = MARKET_TIME_ZONE.localize(naive_close_time)
                if close_time <= self.now:
                    return close_time
            date -= timedelta(days=1)

    def get_next_market_close_datetime(self):
        date = self.now
        while True:
            if date.weekday() in OPEN_DAYS:
                naive_close_time = datetime.combine(date.date(), MARKET_CLOSE_TIME)
                close_time = MARKET_TIME_ZONE.localize(naive_close_time)
                if close_time > self.now:
                    if self.is_market_open:
                        return close_time
                    elif close_time.time() >= self.now.time():
                        return close_time
                elif self.is_market_currently_open():
                    today_close_time = MARKET_TIME_ZONE.localize(
                        datetime.combine(self.now.date(), MARKET_CLOSE_TIME)
                    )
                    return today_close_time
            date += timedelta(days=1)

    def time_until_next_open(self):
        if self.is_market_open:
            return timedelta(0)
        else:
            return self.next_time_open - self.now

    def time_until_next_close(self):
        if self.is_market_open:
            return self.next_time_close - self.now
        else:
            return timedelta(0)

    def __str__(self):
        if self.is_market_open:
            delta = self.time_until_next_close()
            status = "OPEN"
            next_action = "close"
        else:
            delta = self.time_until_next_open()
            status = "CLOSED"
            next_action = "open"
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        return f"Market is {status}. It will {next_action} in {hours} hours and {minutes} minutes."


def format_time_difference(delta):
    total_seconds = delta.total_seconds()
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return int(hours), int(minutes)
