import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import argrelextrema
from sklearn.neighbors._kde import KernelDensity
from utils import add_noise
from random import gauss

foldername = 'FalconSimulation'
classname = 'Falcon'

from elmo.manage import get_simulation
simu = get_simulation(classname, foldername)
simulation = simu()


nb_tests = 1000
nb_challenges = 100


index = 68
for index in range(68, 69):

    success = 0
    for i in range(nb_tests//nb_challenges):

        challenges = simulation.get_random_challenges(nb_challenges)
        simulation.set_challenges(challenges)
        simulation.run()

        traces = simulation.get_traces()
        out = simulation.get_printed_data(False)

        for j in range(nb_challenges):
            # for t in traces[j*18:(j+1)*18]:
            #     plt.plot(t)
            # plt.show()
 
            points = [t[index] for t in traces[j*18:(j+1)*18]]
            points.sort()
            a = np.array(points).reshape(-1, 1)
            kde = KernelDensity(kernel='gaussian', bandwidth=0.00005).fit(a)
            s = np.linspace(min(points),max(points))
            e = kde.score_samples(s.reshape(-1,1))
            
            mi, ma = argrelextrema(e, np.less)[0], argrelextrema(e, np.greater)[0]
            if len(mi) == 0:
                z0 = 0
            else:
                seuil = s[mi[np.argmin([e[m] for m in mi])]]
                z0 = len(list(filter(lambda p: p > seuil, points)))

            if (z0 == out[j]):
                success += 1

    print("success:", success)
    print("nb tests:", nb_tests)
