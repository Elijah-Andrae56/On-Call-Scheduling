import unittest
import os
import sys


# Add parent directory to PATH
current_directory = os.path.dirname(os.path.realpath(__file__))  # pwd
parent_directory = os.path.dirname(current_directory)            # cd ..
sys.path.append(parent_directory)                                # add parent dir to PATH


# Now import from file in the parent directory.
from scheduler import Scheduler


class TestScheduler(unittest.TestCase):

    def test_scheduler(self):
        path_to_csv = current_directory + r'/data/example_2.csv'
        scheduler = Scheduler(leading_offset=3, trailing_offset=1)
        df = scheduler.csv_to_df(path_to_csv)
        scheduler.load_df(df)
        scheduler.set_constraints()
        scheduler.set_objective()
        scheduler.solve()
        scheduler.print_schedule()
        scheduler_df = scheduler.get_dataframe()
        scheduler_df.to_csv(current_directory + r'/data/schedule_example.csv')


if __name__ == '__main__':
    unittest.main()