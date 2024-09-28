# Define the Date and DateManager classes
from dataclasses import dataclass
import datetime as dt


@dataclass
class Date:
    date: dt.datetime
    day_number: int
    is_weekend: bool
    week_number: int  # Added week_number

    def __str__(self):
        return f"{self.date}, {self.day_number}, {self.is_weekend}, Week {self.week_number}"

class DateManager:
    def __init__(self, start_date: dt.datetime, end_date: dt.datetime):
        self.days = self.generate_days(start_date, end_date)
        shift_days = self.count_days()
        self.weekend_shift_count = shift_days[0]
        self.weekday_shift_count = shift_days[1]

    def __str__(self):
        return str([str(day) for day in self.days])

    def generate_days(self, start_date, end_date):
        num_days = (end_date - start_date).days + 1
        days = []
        for i in range(num_days):
            current_date = start_date + dt.timedelta(days=i)
            day_number = current_date.weekday()  # 0=Monday, 6=Sunday
            is_weekend = day_number >= 4 and day_number <= 5  # Friday (4) and Saturday (5)
            week_number = ((current_date - start_date).days) // 7 + 1
            days.append(Date(current_date, day_number, is_weekend, week_number))
        return days

    def count_days(self):
        num_weekend_days = sum(1 for day in self.days if day.is_weekend)
        num_week_days = len(self.days) - num_weekend_days
        return (num_weekend_days, num_week_days)