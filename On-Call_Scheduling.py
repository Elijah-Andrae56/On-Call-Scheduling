"""Elijah Andrae
This project is built in great colaberation with GPT-o1"""

NUMBER_PREFERRED_SHIFTS = 15
NUMBER_UNAVAILABLE_SHIFTS = 10

from ortools.sat.python import cp_model

# Step 1: Define the data

# List of RAs
ras = ['RA1', 'RA2', 'RA3', 'RA4', 'RA5', 'RA6', 'RA7', 'RA8',
       'RA9', 'RA10', 'RA11', 'RA12', 'RA13', 'RA14', 'RA15', 'RA16']

num_ras = len(ras)

# Define the schedule period (e.g., 30 days)
num_days = 90

# For simplicity, let's assume day 0 is a Monday
# Define whether each day is a weekday (0) or weekend (1)
weekend = [1 if (day % 7) in [5, 6] else 0 for day in range(num_days)]

# Each day has two roles: primary (0) and secondary (1)
roles = [0, 1]  # 0: Primary, 1: Secondary

# RAs' preferences and unavailabilities
# For this example, we'll create random preferences and unavailabilities
# In a real scenario, you would collect this data from the RAs

import random

# random.seed(42)  # For reproducibility

# Initialize dictionaries to hold preferences and unavailabilities
preferences = {}     # preferences[ra] = set of preferred (day, role)
unavailabilities = {}  # unavailabilities[ra] = set of (day)

for ra in ras:
    # Randomly select 15 preferred weekdays (roles are ignored for preferences)
    preferred_weekdays = random.sample([d for d in range(num_days) if weekend[d] == 0], NUMBER_PREFERRED_SHIFTS)
    preferences[ra] = set(preferred_weekdays)
    # Randomly select days the RA is unavailable (up to 5 days)
    unavailable_days = random.sample(range(num_days), random.randint(0, NUMBER_UNAVAILABLE_SHIFTS))
    unavailabilities[ra] = set(unavailable_days)

# Step 2: Create the model
model = cp_model.CpModel()

# Step 3: Define variables
# x[ra_index][day][role] = 1 if RA is assigned to day and role
x = {}
for ra_index, ra in enumerate(ras):
    x[ra_index] = {}
    for day in range(num_days):
        x[ra_index][day] = {}
        for role in roles:
            x[ra_index][day][role] = model.NewBoolVar(f'x_{ra}_{day}_{role}')

# Step 4: Add constraints

# Constraint 1: Each shift (day and role) must have exactly one RA assigned
for day in range(num_days):
    for role in roles:
        model.Add(sum(x[ra_index][day][role] for ra_index in range(num_ras)) == 1)

# Constraint 2: RAs cannot be assigned on days they are unavailable
for ra_index, ra in enumerate(ras):
    for day in unavailabilities[ra]:
        for role in roles:
            model.Add(x[ra_index][day][role] == 0)

# Constraint 3: Each RA must have 3-4 weekend shifts
for ra_index, ra in enumerate(ras):
    num_weekend_shifts = sum(
        x[ra_index][day][role]
        for day in range(num_days)
        for role in roles
        if weekend[day] == 1
    )
    model.Add(num_weekend_shifts >= 3)
    model.Add(num_weekend_shifts <= 4)

# Constraint 4: Each RA must have 8-9 weekday shifts
for ra_index, ra in enumerate(ras):
    num_weekday_shifts = sum(
        x[ra_index][day][role]
        for day in range(num_days)
        for role in roles
        if weekend[day] == 0
    )
    model.Add(num_weekday_shifts >= 8)
    model.Add(num_weekday_shifts <= 9)

# Constraint 5: Balance primary and secondary shifts for each RA
for ra_index, ra in enumerate(ras):
    num_primary = sum(
        x[ra_index][day][0]  # role 0 is primary
        for day in range(num_days)
    )
    num_secondary = sum(
        x[ra_index][day][1]  # role 1 is secondary
        for day in range(num_days)
    )
    # The difference between primary and secondary shifts should be at most 1
    diff = model.NewIntVar(0, num_days, f'diff_{ra_index}') # Assume num_days as the max possible difference for simplicity
    
    model.AddAbsEquality(diff, num_primary - num_secondary)
    # The modified version of the constraint: the difference should be at most 1
    model.Add(diff <= 1)

# Constraint 6: Ensure the primary and secondary RA is not the same person on any given day
for ra_index, ra in enumerate(ras):
    for day in range(num_days):
        for ra_index in range(num_ras):
            model.Add(x[ra_index][day][0] + x[ra_index][day][1] <= 1)

# Constraint 7: Ensure no RA works more than 3 consecutive days
for ra_index, ra in enumerate(ras):
    for start_day in range(num_days - 3):  # Subtract 3 to prevent index out of range
        model.Add(sum(x[ra_index][day][role] for day in range(start_day, start_day + 4) for role in roles) <= 3)

 

# Step 5: Define the objective function
# Maximize the number of preferred shifts assigned
total_preferences = []
for ra_index, ra in enumerate(ras):
    for day in range(num_days):
        for role in roles:
            if day in preferences[ra] and weekend[day] == 0:
                # Only consider weekday preferences
                total_preferences.append(x[ra_index][day][role])

model.Maximize(sum(total_preferences))

# Step 6: Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Step 7: Output the results
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print('Solution found:')
    schedule = {}
    for day in range(num_days):
        schedule[day] = {}
        for role in roles:
            for ra_index, ra in enumerate(ras):
                if solver.Value(x[ra_index][day][role]) == 1:
                    schedule[day][role] = ra
                    break  # Move to the next role
    # Print the schedule
    for day in range(num_days):
        day_type = 'Weekend' if weekend[day] == 1 else 'Weekday'
        print(f'Day {day} ({day_type}):')
        print(f"  Primary RA: {schedule[day][0]}")
        print(f"  Secondary RA: {schedule[day][1]}")
else:
    print('No feasible solution found.')
