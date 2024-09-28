import unittest
import datetime as dt
import os
import sys

# Add parent directory to PATH
current_directory = os.path.dirname(os.path.realpath(__file__))  # pwd
parent_directory = os.path.dirname(current_directory)            # cd ..
sys.path.append(parent_directory)                                # add parent dir to PATH

# Import from file in the parent directory.
from on_call_scheduling_final import Scheduler

# Now import date_manager from parent directory
from date_manager import DateManager, DateManager


class TestScheduleFinal(unittest.TestCase):

    def test_on_call_scheduling_final(self):
        # This is what was found in on_call_scheduling_final.py
        
        start_date = dt.datetime(2024, 9, 29)  # Enter the date of Sunday Week 1
        end_date = dt.datetime(2024, 12, 13)   # Enter the date of Friday end of Finals Week

        time_range = DateManager(start_date, end_date)
        scheduler = Scheduler(time_range)

        # Path to your CSV file
        file_path = current_directory + r'/data/example_1.csv'
        
        scheduler.load_data(file_path)
        scheduler.parse_data()
        
        # scheduler.build_model()
        # scheduler.add_constraints()
        # scheduler.define_objective()
        # scheduler.solve()
        scheduler.run()

        test_schedular = scheduler.return_schedule()
        print(test_schedular)

if __name__ == '__main__':
    unittest.main()
    print()