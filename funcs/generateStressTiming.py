import numpy as np


def generateInterval(end_time):


# Define parameters
    start_time = 1  # starting time
    end_time = end_time  # ending time
    num_intervals = 10  # number of intervals

    # Generate time intervals with a power-law behavior
    time_intervals = np.logspace(np.log10(start_time), np.log10(end_time), num=num_intervals, base=10.0)

    print("Generated time intervals:", time_intervals)
    return time_intervals