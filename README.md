# RA Shift Scheduler

This project is a Resident Assistant (RA) shift scheduler for Summer 2024, designed to automate the assignment of primary and secondary RAs to shifts over a specified date range. It takes into account RA availability, preferences, and various scheduling constraints to produce an optimal schedule.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Data Format](#data-format)
- [Constraints and Objectives](#constraints-and-objectives)
- [Example Output](#example-output)
- [License](#license)

## Introduction

### Step 1: Fill Out the Availability Form

Before running the scheduler, RAs need to fill out the [On-Call Availability Form](https://docs.google.com/forms/d/e/1FAIpQLScU_GKuOyepmiIuW-9scQHOhAViftG3sAhm7SkTvF2Zr-zV7Q/viewform?usp=sf_link). This Google Form collects each RA's availability and unavailability using a grid-based input process:


- **Grid-Based Input**: The form presents a grid where RAs can select their preferred shifts and indicate any shifts they absolutely cannot work.
- **Shift Selection**:
  - **Preferred Shifts**: Choose a minimum number of weekend and weekday shifts for your RA to choose.
  - **Unavailable Shifts**: Select any shifts you absolutely cannot work (e.g., due to important events or commitments).
- **Important Notes**:
  - Do not select both available and unavailable for the same shift, as this will cause scheduling conflicts.
  - Refer to the provided dates for each week to accurately select your availability.

By filling out this form, you provide the necessary data for the scheduler to generate an optimal shift schedule that accommodates everyone's preferences and constraints.

## Features

- **Automated Scheduling**: Automatically assigns RAs to shifts based on availability and preferences.
- **Constraint Satisfaction**: Ensures scheduling constraints are met, such as maximum consecutive working days and balanced shift distribution.
- **Preference Maximization**: Maximizes the assignment of preferred shifts to RAs.
- **Weekend and Weekday Balancing**: Balances the number of weekend and weekday shifts among RAs.
- **Role Balancing**: Balances primary and secondary roles for each RA.

## Requirements

- Python 3.7 or higher
- Required Python packages:
  - `pandas`
  - `ortools`

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/ra-shift-scheduler.git
   cd ra-shift-scheduler
   ```

2. **Install Dependencies**

   Install the required Python packages using `pip`:

   ```bash
   pip install pandas ortools
   ```

## Usage

1. **Prepare the Availability Data**

   Ensure all RAs have filled out the [On-Call Availability Form](https://docs.google.com/forms/d/e/1FAIpQLScU_GKuOyepmiIuW-9scQHOhAViftG3sAhm7SkTvF2Zr-zV7Q/viewform?usp=sf_link). The responses should be collected and saved as a CSV file.

2. **Set the Date Range**

   In the `__main__` section of the script, set the `start_date` and `end_date`:

   ```python
    # Start date, Sunday before week 1 (YYYY, M, D) 
   start_date = dt.datetime(2024, 9, 29) 

    # End date, Saturday after finals week (YYYY, M, D)
    end_date = dt.datetime(2024, 12, 13)   
   ```
   

3. **Update the CSV File Path**

   Ensure the `file_path` variable points to the CSV file containing the form responses:

   ```python
   file_path = 'Schedule/test_data.csv'
   ```

4. **Run the Scheduler**

   Execute the script:

   ```bash
   python ra_shift_scheduler.py
   ```

5. **View the Output**

   The script will output the scheduled shifts in the console, detailing the primary and secondary RAs assigned to each day.

## Data Format

The scheduler expects a CSV file containing the responses from the Google Form with the following structure:

- **Columns**:
  - `Timestamp`: Submission timestamp (formatted as `YYYY/MM/DD HH:MM:SS AM/PM`)
  - `Name`: Full name of the RA
  - `95#`: RA identification number
  - **Preferred Shifts**: Columns labeled as `Availability Week X`, where X is the week number, containing semicolon-separated lists of preferred days.
  - **Unavailable Shifts**: Columns labeled as `Unavailability Week X`, where X is the week number, containing semicolon-separated lists of unavailable days.

- **Day Names**:

  Days should be spelled correctly (e.g., `Monday`, `Tuesday`, etc.). The script accounts for common misspellings like `Wednsday`.

- **Example Row**:

  | Timestamp           | Name         | 95#     | Availability Week 1 | Unavailability Week 1 |
  |---------------------|--------------|---------|---------------------|-----------------------|
  | 2024/09/01 10:00:00 | John Doe     | 9500001 | Monday; Wednesday   | Friday                |

## Constraints and Objectives

### Constraints

1. **Shift Coverage**: Each shift must have exactly one primary and one secondary RA assigned.
2. **Availability**: RAs cannot be assigned on days they are unavailable.
3. **Shift Distribution**:
   - Weekend shifts are evenly distributed among RAs.
   - Weekday shifts are evenly distributed among RAs.
4. **Role Balancing**: Each RA should have a balanced number of primary and secondary shifts (difference should not exceed 1).
5. **No Double Booking**: An RA cannot be both primary and secondary on the same day.
6. **Consecutive Workdays**: An RA cannot work more than 3 consecutive days.

### Objectives

- **Preference Maximization**: Maximize the number of preferred shifts assigned to RAs.

## Example Output

```
Solution found:
Day 0 (2024-09-29, Weekend, Week 1):
  Primary RA: John Doe
  Secondary RA: Jane Smith
Day 1 (2024-09-30, Weekday, Week 1):
  Primary RA: Alice Johnson
  Secondary RA: Bob Brown
...
```

## License

This project is licensed under the MIT License. 

# Contact

For any questions or suggestions, please contact Elijah Andrae at [elijah.andrae56&outlook.com](mailto:elijah.andrae56&outlook.com).

# Acknowledgments

- [Google OR-Tools](https://developers.google.com/optimization) for the constraint programming library.
- The Barnhart RA team for providing test-availability data.
- ChatGPT-4o and ChatGPT-o1

# Notes

- Ensure the CSV file path in the script matches the location of your data file:

  ```python
  file_path = 'Schedule/test_data.csv'
  ```

- Adjust the start and end dates to match your scheduling period.

- The script currently outputs to the console. Modify the `print_schedule()` method if you wish to save the output to a file.

# Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

---

*This README was generated to assist users in understanding and utilizing the RA Shift Scheduler for Summer 2024.*
