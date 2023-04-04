import numpy as np


#generate time intervals
def generateStressTiming(totalTime, num):
    # generate time intervals for stress, the next step is 1/2 decades * (last step)
    stress_interval = np.logspace(start=0, stop=np.log10(totalTime), num=num, base=10)
    return stress_interval



    