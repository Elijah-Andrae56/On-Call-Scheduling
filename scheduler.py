from ortools.sat.python import cp_model
from typing import Union, Iterable
import pandas as pd


DAY_TO_INT = {
    "Sunday": 0,
    "Monday": 1,
    "Tuesday": 2,
    "Wednsday": 3,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6
}


INT_TO_DAY = {
    DAY_TO_INT["Sunday"]: "Sunday",
    DAY_TO_INT["Monday"]: "Monday",
    DAY_TO_INT["Tuesday"]: "Tuesday",
    DAY_TO_INT["Wednsday"]: "Wednsday",
    DAY_TO_INT["Wednesday"]: "Wednesday",
    DAY_TO_INT["Thursday"]: "Thursday",
    DAY_TO_INT["Friday"]: "Friday",
    DAY_TO_INT["Saturday"]: "Saturday",
}

        
class Scheduler:
    def __init__(self, leading_offset: int = 3, trailing_offset: int = 0):
        self.shifts: dict = {}
        self.shift_requests: dict = {}
        self.model: cp_model.CpModel = cp_model.CpModel()
        self.solver: cp_model.CpSolver = cp_model.CpSolver()
        self.status: cp_model.CpSolverStatus = cp_model.UNKNOWN
        self.num_weeks: int = 0
        self.num_days: int = 7
        self.num_ras: int = 0
        self.min_shifts_per_ra: int = 0
        self.all_weeks: Iterable = range(0)
        self.all_days: Iterable = range(self.num_days)
        self.all_uoids: Iterable = []
        self.uoid_to_name: dict = {}
        self.LEADING_OFFSET: int = leading_offset  # for Timestamp, Name, 95# columns
        self.OFFSET: int = leading_offset + trailing_offset  # for all columns that are not Availability/Unavailability

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
            df.columns[i+self.LEADING_OFFSET]: f"Availability Week {i+1}"
            for i in range(self.num_weeks)
            },
            **{
            df.columns[i+self.LEADING_OFFSET+self.num_weeks]: f"Unavailability Week {i+1}"
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
            error_msg = "ERR: dataframe should contain even ratio of available"
            error_msg += " weeks to unavailable weeks. Try reconfiguring the"
            error_msg += " leading offset and trailing offset."
            raise ValueError(error_msg)
        self.all_weeks = range(1, self.num_weeks + 1)
        for index, row in df.iterrows():
            uoid = row["95#"]
            self.uoid_to_name[uoid] = row["Name"]
            self.num_ras += 1
            self.all_uoids.append(uoid)
            for w in self.all_weeks:
                if not df.isna().at[index, f"Availability Week {w}"]:
                    available = row[f"Availability Week {w}"].split(';')
                else:
                    available = []
                if not df.isna().at[index, f"Unavailability Week {w}"]:
                    unavailable = row[f"Unavailability Week {w}"].split(';')
                else:
                    unavailable = []
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
        # 1: Each shift is assigned to exactly one RA.
        for w in self.all_weeks:
            for d in self.all_days:
                self.model.add_exactly_one(self.shifts[(uoid, w, d)] for uoid in self.all_uoids)
        # 2: Try to distribute the shifts evenly, so that each RA works
        # min_shifts_per_ra shifts. If this is not possible, because the total
        # number of shifts is not divisible by the number of ras, some ras will
        # be assigned one more shift.
        self.min_shifts_per_ra = (self.num_weeks * self.num_days) // self.num_ras
        if self.num_weeks * self.num_days % self.num_ras == 0:
            max_shifts_per_ra = self.min_shifts_per_ra
        else:
            max_shifts_per_ra = self.min_shifts_per_ra + 1
        for uoid in self.all_uoids:
            num_shifts_worked: Union[cp_model.LinearExpr, int] = 0
            for w in self.all_weeks:
                for d in self.all_days:
                    num_shifts_worked += self.shifts[(uoid, w, d)]
            self.model.add(self.min_shifts_per_ra <= num_shifts_worked)
            self.model.add(num_shifts_worked <= max_shifts_per_ra)

        # 3: RAs cannot work more than 3 consecutive shifts
        # BUG: Does not check for consecutive days that cross week boundaries.
        # Example: Jeff works "Friday, Saturday" of week 1 then works "Sunday, Monday" of week 2.
        for uoid in self.all_uoids:
            for w in self.all_weeks:
                for start in range(self.num_days - 3):
                    consecutive_shifts = sum(
                        self.shifts[(uoid, w, d)]
                        for d in range(start, start + 3)
                    )
                    self.model.add(consecutive_shifts <= 3)
        return None

    def set_objective(self) -> None:
        self.model.maximize(
            sum(
                self.shift_requests[(uoid, w, d)] * self.shifts[(uoid, w, d)]
                for uoid in self.all_uoids
                for w in self.all_weeks
                for d in self.all_days
            )
        )
        return None

    def solve(self) -> None:
        self.status = self.solver.solve(self.model)
        return None

    def print_schedule(self) -> None:
        if self.status == cp_model.OPTIMAL:
            print("Solution:")
            for w in self.all_weeks:
                print("Week", w)
                for uoid in self.all_uoids:
                    for d in self.all_days:
                        if self.solver.value(self.shifts[(uoid, w, d)]) == 1:
                            if self.shift_requests[(uoid, w, d)] == 1:
                                print("RA", self.uoid_to_name[uoid], "works week", w, INT_TO_DAY[d], "(requested).")
                            else:
                                print("RA", self.uoid_to_name[uoid], "works week", w, INT_TO_DAY[d], "(not requested).")
                print()
            print(
                f"Number of shift requests met = {self.solver.objective_value}",
                f"(out of {self.num_ras * self.min_shifts_per_ra})",
            )
        else:
            print("No optimal solution found !")
        return None
