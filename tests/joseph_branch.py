import unittest
import os
import sys

# Add parent directory to PATH
current_directory = os.path.dirname(os.path.realpath(__file__))  # pwd
parent_directory = os.path.dirname(current_directory)            # cd ..
sys.path.append(parent_directory)                                # add parent dir to PATH

# Now import from file in the parent directory.
from scheduler import Scheduler

class TestJosephBranch(unittest.TestCase):

    def test_branch(self):
        path_to_csv = current_directory + r'/data/example_3.csv'
        
        scheduler = Scheduler()

        df = scheduler.csv_to_df(path_to_csv)
        scheduler.load_df(df)
        # Append Constraints
        # Set objective
        # Solve



if __name__ == '__main__':
    unittest.main()