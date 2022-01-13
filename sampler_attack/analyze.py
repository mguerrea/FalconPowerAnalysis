import getopt, h5py, sys
import numpy as np
from hidden_python import parallelepiped
from utils import shift, conjugate, permute, split
from math import sqrt
import os
import gc
from tqdm import trange
from random import randint
import logging
import time
from ctypes import *

Q = 12289

sigmas = {2: 144.81253976308423, 4: 146.83798833523608, 8: 148.83587593064718, 16: 151.78340713845503, 32: 154.6747794602761, 64: 157.51308555044122, 128: 160.30114421975344, 256: 163.04153322607107, 512: 165.7366171829776, 1024: 168.38857144654395}

def make_indices(n):
    indices = [i for i in range(n-1, -1, -1)]
    indices = permute(indices)
    indices = indices[n//2:] + indices[:n//2]
    f0,f1 = split(indices)
    return(f0+f1)

def make_average(vectors, row, n, existing):
    if len(vectors) == 0 and len(existing) == 0:
        return [0]*n
    if len(vectors) == 0:
        average = np.mean(existing, axis=0)
    else:
        average = np.mean(vectors, axis=0)
    if row < n//2:
        return shift(list(average[n//2:]), row) + shift(list(-average[:n//2]), row)
    else:
        return shift(conjugate(list(average[:n//2])), row - n//2) + shift(conjugate(list(average[n//2:])), row - n//2)

def run_attack(nb_sigs, file, verbose, max_desc, row, existing=[]):
    
    test_sets = [elem for elem in file]
    key_group = file[test_sets[0]]
    key = list(key_group.attrs["key"])
    f,g,F,G = key
    LOGN = key_group.attrs["logn"]
    n = (1 << LOGN) * 2
    indices = make_indices(n)
    nb_cpu = os.cpu_count()
    print("nb cpu:", nb_cpu)
    np.save("key_"+str(n//2)+".npy", key)
    vectors_found = []

    basis = np.array(list(f) + list(g))
    print(basis)

    if row:
        rows = [row]
    else:
        rows = [indices.index(i) for i in range(n-1, n-5, -1)] + [indices.index(i) for i in range(0, 4, 1)]
    for row in rows:
        # vectors_found = []
        print("row:", row)
        sigs =  np.array([[0] * n] * nb_sigs, dtype=np.int16)
        # aleas = np.array([0] * nb_sigs, dtype=np.int8)

        print(nb_sigs)

        datasets = [elem for elem in key_group]
        index = indices[row]
        i = 0
        for k in trange(nb_sigs):
            # aleas[k] = key_group[datasets[k]].attrs["alea"][index]
            if key_group[datasets[k]].attrs["alea"][index] == 0 or key_group[datasets[k]].attrs["alea"][index] == 1:
                sigs[i] = key_group[datasets[k]][:,]
                i += 1

        nb_sigs_real = i

        points = sigs[:nb_sigs_real]
        print(len(points))
        del sigs

        gc.collect()

        bound = sqrt(n)
        norm_th = 1.17*sqrt(Q)
        total_time = 0

        average = make_average(vectors_found, row, n, existing)

        start = time.time()
        v = parallelepiped(points, average, max_desc, nb_cpu)
        end = time.time()
        total_time += (end - start)
        print("time =", total_time)
        v = v/(np.linalg.norm(v)/norm_th)
        
        if (row < n//2):
            v = shift(list(-v[n//2:]), -row) + shift(list(v[:n//2]), -row)
        else:
            v = conjugate(shift(list(v[:n//2]), - (row - n//2))) + conjugate(shift(list(v[n//2:]), -(row-n//2)))

        if np.linalg.norm(basis+v) < np.linalg.norm(basis-v):
            v = -np.array(v)

        dist = np.linalg.norm(basis-v)
        logging.info("distance: {}".format(dist))
        if verbose:
            print(v)
            print(dist)
        if dist < bound:
            print("close:")
            print("V:", v)
            logging.info("close vector found")
            
        vectors_found.append(v)

        np.save("vectors_"+str(n//2)+"_"+str(row)+".npy", vectors_found[-1])

    np.save("vectors_"+str(n//2)+".npy", vectors_found)
    average = np.mean(vectors_found, axis=0)
    basis = list(f) + list(g)
    dist = np.linalg.norm(average-basis)
    print("average:", dist)
    logging.info("average: {}".format(dist))
    



def usage(exe):
    opt = {"-h --help": "display this summary",
        "--nb-sigs=<value>": "number of signatures to use for each test",
        "--input-file=<file>": "file where the signatures are stored",
        "-v --verbose": "run the attack in verbose mode",
        "--row=<value>": "recover specific row",
        "--existing=<file>": "use existing vectors as starting point",
        "--max-desc=<value>": "maximum of iterations for a gradient descent"
        }
    print("usage:", exe, "[options]")
    print("Options:")
    for elem in opt:
        print(f' {elem:30} {opt[elem]}')

def main():
    argv = sys.argv[1:]
    nb_sigs = 1000
    input_file = "sig.hdf5"
    verbose = False
    max_desc=100
    row = None
    existing = []

    if len(argv) > 0:
        try:
            opts, args = getopt.getopt(
                argv, "vh", ["nb-sigs=", "input-file=", "help", "max-desc=", "row=", "existing="]
            )
        except getopt.GetoptError as err:
            print(err)
            usage(sys.argv[0])
            sys.exit(2)
        for o, a in opts:
            if o == "--nb-sigs":
                nb_sigs = int(a)
            elif o == "--input-file":
                input_file = a
            elif o in ["-v", '--verbose']:
                verbose = True
            elif o in ['-h', '--help']:
                usage(sys.argv[0])
                sys.exit(2)
            elif o == "--max-desc":
                max_desc = int(a)
            elif o == "--row":
                row = int(a)
            elif o == "--existing":
                existing = np.load(a)

    file = h5py.File(input_file, "r")
    test_sets = [elem for elem in file]
    assert nb_sigs <= min([len(file[elem]) for elem in test_sets])
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(filename='analyze.log', level=logging.DEBUG, format=FORMAT)
    logging.info("----START ATTACK----")
    logging.info("input file: " + input_file)
    logging.info("nb sigs: " + str(nb_sigs))
    logging.info("max desc: " + str(max_desc))
    run_attack(nb_sigs, file, verbose, max_desc, row, existing)
    logging.info("----END ATTACK----")


if __name__ == "__main__":
    main()
