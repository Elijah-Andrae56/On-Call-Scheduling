"""Elijah Andrae, Joseph Erlinger; Summer, Fall 2024"""

from dataclasses import dataclass
import datetime as dt
from ortools.sat.python import cp_model
import pandas as pd
import numpy as np

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
        """
        @brief: The load_data method uses the Pandas library to read a CSV file
        and create a dataframe table with the following columns: Timestamp,
        Name, 95#, Availability Week [1,11], and Unavailability Week [1,11].

        @params:
        1. file_path <str>: path/to/file.csv

        @return:
        1. self.data <dataframe>: table containing the data from the csv file.
        2. self.ras <list>: array representation of the 'Name' column.
        3. self.num_ras <int>: length of self.ras
        4. self.ra_to_index <dict>: mapping from RA name to index in self.ras.

        @note: The input csv does not need to have column names that match the
        output dataframe table. That said, the content of the input csv must
        match the output dataframe table.
        """
        # Read csv using Pandas
        df = pd.read_csv(file_path)

        # The first three columns are defined.
        OFFSET = 3

        # The next N columns are dynamically defined.
        num_weeks = (len(df.columns) - OFFSET) // 2

        # Enforce naming on the dataframe's columns.
        df = df.rename(columns={
            **{
            df.columns[0]: "Timestamp",
            df.columns[1]: 'Name', 
            df.columns[2]: '95#'},
            **{
            df.columns[i+OFFSET]: f"Availability Week {i+1}"
            for i in range(num_weeks)
            },
            **{
            df.columns[i+OFFSET+num_weeks]: f"Unavailability Week {i+1}" 
            for i in range(num_weeks)
            },
        })

        # Convert 'Google Form' timestamps (ts) to Pandas datatimes.
        ts_series = df['Timestamp'].str[:-4]
        ts_format = r"%Y/%m/%d %I:%M:%S %p"
        df['Timestamp'] = pd.to_datetime(ts_series, format=ts_format)

        # Sort Dataframe by ascending 95# and descending timestamp.
        df = df.sort_values(by=['95#', 'Timestamp'], ascending=[True, False])

        # Keep only the most-recent entry for each 95#.
        df = df.drop_duplicates(subset='95#', keep='first')

        # Build the availability matrix from the data in the dataframe.
        self.establish_availability_matrix(df)
       

    def establish_availability_matrix(self, dataframe):
        """Build the availability matrix from the data in the dataframe."""
        self.data = dataframe
        self.ras = self.data['Name'].tolist()
        self.num_ras = len(self.ras)
        self.ra_to_index = {ra_name: index for index, ra_name in enumerate(self.ras)}

    def parse_data(self):
        # Initialize dictionaries
        self.preferences = {ra_index: set() for ra_index in range(self.num_ras)}
        self.unavailabilities = {ra_index: set() for ra_index in range(self.num_ras)}
        
        # Map day names to numbers
        day_name_to_number = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Wednsday': 2,
            'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
        }
        
        # Build week to date indices mapping
        week_to_date_indices = {}
        for i, date in enumerate(self.time_range.days):
            week_to_date_indices.setdefault(date.week_number, []).append(i)
        
        # Iterate over RAs
        for _, row in self.data.iterrows():
            ra_name = row['Name']
            ra_index = self.ra_to_index[ra_name]  # Correctly get the RA index
            for week in week_to_date_indices:
                for col_prefix, attr in [('Availability', self.preferences), ('Unavailability', self.unavailabilities)]:
                    column = f'{col_prefix} Week {week}'
                    if column in row and pd.notna(row[column]):
                        days = [day.strip().capitalize() for day in row[column].split(';')]
                        day_numbers = [day_name_to_number.get(day) for day in days if day]
                        days_set = set(filter(None, day_numbers))
                        date_indices = week_to_date_indices[week]
                        matching_days = {i for i in date_indices if self.time_range.days[i].day_number in days_set}
                        attr[ra_index].update(matching_days)

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

    def run(self):
        """Quickly build the model, add the constraints, 
            define the objective, and solve the schedule"""
        self.build_model()
        self.add_constraints()
        self.define_objective()
        self.solve()

    def return_schedule(self):
        """Returns the schedule in a DataFrame format, returns with columns
           'Day Number', 'Date', 'Primary RA', 'Secondary RA'"""
        
        if self.status == cp_model.OPTIMAL or self.status == cp_model.FEASIBLE:
            schedule_df = pd.DataFrame()
            day_numbers = []
            week_numbers = []
            primary_ras = []
            secondary_ras = []
            dates = []

            for day in range(self.num_days):
                date_info = self.time_range.days[day]
                day_numbers.append("Day " + str(day))
                week_numbers.append("Week " + str(date_info.week_number))
                dates.append(date_info.date.strftime('%Y-%m-%d'))

                for role in self.roles:
                    assigned_ra = "Unassigned"
                    for ra_index, ra in enumerate(self.ras):
                        if self.solver.Value(self.x[ra_index][day][role]) == 1:
                            assigned_ra = ra
                            break
                    if role == 0:  # Primary
                        primary_ras.append(assigned_ra)
                    else:  # Secondary
                        secondary_ras.append(assigned_ra)
     
            schedule_df['Day Number'] = day_numbers
            schedule_df['Week Number'] = week_numbers
            schedule_df['Date'] = dates
            schedule_df['Primary RA'] = primary_ras
            schedule_df['Secondary RA'] = secondary_ras
            return schedule_df
        else:
            print('No feasible solution found.')
            return pd.DataFrame()  # Return an empty DataFrame if no solution
