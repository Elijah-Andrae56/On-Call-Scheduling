from ortools.sat.python import cp_model
from typing import Union, Iterable, Callable
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


ROLE_TO_INT = {
    "Primary": 0,
    "Secondary": 1
}


INT_TO_ROLE = {
    ROLE_TO_INT["Primary"]: "Primary",
    ROLE_TO_INT["Secondary"]: "Secondary"
}


def is_weekday(day_num: int) -> bool:
    return day_num >= 0 and day_num <= 4


def is_weekend(day_num: int) -> bool:
    return day_num == 5 or day_num == 6


def is_primary(role_num: int) -> bool:
    return role_num == ROLE_TO_INT["Primary"]


def is_secondary(role_num: int) -> bool:
    return role_num == ROLE_TO_INT["Secondary"]

        
class Scheduler:
    def __init__(self, leading_offset: int = 3, trailing_offset: int = 0):
        # Shift Datastructures
        self.shifts: dict = {}
        self.shift_requests: dict = {}
        # Shape of CSV file
        self.LEADING_OFFSET: int = leading_offset  #< for Timestamp, Name, 95# columns.
        self.OFFSET: int = leading_offset + trailing_offset  #< for all columns that are not Availability/Unavailability.
        # Google Ortools
        self.model: cp_model.CpModel = cp_model.CpModel()
        self.solver: cp_model.CpSolver = cp_model.CpSolver()
        self.status: cp_model.CpSolverStatus = cp_model.UNKNOWN
        # General Accounting Information
        self.num_weeks: int = 0
        self.num_days: int = 7  #< All days of the week.
        self.num_weekdays: int = 0
        self.num_weekends: int = 0
        self.num_shifts: int = 0
        self.num_weekday_shifts: int = 0
        self.num_weekend_shifts: int = 0
        self.num_roles: int = 2  #< Primary and Secondary.
        self.num_ras: int = 0
        self.min_shifts_per_ra: int = 0
        self.all_weeks: Iterable = range(0)
        self.all_days: Iterable = range(self.num_days)
        self.all_roles: Iterable = range(self.num_roles)
        self.all_uoids: Iterable = []
        self.uoid_to_name: dict = {}

    def csv_to_df(self, path_to_csv: str) -> pd.DataFrame:
        # Use Pandas to convert csv to dataframe.
        df = pd.read_csv(path_to_csv)
        # The next N columns are dynamically defined.
        self.num_weeks = (df.shape[1] - self.OFFSET) // 2
        self.all_weeks = range(1, self.num_weeks + 1)
        self.num_shifts = self.num_weeks * self.num_days * self.num_roles
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
        # Count Weekdays and Weekends
        for _ in self.all_weeks:
            for d in self.all_days:
                self.num_weekdays += is_weekday(d)
                self.num_weekends += is_weekend(d)
        self.num_weekday_shifts = self.num_weekdays * self.num_roles
        self.num_weekend_shifts = self.num_weekends * self.num_roles
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
                    for r in self.all_roles:
                        self.shifts[(uoid, w, d, r)] = self.model.new_bool_var(f"shift_uoid{uoid}_w{w}_day{d}_role{r}")
                    if ptr2 < len(unavailable) and unavailable[ptr2] == d:
                        for r in self.all_roles:
                            self.shift_requests[(uoid, w, d, r)] = -1
                        ptr2 += 1
                    elif ptr1 < len(available) and available[ptr1] == d:
                        for r in self.all_roles:
                            self.shift_requests[(uoid, w, d, r)] = 1
                        ptr1 += 1
                    else:
                        for r in self.all_roles:
                            self.shift_requests[(uoid, w, d, r)] = 0
                    while ptr1 < len(available) and available[ptr1] < d:
                        ptr1 += 1
        return None

    def constraint_exactly_one_ra_per_shift(self) -> None:
        """
        Each shift is assigned to exactly one RA.
        """
        for w in self.all_weeks:
            for d in self.all_days:
                for r in self.all_roles:
                    self.model.add_exactly_one(
                        self.shifts[(uoid, w, d, r)] 
                        for uoid in self.all_uoids
                    )
        return None

    def constraint_one_ra_per_role_per_day(self) -> None:
        """
        An RA can only work one role per shift.
        """
        for uoid in self.all_uoids:
            for w in self.all_weeks:
                for d in self.all_days:
                    shift_roles = sum(
                        self.shifts[(uoid, w, d, r)]
                        for r in self.all_roles
                    )
                    self.model.add(shift_roles != 2)
        return None

    def constraint_balance_roles_per_ra(self) -> None:
        """
        Balance the number of Primary to Secondary shifts for each RA
        """
        for uoid in self.all_uoids:
            primary_shifts = sum(
                self.shifts[(uoid, w, d, 0)]
                for w in self.all_weeks
                for d in self.all_days
            )
            secondary_shifts = sum(
                self.shifts[(uoid, w, d, 1)]
                for w in self.all_weeks
                for d in self.all_days
            )   
            self.model.add(primary_shifts <= secondary_shifts + 1)
            self.model.add(secondary_shifts <= primary_shifts + 1)
        return None
    
    def constraint_balance_shifts_per_ra(self, num_shifts: int, condition: Callable[[int], bool]) -> None:
        """
        Try to distribute the shifts evenly, so that each RA works min_shifts_per_ra shifts.
        If this is not possible, because the total number of shifts is not divisible by the
        number of ras, some ras will be assigned one more shift.
        """
        min_shifts_per_ra = num_shifts // self.num_ras
        if num_shifts % self.num_ras == 0:
            max_shifts_per_ra = min_shifts_per_ra
        else:
            max_shifts_per_ra = min_shifts_per_ra + 1
        for uoid in self.all_uoids:
            num_total_shifts_worked: Union[cp_model.LinearExpr, int] = 0
            for w in self.all_weeks:
                for d in self.all_days:
                    for r in self.all_roles:
                        if condition(d):
                            num_total_shifts_worked += self.shifts[(uoid, w, d, r)]
            self.model.add(min_shifts_per_ra <= num_total_shifts_worked)
            self.model.add(num_total_shifts_worked <= max_shifts_per_ra)
        return None

    def constraint_at_most_three_consecutive_shifts_per_ra(self) -> None:
        # RAs cannot work more than 3 consecutive shifts
        # NOTE: including across week boundaries
        # Example: Jeff cannot work "Friday, Saturday" of Week 1 and "Sunday, Monday" of Week 2
        n = range((self.num_weeks * self.num_days) - 2)
        for uoid in self.all_uoids:
            for ptr in n:
                consecutive_shifts = sum(
                    self.shifts[(uoid, (i // self.num_days) + 1, i % self.num_days, r)]
                    for i in range(ptr, ptr + 3)
                    for r in self.all_roles
                )
                self.model.add(consecutive_shifts <= 3)
        return None

    def set_constraints(self) -> None:
        self.constraint_exactly_one_ra_per_shift()
        self.constraint_one_ra_per_role_per_day()
        self.constraint_balance_roles_per_ra()
        self.constraint_balance_shifts_per_ra(self.num_shifts, lambda d: True)
        self.constraint_balance_shifts_per_ra(self.num_weekday_shifts, is_weekday)
        self.constraint_balance_shifts_per_ra(self.num_weekend_shifts, is_weekend)
        self.constraint_at_most_three_consecutive_shifts_per_ra()
        return None

    def set_objective(self) -> None:
        self.model.maximize(
            sum(
                self.shift_requests[(uoid, w, d, r)] * self.shifts[(uoid, w, d, r)]
                for uoid in self.all_uoids
                for w in self.all_weeks
                for d in self.all_days
                for r in self.all_roles
            )
        )
        return None

    def solve(self) -> None:
        self.status = self.solver.solve(self.model)
        return None

    def print_schedule(self) -> None:
        if self.status == cp_model.OPTIMAL:
            for w in self.all_weeks:
                print(f'{"Week "+str(w):^68}')
                print(f'{"RA":^17}{"Role":^17}{"Day":^17}{"Preference":^17}')
                print('-'*68)
                for d in self.all_days:
                    for r in self.all_roles:
                        for uoid in self.all_uoids:
                            if self.solver.value(self.shifts[(uoid, w, d, r)]) == 1:
                                pref_str = "(requested)" if self.shift_requests[(uoid, w, d, r)] == 1 else "(not requested)"
                                print(f'{self.uoid_to_name[uoid]:<17}{INT_TO_ROLE[r]:<17}{INT_TO_DAY[d]:<17}{pref_str:<17}')
                print()
            for uoid in self.all_uoids:
                print(f'{"RA " + self.uoid_to_name[uoid] + " Shift Summary":<25}')
                print('='*25)
                total_shifts = 0
                total_weekday_shifts = 0
                total_weekend_shifts = 0
                total_primary_shifts = 0
                total_secondary_shifts = 0
                for w in self.all_weeks:
                    for d in self.all_days:
                        for r in self.all_roles:
                            if self.solver.value(self.shifts[(uoid, w, d, r)]) == 1:
                                total_weekday_shifts += is_weekday(d)
                                total_weekend_shifts += is_weekend(d)
                                total_primary_shifts += is_primary(r)
                                total_secondary_shifts += is_secondary(r)
                                total_shifts += 1
                print(f'{str(total_weekday_shifts) + " Weekday Shifts":>25}')
                print(f'{str(total_weekend_shifts) + " Weekend Shifts":>25}')
                print(f'{str(total_primary_shifts) + " Primary Shifts":>25}')
                print(f'{str(total_secondary_shifts) + " Secondary Shifts":>25}')
                print(f'{"-"*20:>25}')
                print(f'{"Total Shifts: " + str(total_shifts):>25}')
                print()
            print('='*50)
            print("|", end='')
            print(f'{"Schedule Summary":^48}', end='')
            print("|")
            print('='*50)
            print(f'{str(self.num_weeks) + " Weeks":^50}')
            print(f'{str(self.num_weekdays) + " Weekdays":^50}')
            print(f'{str(self.num_weekends) + " Weekends":^50}')
            print(f'{str(self.num_weekday_shifts) + " Weekday Shifts":^50}')
            print(f'{str(self.num_weekend_shifts) + " Weekend Shifts":^50}')
            print(f'{str(int(self.solver.objective_value)) + " out of " + str(self.num_shifts) + " Shift requests met":^50}')
        else:
            print("No optimal solution found !")
        return None
