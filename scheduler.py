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

    def load_csv(self, path_to_csv: str):
        print(path_to_csv)
        

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
