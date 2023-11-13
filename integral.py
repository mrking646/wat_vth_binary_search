import numpy as np
import  scipy

data = []
with open("data.txt") as f:
    for line in f:
        data.append(float(line.strip()))
    print(data)
vg = []
G1 = []
for i in range(len(data)):
    vg.append(-0.5+i*0.02)
for i in range(len(data)):
    G1.append(vg[i] - 2*scipy.integrate.simps(data)/data[i])

print(G1)