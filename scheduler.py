import datetime as dt
from ortools.sat.python import cp_model
import pandas as pd
import numpy as np


class Date:
    def __init__(self) -> None:
        pass

    def __str__(self):
        pass


class DateManager:
    def __init__(self):
        pass

    def __str__(self):
        pass

    def generate_days(self):
        pass

    def count_days(self):
        pass
        

class Scheduler:
    def __init__(self):
        pass

    def csv_to_df(self, path_to_csv: str) -> pd.DataFrame:
        # Use Pandas to convert csv to dataframe.
        df = pd.read_csv(path_to_csv)
        
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

        return df

    def create_shift_variables(self):
        pass

    def append_constraint(self):
       pass

    def set_objective(self):
       pass

    def solve(self):
       pass

    def return_schedule(self):
        pass
