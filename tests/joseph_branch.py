import unittest
import os
import sys

# Add parent directory to PATH
current_directory = os.path.dirname(os.path.realpath(__file__))  # pwd
parent_directory = os.path.dirname(current_directory)            # cd ..
sys.path.append(parent_directory)                                # add parent dir to PATH

# Now import from file in the parent directory.
# from on_call_scheduling_final import DateManager, Scheduler

class TestJosephBranch(unittest.TestCase):

    def test_branch(self):
        file_path = current_directory + r'/data/example_3.csv'
        print(file_path)


if __name__ == '__main__':
    unittest.main()