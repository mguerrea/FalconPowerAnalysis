import matplotlib.pyplot as plt
import numpy as np
import os, sys, getopt
import h5py
from utils import decompose, get_float, add_noise, remove_noise, find_all_indexes
from math import ceil
import time, operator
from fft import iFFT, FFT

PRECISION = 8

HW = [bin(n).count("1") for n in range(0, 2048)]

def perform_cpa(keys, traces, challenges, dist, key, plot):

    numtraces = len(traces)
    numpoint = np.shape(traces)[1]
    cpaoutput = {}
    maxcpa = {}

    for kguess in keys:
        sumnum = np.zeros(numpoint)
        sumden1 = np.zeros(numpoint)
        sumden2 = np.zeros(numpoint)

        hyp = np.zeros(numtraces)
        for tnum in range(0, numtraces):
            hyp[tnum] = dist(challenges[tnum], kguess)

        meanh = np.mean(hyp, dtype=np.float64)
        meant = np.mean(traces, axis=0, dtype=np.float64)

        for tnum in range(0, numtraces):
            hdiff = hyp[tnum] - meanh
            tdiff = traces[tnum, :] - meant

            sumnum = sumnum + (hdiff * tdiff)
            sumden1 = sumden1 + hdiff * hdiff
            sumden2 = sumden2 + tdiff * tdiff

        cpaoutput[kguess] = sumnum / np.sqrt(sumden1 * sumden2)
        maxcpa[kguess] = max(abs(cpaoutput[kguess]))

    guess = max(maxcpa, key=lambda y: abs(maxcpa[y]))
    return guess


def recover_mantissa(traces, challenges, verbose, plot, key):
    def intermediate(op, key):
        s, e, m = decompose(op)
        tmp = (key << (27 - PRECISION)) * (m >> 25)
        return HW[tmp >> 49]

    start = 400 # POI: change if needed
    end = -1 # POI: change if needed
    traces = np.array([t[start:end] for t in traces], dtype=np.float64) 

    mantissas = [i for i in range(1 << PRECISION)]
    keys = [1 << PRECISION | m for m in mantissas]

    guess = perform_cpa(keys, traces, challenges, intermediate, key, False)
    guess = [get_float(0, 1024 + i, guess << (52 - PRECISION)) for i in range(-12, 8)]
    if verbose:
        print("first guess:", guess)

    return guess


def recover_exponent(keys, traces, challenges, verbose, plot, key):
    def intermediate(op, key):
        s, e, m = decompose(op * key)
        return HW[e-1]

    start = 0 # POI: change if needed
    end = -1 # POI: change if needed
    traces = np.array([t[start:end] for t in traces], dtype=np.float64)

    guess = perform_cpa(keys, traces, challenges, intermediate, key, False)
    if verbose:
        print("final guess:", guess)
    return guess


def recover_sign(guess, traces, challenges, verbose, plot):
    traces1 = []
    traces0 = []
    nb_challenges = len(challenges)
    start = 395 # POI: change if needed
    end = -1 # POI: change if needed

    for j in range (nb_challenges):
        op = challenges[j]
        res = op*guess

        if (res < 0):
            traces1.append(traces[j][start:end])
        else:
            traces0.append(traces[j][start:end])

    mean0 = np.mean(traces0, axis=0)
    mean1 = np.mean(traces1, axis=0)
    diff = list(map(operator.sub, mean0, mean1))
    if (max(diff[:]) >= abs(min(diff[:]))):
        guess = -guess
    return(guess)

def run_sca(nb_tests, nb_traces, file, verbose, plot, all_data, detect_error):

    success = 0
    nb_cpu = os.cpu_count()

    test_sets = [elem for elem in file]

    for t in range(nb_tests):
        challenges = []
        traces = []

        key_group = file[test_sets[t]]
        key = list(key_group.attrs["key"])
        LOGN = key_group.attrs["logn"]
        DIM = 1 << LOGN
        HALF = DIM >> 1

        datasets = [elem for elem in key_group]
        for elem in datasets[:nb_traces]:
            dataset = key_group[elem][:,]
            traces.append(dataset)
            challenges.append(key_group[elem].attrs["challenge"])

        del datasets

        print("key:\t", key)
        key_fft = key[:]
        FFT(key_fft, LOGN)

        offset = 85 # this offset has to be set manually
        points_per_mul = 445 # this has to be set manually
        pattern = np.mean([t[offset:offset+points_per_mul] for t in traces], axis=0)
    
        indexes = find_all_indexes(traces, pattern, DIM, False)

        '''Uncomment to check if pattern matching is correct.
        If not, change offset and points_per_mul. (+- 20) '''

        # for t in traces[:10]:
        #     plt.plot(t)
        # for i in indexes:
        #     plt.axvline(x=i, color='r')
        # plt.show()

        guess = [0]*DIM
        second_guess = [0]*DIM

        for i in range(0, HALF):
            partial_traces = np.array([t[indexes[4*i] : indexes[4*i] + points_per_mul] for t in traces])
            partial_challenges = np.array([row[i] for row in challenges])
    
            if all_data: # add 4th mul pattern to the 1st
                partial_traces = np.concatenate([partial_traces, [t[indexes[4*i+3] : indexes[4*i+3] + points_per_mul] for t in traces]])
                partial_challenges = np.concatenate([partial_challenges, [row[HALF + i] for row in challenges]])
            
            new_traces, new_challenges = remove_noise(partial_traces, partial_challenges)
            recovered = recover_mantissa(new_traces, new_challenges, False, plot, key_fft[i])
            recovered = recover_exponent(recovered,new_traces,new_challenges, False,True, key_fft[i])
            guess[i] = recover_sign(recovered, partial_traces, partial_challenges, False, plot)
            if (verbose):
                print("guess: {}\tkey: {}".format(guess[i], key_fft[i]))

            partial_traces = np.array([t[indexes[4*i+1] : indexes[4*i+1]+points_per_mul] for t in traces])
            partial_challenges = np.array([row[HALF + i] for row in challenges])
    
            if all_data: # add 3rd mul pattern to the second
                partial_traces = np.concatenate([partial_traces, [t[indexes[4*i+2] : indexes[4*i+2] + points_per_mul] for t in traces]])
                partial_challenges = np.concatenate([partial_challenges, [row[i] for row in challenges]])

            new_traces, new_challenges = remove_noise(partial_traces, partial_challenges)
            recovered = recover_mantissa(new_traces, new_challenges, False, plot, key_fft[HALF + i])
            recovered = recover_exponent(recovered,new_traces,new_challenges, False,True, key_fft[i])
            guess[HALF + i] = recover_sign(recovered, partial_traces, partial_challenges, False, plot)
            if (verbose):
                print("guess: {}\tkey: {}".format(guess[HALF + i], key_fft[HALF + i]))

            if (detect_error):
                partial_traces = np.array([t[indexes[4*i+2] : indexes[4*i+2] + points_per_mul] for t in traces])
                partial_challenges = np.array([row[i] for row in challenges])
                recovered = recover_mantissa(partial_traces, partial_challenges, False, plot, key_fft[HALF + i])
                recovered = recover_exponent(recovered,partial_traces,partial_challenges, False,True, key_fft[HALF + i])
                second_guess[HALF + i] = recover_sign(recovered, partial_traces, partial_challenges, False, plot)
                if (verbose):
                    print("second guess: {}\tkey: {}".format(second_guess[HALF + i], key_fft[HALF + i]))

                partial_traces = np.array([t[indexes[4*i+3] : indexes[4*i+3] + points_per_mul] for t in traces])
                partial_challenges = np.array([row[HALF + i] for row in challenges])
                recovered = recover_mantissa(partial_traces, partial_challenges, False, plot, key_fft[i])
                recovered = recover_exponent(recovered,partial_traces,partial_challenges, False,True, key_fft[i])
                second_guess[i] = recover_sign(recovered, partial_traces, partial_challenges, False, plot)
                if (verbose):
                    print("second guess: {}\tkey: {}".format(second_guess[i], key_fft[i]))

        if (detect_error):
            for i in range(DIM):
                if (guess[i] != second_guess[i]):
                    print("mismatch at index {}: {} {} {}".format(i, guess[i], second_guess[i], key_fft[i]))

        iFFT(guess, LOGN)
        guess = [round(e) for e in guess]
        print("key:\t", key)
        print("guess:\t", guess)
        if (key == guess):
            success += 1

        # if (t%10 == 9):
        #     print("nb tests:", t+1)
        #     print("nb success:", success)

    print("nb tests:", nb_tests)
    print("nb success:", success)

def usage(exe):
    opt = {"-h --help": "display this summary",
        "--nb-tests=<value>": "number of tests to run on the traces",
        "--nb-traces=<value>": "number of traces to use for each test",
        "--input-file=<file>": "file where the traces are stored",
        "-v --verbose": "run the attack in verbose mode",
        "-a --all": "use all available multiplication patterns"
        }
    print("usage:", exe, "[options]")
    print("Options:")
    for elem in opt:
        print(f' {elem:30} {opt[elem]}')

def main():
    argv = sys.argv[1:]
    nb_tests = 1
    nb_traces = 1
    input_file = "traces.hdf5"
    verbose = False
    plot = False
    all_data = False
    detect_error = False

    if len(argv) > 0:
        try:
            opts, args = getopt.getopt(
                argv, "vpha", ["nb-tests=", "nb-traces=", "input-file=", "help", "all", "detect"]
            )
        except getopt.GetoptError as err:
            print(err)
            usage(sys.argv[0])
            sys.exit(2)
        for o, a in opts:
            if o == "--nb-tests":
                nb_tests = int(a)
            elif o == "--nb-traces":
                nb_traces = int(a)
            elif o == "--input-file":
                input_file = a
            elif o in ["-v", '--verbose']:
                verbose = True
            elif o == "-p":
                plot = True
            elif o in ['-h', '--help']:
                usage(sys.argv[0])
                sys.exit(2)
            elif o in ['-a', "--all"]:
                all_data = True
            elif o == "--detect":
                detect_error = True
            elif o == "--noise":
                noise = float(a)


    else:
        print("Enter number of tests:")
        nb_tests = int(input())
        print("Enter number of traces:")
        nb_traces = int(input())
        print("Enter input file:")
        input_file = input()

    file = h5py.File(input_file, "r")
    test_sets = [elem for elem in file]
    assert nb_tests <= len(test_sets)
    assert nb_traces <= min([len(file[elem]) for elem in test_sets])
    run_sca(nb_tests, nb_traces, file, verbose, plot, all_data, detect_error)


if __name__ == "__main__":
    main()
