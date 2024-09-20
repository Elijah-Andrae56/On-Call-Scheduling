"""Elijah Andrae Summer 2024"""


import datetime as dt
from ortools.sat.python import cp_model
import random

# First, define the Date and DateManager
class Date:
    def __init__(self, date, day_number, is_weekend):
        self.date = date
        self.day_number = day_number
        self.is_weekend = is_weekend

    def __str__(self):
        return f"{self.date}, {self.day_number}, {self.is_weekend}"

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
            days.append(Date(current_date, day_number, is_weekend))
        return days

    def count_days(self):
        num_weekend_days = sum(1 for day in self.days if day.is_weekend)
        num_week_days = len(self.days) - num_weekend_days
        return (num_weekend_days, num_week_days)

# Initialize the DateManager with your desired date range
start_date = dt.datetime(2024, 9, 23)
end_date = dt.datetime(2024, 12, 13)
time_range = DateManager(start_date, end_date)

# Now, proceed with the scheduling code from your second file

# List of RAs
ras = ['RA1', 'RA2', 'RA3', 'RA4', 'RA5', 'RA6', 'RA7', 'RA8',
       'RA9', 'RA10', 'RA11', 'RA12', 'RA13', 'RA14', 'RA15', 'RA16']

num_ras = len(ras)

# Number of days from DateManager
num_days = len(time_range.days)

# Build the weekend list from DateManager
weekend = [1 if day.is_weekend else 0 for day in time_range.days]

# Each day has two roles: primary (0) and secondary (1)
roles = [0, 1]  # 0: Primary, 1: Secondary

# Constants for preferred and unavailable shifts
NUMBER_PREFERRED_SHIFTS = 15
NUMBER_UNAVAILABLE_SHIFTS = 30

# Initialize dictionaries to hold preferences and unavailabilities
preferences = {}     # preferences[ra] = set of preferred days
unavailabilities = {}  # unavailabilities[ra] = set of days

for ra in ras:
    # Randomly select preferred weekdays (up to the number available)
    weekday_indices = [i for i in range(num_days) if weekend[i] == 0]
    preferred_weekdays = random.sample(
        weekday_indices, min(NUMBER_PREFERRED_SHIFTS, len(weekday_indices)))
    preferences[ra] = set(preferred_weekdays)
    # Randomly select unavailable days (up to the number available)
    unavailable_days = random.sample(
        range(num_days), random.randint(0, min(NUMBER_UNAVAILABLE_SHIFTS, num_days)))
    unavailabilities[ra] = set(unavailable_days)

# Create the model
model = cp_model.CpModel()

# Define variables
x = {}
for ra_index, ra in enumerate(ras):
    x[ra_index] = {}
    for day in range(num_days):
        x[ra_index][day] = {}
        for role in roles:
            x[ra_index][day][role] = model.NewBoolVar(f'x_{ra}_{day}_{role}')

# Constraint 1: Each shift must have exactly one RA assigned
for day in range(num_days):
    for role in roles:
        model.Add(sum(x[ra_index][day][role] for ra_index in range(num_ras)) == 1)

# Constraint 2: RAs cannot be assigned on days they are unavailable
for ra_index, ra in enumerate(ras):
    for day in unavailabilities[ra]:
        for role in roles:
            model.Add(x[ra_index][day][role] == 0)

# Compute total weekend and weekday shifts
total_weekend_shifts = weekend.count(1) * len(roles)
total_weekday_shifts = weekend.count(0) * len(roles)

# Compute per-RA shift counts
per_ra_weekend_shifts = total_weekend_shifts // num_ras
per_ra_weekday_shifts = total_weekday_shifts // num_ras

# Constraints for weekend shifts per RA
for ra_index, ra in enumerate(ras):
    num_weekend_shifts = sum(
        x[ra_index][day][role]
        for day in range(num_days)
        for role in roles
        if weekend[day] == 1
    )
    model.Add(num_weekend_shifts >= per_ra_weekend_shifts)
    model.Add(num_weekend_shifts <= per_ra_weekend_shifts + 1)

# Constraints for weekday shifts per RA
for ra_index, ra in enumerate(ras):
    num_weekday_shifts = sum(
        x[ra_index][day][role]
        for day in range(num_days)
        for role in roles
        if weekend[day] == 0
    )
    model.Add(num_weekday_shifts >= per_ra_weekday_shifts)
    model.Add(num_weekday_shifts <= per_ra_weekday_shifts + 1)

# Constraint 5: Balance primary and secondary shifts for each RA
for ra_index, ra in enumerate(ras):
    num_primary = sum(
        x[ra_index][day][0]  # role 0 is primary
        for day in range(num_days)
    )
    num_secondary = sum(
        x[ra_index][day][1]  # role 1 is secondary
        for day in range(num_days)
    )
    # The difference between primary and secondary shifts should be at most 1
    model.AddAbsEquality(model.NewIntVar(0, num_days, ''), num_primary - num_secondary)
    model.Add(num_primary - num_secondary <= 1)
    model.Add(num_primary - num_secondary >= -1)

# Constraint 6: Ensure the primary and secondary RA is not the same person on any given day
for day in range(num_days):
    for ra_index in range(num_ras):
        model.Add(x[ra_index][day][0] + x[ra_index][day][1] <= 1)

# Constraint 7: Ensure no RA works more than 3 consecutive days
for ra_index, ra in enumerate(ras):
    for start_day in range(num_days - 3):
        total_shifts = sum(
            x[ra_index][day][role]
            for day in range(start_day, start_day + 4)
            for role in roles
        )
        model.Add(total_shifts <= 3)

# Define the objective function
total_preferences = []
for ra_index, ra in enumerate(ras):
    for day in range(num_days):
        for role in roles:
            if day in preferences[ra] and weekend[day] == 0:
                total_preferences.append(x[ra_index][day][role])

model.Maximize(sum(total_preferences))

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Output the results
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print('Solution found:')
    schedule = {}
    for day in range(num_days):
        schedule[day] = {}
        for role in roles:
            for ra_index, ra in enumerate(ras):
                if solver.Value(x[ra_index][day][role]) == 1:
                    schedule[day][role] = ra
                    break
    # Print the schedule with actual dates
    for day in range(num_days):
        date_info = time_range.days[day]
        day_type = 'Weekend' if date_info.is_weekend else 'Weekday'
        date_str = date_info.date.strftime('%Y-%m-%d')
        print(f'Day {day} ({date_str}, {day_type}):')
        print(f"  Primary RA: {schedule[day][0]}")
        print(f"  Secondary RA: {schedule[day][1]}")
else:
    print('No feasible solution found.')

