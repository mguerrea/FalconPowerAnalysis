import numpy as np
from random import gauss
import operator
import matplotlib.pyplot as plt

def decompose(x: np.float64): 
    n = np.abs(x).view(np.int64)
    negative = (x < 0)*1
    exponent = (n >> 52) & 0x7ff
    significand = (n & np.int64((1 << 52) - 1))  | np.int64(1 << 52)
    return (negative, exponent, significand)

def get_float(s, e, zu):
    return ((-1)**s*2.0**(e-1023-52)*zu)

def parse_float(b0, b1, b2, b3, b4, b5, b6, b7):
    x = b0 << 56 | b1 << 48 | b2 << 40 | b3 << 32 | b4 << 24 | b5 << 16 | b6 << 8 | b7 
    s = x >> 63
    e = (x >> 52) & 0x7ff
    m = (x & ((1 << 52) - 1)) | (1 << 52)
    return(get_float(s,e,m))

def find_pattern(pattern, traces, start, end):
    nb_points = len(pattern)
    
    if start < 0:
        start = 0
    mean = np.mean([t[start:end] for t in traces], axis=0)
    index = start
    for i in range(start, end - nb_points):
        diff = list(map(operator.sub, pattern, mean[i-start:i-start+nb_points]))
        norm = np.linalg.norm(diff)
        if norm < 0.4:
            return i
    return index

def find_all_indexes(traces, pattern, DIM, plot):
    points_per_mul = len(pattern)
    indexes = []

    if plot:
        for t in traces[:50]:
            plt.plot(t, linewidth=0.2, color='green')

    start = 0
    end = start + points_per_mul + 1000
    for i in range(DIM):
        xc = find_pattern(pattern, traces, start, end)
        indexes.append(xc)

        start = xc + points_per_mul - 50
        end = start + points_per_mul + 1000

        xc = find_pattern(pattern, traces, start, end)
        indexes.append(xc)
    
        start = xc + points_per_mul - 50
        end = start + points_per_mul + 1000
        
    
    if plot:
        for i in range(DIM*2):
            if (i%4 == 0):
                plt.axvline(x=indexes[i], color='r')
            else:
                plt.axvline(x=indexes[i], color='b')
        plt.show()
    
    return(indexes)

def add_noise(traces, sigma):
    for i in range(len(traces)):
        traces[i] += gauss(0, sigma)

def remove_noise(traces, challenges):
    sorted_challenges = {}
    PREC = 10
    for i in range(len(challenges)):
        s,e,m = decompose(challenges[i])
        dist = e << PREC | m >> (53 - PREC)
        if dist not in sorted_challenges:
            sorted_challenges[dist] = [traces[i]]
        else:
            sorted_challenges[dist].append(traces[i])
    
    new_traces = []
    new_challenges = []
    for elem, t in sorted_challenges.items():
        new_challenges.append(get_float(0, elem >> PREC, (elem & ((1 << PREC) - 1)) << (53 - PREC)))
        new_traces.append(np.mean(t, axis=0))
    
    return (new_traces, new_challenges)