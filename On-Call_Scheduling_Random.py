"""Elijah Andrae Summer 2024"""

from dataclasses import dataclass
import datetime as dt
from ortools.sat.python import cp_model
import random

# First, define the Date and DateManager

@dataclass
class Date:
    date: dt.datetime
    day_number: int
    is_weekend: bool

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
    
class Scheduler:
    def __init__(self, ras, time_range):
        self.ras = ras
        self.time_range = time_range
        self.num_ras = len(ras)
        self.num_days = len(time_range.days)
        self.weekend = [1 if day.is_weekend else 0 for day in time_range.days]
        self.roles = [0, 1]  # 0: Primary, 1: Secondary
        self.model = cp_model.CpModel()
        self.x = {}

    def generate_preferences(self):
        # Constants for preferred shifts
        NUMBER_PREFERRED_SHIFTS = 15

        # Initialize dictionary to hold preferences
        self.preferences = {}  # preferences[ra] = set of preferred days

        for ra in self.ras:
            # Randomly select preferred weekdays (up to the number available)
            weekday_indices = [i for i in range(self.num_days) if self.weekend[i] == 0]
            preferred_weekdays = random.sample(
                weekday_indices, min(NUMBER_PREFERRED_SHIFTS, len(weekday_indices)))
            self.preferences[ra] = set(preferred_weekdays)

    def generate_unavailabilities(self):
        # Constants for unavailable shifts
        NUMBER_UNAVAILABLE_SHIFTS = 30

        # Initialize dictionary to hold unavailabilities
        self.unavailabilities = {}  # unavailabilities[ra] = set of days

        for ra in self.ras:
            # Randomly select unavailable days (up to the number available)
            unavailable_days = random.sample(
                range(self.num_days), random.randint(0, min(NUMBER_UNAVAILABLE_SHIFTS, self.num_days)))
            self.unavailabilities[ra] = set(unavailable_days)

    def build_model(self):
        # Define variables
        for ra_index, ra in enumerate(self.ras):
            self.x[ra_index] = {}
            for day in range(self.num_days):
                self.x[ra_index][day] = {}
                for role in self.roles:
                    self.x[ra_index][day][role] = self.model.NewBoolVar(f'x_{ra}_{day}_{role}')

    def add_constraints(self):
        # Constraint 1: Each shift must have exactly one RA assigned
        for day in range(self.num_days):
            for role in self.roles:
                self.model.Add(sum(self.x[ra_index][day][role] for ra_index in range(self.num_ras)) == 1)

        # Constraint 2: RAs cannot be assigned on days they are unavailable
        for ra_index, ra in enumerate(self.ras):
            for day in self.unavailabilities[ra]:
                for role in self.roles:
                    self.model.Add(self.x[ra_index][day][role] == 0)

        # Compute total weekend and weekday shifts
        total_weekend_shifts = self.weekend.count(1) * len(self.roles)
        total_weekday_shifts = self.weekend.count(0) * len(self.roles)

        # Compute per-RA shift counts
        per_ra_weekend_shifts = total_weekend_shifts // self.num_ras
        per_ra_weekday_shifts = total_weekday_shifts // self.num_ras

        # Constraints for weekend shifts per RA
        for ra_index, ra in enumerate(self.ras):
            num_weekend_shifts = sum(
                self.x[ra_index][day][role]
                for day in range(self.num_days)
                for role in self.roles
                if self.weekend[day] == 1
            )
            self.model.Add(num_weekend_shifts >= per_ra_weekend_shifts)
            self.model.Add(num_weekend_shifts <= per_ra_weekend_shifts + 1)

        # Constraints for weekday shifts per RA
        for ra_index, ra in enumerate(self.ras):
            num_weekday_shifts = sum(
                self.x[ra_index][day][role]
                for day in range(self.num_days)
                for role in self.roles
                if self.weekend[day] == 0
            )
            self.model.Add(num_weekday_shifts >= per_ra_weekday_shifts)
            self.model.Add(num_weekday_shifts <= per_ra_weekday_shifts + 1)

        # Constraint 5: Balance primary and secondary shifts for each RA
        for ra_index, ra in enumerate(self.ras):
            num_primary = sum(
                self.x[ra_index][day][0]  # role 0 is primary
                for day in range(self.num_days)
            )
            num_secondary = sum(
                self.x[ra_index][day][1]  # role 1 is secondary
                for day in range(self.num_days)
            )
            # The difference between primary and secondary shifts should be at most 1
            diff = self.model.NewIntVar(-self.num_days, self.num_days, f'diff_{ra}')
            self.model.Add(diff == num_primary - num_secondary)
            self.model.Add(diff >= -1)
            self.model.Add(diff <= 1)

        # Constraint 6: Ensure the primary and secondary RA is not the same person on any given day
        for day in range(self.num_days):
            for ra_index in range(self.num_ras):
                self.model.Add(self.x[ra_index][day][0] + self.x[ra_index][day][1] <= 1)

        # Constraint 7: Ensure no RA works more than 3 consecutive days
        for ra_index, ra in enumerate(self.ras):
            for start_day in range(self.num_days - 3):
                total_shifts = sum(
                    self.x[ra_index][day][role]
                    for day in range(start_day, start_day + 4)
                    for role in self.roles
                )
                self.model.Add(total_shifts <= 3)

    def define_objective(self):
        total_preferences = []
        for ra_index, ra in enumerate(self.ras):
            for day in range(self.num_days):
                for role in self.roles:
                    if day in self.preferences[ra] and self.weekend[day] == 0:
                        total_preferences.append(self.x[ra_index][day][role])
        self.model.Maximize(sum(total_preferences))

    def solve(self):
        # Create a solver and solve the model
        self.solver = cp_model.CpSolver()
        self.status = self.solver.Solve(self.model)

    def print_schedule(self):
        # Output the results
        if self.status == cp_model.OPTIMAL or self.status == cp_model.FEASIBLE:
            print('Solution found:')
            schedule = {}
            for day in range(self.num_days):
                schedule[day] = {}
                for role in self.roles:
                    for ra_index, ra in enumerate(self.ras):
                        if self.solver.Value(self.x[ra_index][day][role]) == 1:
                            schedule[day][role] = ra
                            break

            # Print the schedule with actual dates
            for day in range(self.num_days):
                date_info = self.time_range.days[day]
                day_type = 'Weekend' if date_info.is_weekend else 'Weekday'
                date_str = date_info.date.strftime('%Y-%m-%d')
                print(f'Day {day} ({date_str}, {day_type}):')
                print(f"  Primary RA: {schedule[day][0]}")
                print(f"  Secondary RA: {schedule[day][1]}")
        else:
            print('No feasible solution found.')

# Usage
if __name__ == "__main__":
    start_date = dt.datetime(2024, 9, 30)
    end_date = dt.datetime(2024, 12, 13)
    time_range = DateManager(start_date, end_date)
    ras = ["Andrew", "Callie", "Daria", "Erin", "Esperanza", "Hallie", 
       "Jemima", "Joseph", "Kai", "Kalina", "Mason", "Sam", "Eli"]

    scheduler = Scheduler(ras, time_range)
    
    scheduler.generate_preferences()
    scheduler.generate_unavailabilities()

    scheduler.build_model()
    scheduler.add_constraints()
    scheduler.define_objective()
    scheduler.solve()
    scheduler.print_schedule()
