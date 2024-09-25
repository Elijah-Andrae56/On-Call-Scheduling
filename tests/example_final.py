import unittest
import datetime as dt
import os
import sys

# Add parent directory to PATH
current_directory = os.path.dirname(os.path.realpath(__file__))  # pwd
parent_directory = os.path.dirname(current_directory)            # cd ..
sys.path.append(parent_directory)                                # add parent dir to PATH

# Now import from file in the parent directory.
from on_call_scheduling_final import DateManager, Scheduler


class TestScheduleFinal(unittest.TestCase):

    def test_on_call_scheduling_final(self):
        # This is what was found in on_call_scheduling_final.py
        
        start_date = dt.datetime(2024, 9, 29)  # Enter the date of Sunday Week 1
        end_date = dt.datetime(2024, 12, 13)   # Enter the date of Friday end of Finals Week

        time_range = DateManager(start_date, end_date)
        scheduler = Scheduler(time_range)

        # Path to your CSV file
        file_path = f'{current_directory}/../example_1.csv' # Can you explain this to me? I couldn't figure out how to make it work.
        # file_path = f'Schedule/tests/data/example_1.csv'

        scheduler.load_data(file_path)
        scheduler.parse_data()


if __name__ == '__main__':
    unittest.main()