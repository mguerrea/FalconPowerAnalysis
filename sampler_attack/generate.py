import sys
sys.path.insert(0, './falcon')

from falcon import SecretKey
from scripts.sign_KAT import sign_KAT2
from tqdm import trange
import numpy as np
import h5py, getopt, string
from random import gauss, choices

def print_infos(input_file):
    file = h5py.File(input_file, 'r')
    test_sets = [elem for elem in file]
    
    sigs = list(file[test_sets[0]].keys())
    print("Number of sets in file:", len(test_sets))
    print("Number of signatures in each set:", [len(file[elem]) for elem in test_sets])
    print("Dimension:", [1 << file[elem].attrs["logn"] for elem in test_sets])
    print("Data type:", type(file[test_sets[0]][sigs[0]][:,]), type(file[test_sets[0]][sigs[0]][:,][0])) 

    file.close()

def generate_signatures(nb_sets, nb_sigs, input_file, verbose, logn, expand, data_type):

    n = 1 << logn
    msg = b'test'

    file = h5py.File(input_file, "a")
    if expand:
        test_sets = [elem for elem in file]
    for t in range(nb_sets):

        if expand and t < len(test_sets):
            key_group = file[test_sets[t]]
            poly = list(key_group.attrs["key"])
            key = SecretKey(n, poly)
            offset = len(key_group)
        
        else:
            key = SecretKey(n)
            poly = [key.f, key.g, key.F, key.G]
            key_group = file.create_group(''.join(choices(string.ascii_uppercase + string.digits, k=8)))
            key_group.attrs.create("key", poly)
            key_group.attrs.create("logn", logn)
            offset = 0

        print(key)
    
        for i in trange(nb_sigs - offset):
            sig, alea = key.sign(msg)

            dataset = key_group.create_dataset(name=str(i + offset), data=sig[0]+sig[1], dtype=data_type)
            dataset.attrs.create("alea", alea, dtype=np.int8)

    file.close()

def usage(exe):
    opt = {"-h --help": "display this summary",
        "--nb-sets val": "number of sets to generate",
        "--nb-sigs val": "number of signatures to generate for each set",
        "--file file": "file where the signatures are stored",
        "-v --verbose": "run the generator in verbose mode",
        "--info": "display information about the file",
        "--expand" : "expand sets up to nb-sig",
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
    nb_sigs = 1000
    input_file = 'sig.hdf5'
    verbose = False
    info = False
    expand = False
    data_type = None

    if (len(argv) > 0):
        try:
            opts, args = getopt.getopt(argv, 'vh:', ["nb-sets=", "nb-sigs=", "file=", "info", "logn=", "expand", "help", "type="])
        except getopt.GetoptError as err:
            print(err)
            usage(sys.argv[0])
            sys.exit(2)
        for o, a in opts:
            if o == "--nb-sets":
                nb_sets = int(a)
            elif o == "--nb-sigs":
                nb_sigs = int(a)
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
            elif o in ["-h", "--help"]:
                usage(sys.argv[0])
                sys.exit(2)
            elif o == "--type":
                data_type=a

    if (info):
        print_infos(input_file)
    else:
        generate_signatures(nb_sets, nb_sigs, input_file, verbose, logn, expand, data_type)

if __name__ == "__main__":
    main()
    