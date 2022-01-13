import h5py, sys, getopt
from random import gauss, choices
import numpy as np
import string

def print_infos(input_file):
    file = h5py.File(input_file, 'r')
    test_sets = [elem for elem in file]
    
    traces = list(file[test_sets[0]].keys())
    print("Number of sets in file:", len(test_sets))
    print("Number of traces in each set:", [len(file[elem]) for elem in test_sets])
    print("Dimension:", [1 << file[elem].attrs["logn"] for elem in test_sets])
    print("Data type:", type(file[test_sets[0]][traces[0]][:,][0])) 
    ratio = [file[elem].attrs.get("ratio", 0) for elem in test_sets]
    print("Noise ratio:", ratio)

    file.close()

def remove_traces(nb_sets, nb_traces, input_file, verbose):
    file = h5py.File(input_file, 'a')
    test_sets = [elem for elem in file]

    while (nb_sets < len(file)):
        del file[test_sets[0]]
        del test_sets[0]
    for t in range(nb_sets):
        for i in range(nb_traces, len(file[test_sets[t]])):
            del file[test_sets[t]][str(i)]
    
    file.close()

def generate_traces(nb_sets, nb_traces, input_file, verbose, logn, expand):

    foldername = 'FalconSimulation'
    classname = 'Falcon'

    from elmo.manage import get_simulation
    simu = get_simulation(classname, foldername)
    simulation = simu()
    simulation.LOGN = logn
    simulation.DIM = 1 << logn

    file = h5py.File(input_file, "a")
    if expand:
        test_sets = [elem for elem in file]
    for t in range(nb_sets):
        nb_challenges = 5

        if expand and t < len(test_sets):
            key_group = file[test_sets[t]]
            key = list(key_group.attrs["key"])
            offset = len(key_group)
        
        else:
            key = [int(gauss(0, 4)) for _ in range(simulation.DIM)]
            key_group = file.create_group(''.join(choices(string.ascii_uppercase + string.digits, k=8)))
            key_group.attrs.create("key", key)
            key_group.attrs.create("logn", logn)
            offset = 0

        print(key)
        traces = []
    
        rep = (nb_traces - offset) // nb_challenges
        for i in range(rep):
            challenges = simulation.get_random_challenges(nb_challenges)
            simulation.set_challenges([key] + challenges)
            simulation.run()
            traces = simulation.get_traces()
            new = np.array(traces, dtype=np.float64)

            for j in range(len(traces)):
                dataset = key_group.create_dataset(name=str(i*nb_challenges + j + offset), data=new[j])
                dataset.attrs.create("challenge", challenges[j])
            
            if verbose and i*nb_challenges % 100 == 0:
                print("Progression:", i * nb_challenges, nb_traces - offset)

    file.close()

def usage(exe):
    opt = {"-h --help": "display this summary",
        "--nb-sets val": "number of sets to generate",
        "--nb-traces val": "number of traces to generate for each set",
        "--file file": "file where the traces are stored",
        "-v --verbose": "run the generator in verbose mode",
        "--info": "display information about the file",
        "--remove": "reduce sets down to nb-traces",
        "--expand" : "expand sets up to nb-traces",
        "--logn": "dimension of key and challenges"
        }
    print("usage:", exe, "[options]")
    print("Options:")
    for elem in opt:
        print(f' {elem:20} {opt[elem]}')

def main():
    argv = sys.argv[1:]
    logn = 4
    nb_sets = 1
    nb_traces = 1000
    input_file = 'traces.hdf5'
    verbose = False
    info = False
    expand = False
    remove = False

    if (len(argv) > 0):
        try:
            opts, args = getopt.getopt(argv, 'vh:', ["nb-sets=", "nb-traces=", "file=", "info", "logn=", "expand", "remove", "help"])
        except getopt.GetoptError as err:
            print(err)
            usage(sys.argv[0])
            sys.exit(2)
        for o, a in opts:
            if o == "--nb-sets":
                nb_sets = int(a)
            elif o == "--nb-traces":
                nb_traces = int(a)
            elif o == "--file":
                input_file = a
            elif o == '-v':
                verbose = True
            elif o == "--info":
                info = True
            elif o == "--logn":
                logn = int(a)
            elif o == "--expand":
                expand = True
            elif o == "--remove":
                remove = True
            elif o in ["-h", "--help"]:
                usage(sys.argv[0])
                sys.exit(2)

    if (info):
        print_infos(input_file)
    elif (remove):
        remove_traces(nb_sets, nb_traces, input_file, verbose)
    else:
        generate_traces(nb_sets, nb_traces, input_file, verbose, logn, expand)

if __name__ == "__main__":
    main()
    
