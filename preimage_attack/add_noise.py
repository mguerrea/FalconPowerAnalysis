import getopt, sys, h5py
from random import gauss, choices
import string
from utils import add_noise
import numpy as np

def generate(file, ratio, output_file, expand, verbose):
    test_sets = [elem for elem in file]
    new_file = h5py.File(output_file, "a")
    nb_tests = len(test_sets)

    for t in range(nb_tests):
        key_group = file[test_sets[t]]
        key = list(key_group.attrs["key"])
        logn = key_group.attrs["logn"]

        if expand and test_sets[t] in new_file:
            new_key_group = new_file[test_sets[t]]
            offset = len(new_key_group)

        else:
            new_key_group = new_file.create_group(key_group.name)
            new_key_group.attrs.create("key", key)
            new_key_group.attrs.create("logn", logn)
            new_key_group.attrs.create("ratio", ratio)
            offset = 0

        print(key)
        i = 0
        datasets = [elem for elem in key_group]
        nb_traces = len(datasets)
        sigma = np.mean(key_group[datasets[0]][:,]) * ratio
        # print(sigma)
        for elem in datasets:
            i += 1
            if elem in new_key_group:
                continue
            dataset = key_group[elem]
            trace = dataset[:,]
            add_noise(trace, sigma)
            new_dataset = new_key_group.create_dataset(name=dataset.name, data=trace)
            new_dataset.attrs.create("challenge", dataset.attrs["challenge"])
            if verbose and i % 100 == 0:
                print("Progression:", i, nb_traces)
    
    file.close()
    new_file.close()


def main():
    argv = sys.argv[1:]
    input_file = "traces.hdf5"
    output_file = "noisy.hdf5"
    noise = 0.1
    expand = False
    verbose = False

    if len(argv) > 0:
        try:
            opts, args = getopt.getopt(argv, 'v:', ["input-file=", "output-file=", "noise=", "expand"])
        except getopt.GetoptError as err:
            print(err)
            sys.exit(2)
        for o, a in opts:
            if o == "--input-file":
                input_file = a
            elif o == "--output-file":
                output_file = a
            elif o == "--noise":
                noise = float(a)
            elif o == "--expand":
                expand = True
            elif o == '-v':
                verbose = True

    file = h5py.File(input_file, "r")
    generate(file, noise, output_file, expand, verbose)


if __name__ == "__main__":
    main()
