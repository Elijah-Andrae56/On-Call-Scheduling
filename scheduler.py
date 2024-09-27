import datetime as dt
from ortools.sat.python import cp_model
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
        self.OFFSET = 3

    
    def csv_to_df(self, path_to_csv: str) -> pd.DataFrame:
        # Use Pandas to convert csv to dataframe.
        df = pd.read_csv(path_to_csv)

        # The next N columns are dynamically defined.
        num_weeks = (len(df.columns) - self.OFFSET) // 2

        # Enforce naming on the dataframe's columns.
        df = df.rename(columns={
            **{
            df.columns[0]: "Timestamp",
            df.columns[1]: 'Name', 
            df.columns[2]: '95#'},
            **{
            df.columns[i+self.OFFSET]: f"Availability Week {i+1}"
            for i in range(num_weeks)
            },
            **{
            df.columns[i+self.OFFSET+num_weeks]: f"Unavailability Week {i+1}"
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

        return df
    
    def load_df(self, df: pd.DataFrame) -> None:
        if (df.shape[1] - self.OFFSET) % 2 == 1:
            raise ValueError("dataframe should contain even \
            number of available weeks to unavailable weeks.")
        self.model = cp_model.CpModel()
        num_weeks = (df.shape[1] - self.OFFSET) // 2
        for _, row in df.iterrows():
            uoid = row["95#"]
            name = row["Name"]
            for w in range(1, num_weeks + 1):
                available = row[f"Availability Week {w}"].split(';')
                unavailable = row[f"Unavailability Week {w}"].split(';')
                available = [DAY_TO_INT[d] for d in available]
                unavailable = [DAY_TO_INT[d] for d in unavailable]
                available.sort()
                unavailable.sort()
                ptr1 = 0
                ptr2 = 0
                for d in range(7):
                    self.shifts[(uoid, name, w, d)] = self.model.new_bool_var(f"shift_uoid{uoid}_name{name}_w{w}_day{d}")
                    if ptr2 < len(unavailable) and unavailable[ptr2] == d:
                        self.shift_requests[(uoid, name, w, d)] = -1
                        ptr2 += 1
                    elif ptr1 < len(available) and available[ptr1] == d:
                        self.shift_requests[(uoid, name, w, d)] = 1
                        ptr1 += 1
                    else:
                        self.shift_requests[(uoid, name, w, d)] = 0
        return None

    def append_constraint(self):
       pass

    def set_objective(self):
       pass

    def solve(self):
       pass

    def return_schedule(self):
        pass
