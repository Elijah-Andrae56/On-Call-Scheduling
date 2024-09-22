
"""Elijah Andrae Summer 2024"""

from dataclasses import dataclass
import datetime as dt
from ortools.sat.python import cp_model
import pandas as pd

# Define the Date and DateManager classes

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
        
class Scheduler:
    def __init__(self, time_range):
        self.ras = []
        self.time_range = time_range
        self.num_ras = len(self.ras)
        self.num_days = len(time_range.days)
        self.weekend = [1 if day.is_weekend else 0 for day in time_range.days]
        self.roles = [0, 1]  # 0: Primary, 1: Secondary
        self.model = cp_model.CpModel()
        self.x = {}
        self.data = None  # Placeholder for the data from the form

    def load_data(self, file_path):
        # Read the CSV file
        df = pd.read_csv(file_path)

        # Rename columns if necessary
        if df.columns[1] != 'Name':
            df = df.rename(columns={df.columns[1]: 'Name', df.columns[2]: '95#'})

        # Check if the availability columns are already correctly named
        if not any(col.startswith('Availability Week') for col in df.columns):
            # Rename Availability and Unavailability columns
            week = 1
            start = 3  # Adjust based on your actual CSV structure
            total_columns = len(df.columns)
            num_weeks = (total_columns - start) // 2

            for i in range(num_weeks):
                avail_col = start + i
                unavail_col = start + num_weeks + i
                df = df.rename(columns={df.columns[avail_col]: f'Availability Week {week}'})
                df = df.rename(columns={df.columns[unavail_col]: f'Unavailability Week {week}'})
                week += 1

        # Process Timestamp
        df['Timestamp'] = pd.to_datetime(df['Timestamp'].str[:-4], format='%Y/%m/%d %I:%M:%S %p')
        df = df.sort_values(by=['95#', 'Timestamp'], ascending=[True, False])
        df = df.drop_duplicates(subset='95#', keep='first')

        self.data = df

        # Populate the list of RAs
        self.ras = self.data['Name'].tolist()
        self.num_ras = len(self.ras)
        # Create a mapping from RA names to indices
        self.ra_to_index = {ra_name: index for index, ra_name in enumerate(self.ras)}

    def parse_data(self):
        # Initialize preferences and unavailabilities dictionaries
        self.preferences = {}
        self.unavailabilities = {}

        # Map day names to day numbers
        day_name_to_number = {
            'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Wednsday': 2,  # Handle common misspelling
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6
        }

        # Build a mapping from week numbers to date indices
        week_to_date_indices = {}
        for i, date in enumerate(self.time_range.days):
            week_number = date.week_number
            if week_number not in week_to_date_indices:
                week_to_date_indices[week_number] = []
            week_to_date_indices[week_number].append(i)

        # Iterate over each RA's response
        for index, row in self.data.iterrows():
            ra_name = row['Name']
            ra_index = self.ra_to_index[ra_name]

            # Initialize sets for preferred and unavailable days
            preferred_days = set()
            unavailable_days = set()

            # Parse availability
            for week in range(1, max(week_to_date_indices.keys()) + 1):
                availability_column = f'Availability Week {week}'
                if availability_column in row and pd.notna(row[availability_column]):
                    days = row[availability_column].split(';')
                    days = [day.strip() for day in days]
                    for day in days:
                        day_clean = day.strip().capitalize()
                        day_number = day_name_to_number.get(day_clean)
                        if day_number is not None:
                            date_indices = week_to_date_indices.get(week, [])
                            for i in date_indices:
                                if self.time_range.days[i].day_number == day_number:
                                    preferred_days.add(i)

            # Parse unavailability
            for week in range(1, max(week_to_date_indices.keys()) + 1):
                unavailability_column = f'Unavailability Week {week}'
                if unavailability_column in row and pd.notna(row[unavailability_column]):
                    days = row[unavailability_column].split(';')
                    days = [day.strip() for day in days]
                    for day in days:
                        day_clean = day.strip().capitalize()
                        day_number = day_name_to_number.get(day_clean)
                        if day_number is not None:
                            date_indices = week_to_date_indices.get(week, [])
                            for i in date_indices:
                                if self.time_range.days[i].day_number == day_number:
                                    unavailable_days.add(i)

            # Update preferences and unavailabilities
            self.preferences[ra_index] = preferred_days
            self.unavailabilities[ra_index] = unavailable_days

        # Optional: Print preferences and unavailabilities for verification
        print("Preferences:")
        for ra_index, days in self.preferences.items():
            print(f"{self.ras[ra_index]}: {sorted(days)}")

        print("\nUnavailabilities:")
        for ra_index, days in self.unavailabilities.items():
            print(f"{self.ras[ra_index]}: {sorted(days)}")

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
            for day in self.unavailabilities.get(ra_index, set()):
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
        # Maximize the number of preferred shifts assigned
        total_preferences = []
        for ra_index, ra in enumerate(self.ras):
            for day in range(self.num_days):
                for role in self.roles:
                    if day in self.preferences.get(ra_index, set()):
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
                print(f'Day {day} ({date_str}, {day_type}, Week {date_info.week_number}):')
                print(f"  Primary RA: {schedule[day].get(0, 'Unassigned')}")
                print(f"  Secondary RA: {schedule[day].get(1, 'Unassigned')}")
        else:
            print('No feasible solution found.')

if __name__ == "__main__":
    start_date = dt.datetime(2024, 9, 29)  # Enter the date of Sunday Week 1
    end_date = dt.datetime(2024, 12, 13)   # Enter the date of Friday end of Finals Week

    time_range = DateManager(start_date, end_date)
    scheduler = Scheduler(time_range)

    # Path to your CSV file
    file_path = 'Schedule/test_data.csv'

    scheduler.load_data(file_path)
    scheduler.parse_data()

    scheduler.build_model()
    scheduler.add_constraints()
    scheduler.define_objective()
    scheduler.solve()
    scheduler.print_schedule()
