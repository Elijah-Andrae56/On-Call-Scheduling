import datetime as dt
from ortools.sat.python import cp_model
from typing import Union
import pandas as pd
import numpy as np


DAY_TO_INT = {
    "Sunday": 0,
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6
}

        
class Scheduler:
    def __init__(self):
        self.shifts = {}
        self.shift_requests = {}
        self.model = None
        self.num_weeks = 0
        self.num_days = 7
        self.num_ras = 0
        self.all_weeks = None
        self.all_days = None
        self.all_uoids = []
        self.OFFSET = 3

    
    def csv_to_df(self, path_to_csv: str) -> pd.DataFrame:
        # Use Pandas to convert csv to dataframe.
        df = pd.read_csv(path_to_csv)

        # The next N columns are dynamically defined.
        self.num_weeks = (df.shape[1] - self.OFFSET) // 2

        # Enforce naming on the dataframe's columns.
        df = df.rename(columns={
            **{
            df.columns[0]: "Timestamp",
            df.columns[1]: 'Name', 
            df.columns[2]: '95#'},
            **{
            df.columns[i+self.OFFSET]: f"Availability Week {i+1}"
            for i in range(self.num_weeks)
            },
            **{
            df.columns[i+self.OFFSET+self.num_weeks]: f"Unavailability Week {i+1}"
            for i in range(self.num_weeks)
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

        return df
    
    def load_df(self, df: pd.DataFrame) -> None:
        if (df.shape[1] - self.OFFSET) % 2 == 1:
            raise ValueError("dataframe should contain even \
            number of available weeks to unavailable weeks.")
        self.model = cp_model.CpModel()
        self.all_weeks = range(1, self.num_weeks + 1)
        self.all_days = range(7)  # seven days in a week.
        for _, row in df.iterrows():
            uoid = row["95#"]
            self.num_ras += 1
            self.all_uoids.append(uoid)
            for w in self.all_weeks:
                available = row[f"Availability Week {w}"].split(';')
                unavailable = row[f"Unavailability Week {w}"].split(';')
                available = [DAY_TO_INT[d] for d in available]
                unavailable = [DAY_TO_INT[d] for d in unavailable]
                available.sort()
                unavailable.sort()
                ptr1 = 0
                ptr2 = 0
                for d in self.all_days:
                    self.shifts[(uoid, w, d)] = self.model.new_bool_var(f"shift_uoid{uoid}_w{w}_day{d}")
                    if ptr2 < len(unavailable) and unavailable[ptr2] == d:
                        self.shift_requests[(uoid, w, d)] = -1
                        ptr2 += 1
                    elif ptr1 < len(available) and available[ptr1] == d:
                        self.shift_requests[(uoid, w, d)] = 1
                        ptr1 += 1
                    else:
                        self.shift_requests[(uoid, w, d)] = 0
        return None

    def set_constraints(self) -> None:
        # Each shift is assigned to exactly one RA.
        for w in self.all_weeks:
            for d in self.all_days:
                self.model.add_exactly_one(self.shifts[(uoid, w, d)] for uoid in self.all_uoids)


        # Try to distribute the shifts evenly, so that each RA works
        # min_shifts_per_ra shifts. If this is not possible, because the total
        # number of shifts is not divisible by the number of ras, some ras will
        # be assigned one more shift.
        min_shifts_per_ra = (self.num_weeks * self.num_days) // self.num_ras
        if self.num_weeks * self.num_days % self.num_ras == 0:
            max_shifts_per_ra = min_shifts_per_ra
        else:
            max_shifts_per_ra = min_shifts_per_ra + 1
        for uoid in self.all_uoids:
            num_shifts_worked: Union[cp_model.LinearExpr, int] = 0
            for w in self.all_weeks:
                for d in self.all_days:
                    num_shifts_worked += self.shifts[(uoid, w, d)]
            self.model.add(min_shifts_per_ra <= num_shifts_worked)
            self.model.add(num_shifts_worked <= max_shifts_per_ra)
        return None

    def set_objective(self):
       self.model.maximize(
        sum(
            self.shift_requests[(uoid, w, d)] * self.shifts[(uoid, w, d)]
            for uoid in self.all_uoids
            for w in self.all_weeks
            for d in self.all_days
        )
    )

    def solve(self):
       pass

    def return_schedule(self):
        pass
