### In this file is defined a Python class to manipulate the simualtion project.
###  - This class must be inherited from th class 'SimulationProject' (no need to import it)
###  - You can use the function "write(input_file, uint, nb_bits=16)"
###            to write an integer of 'nb_bits' bits in the 'input_file'.
### To get this simulation class in Python scripts, please use the functions in manage.py as
###  - search_simulations(repository)
###  - get_simulation(repository='.', classname=None)

class Falcon(SimulationProject):
    LOGN = 3
    DIM = 1 << LOGN
    @classmethod
    def get_binary_path(cl):
        return 'project.bin'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_input(self, input):
        """ Write into the 'input' file of ELMO tool
                the parameters and the challenges for the simulation """
        super().set_input(input)

    def write_float(self, input, nb: float):
        import numpy as np

        n = np.abs(nb).view(np.int64)
        negative = (nb < 0)*1
        exponent = (n >> 52) & 0x7ff
        significand = (n & np.int64((1 << 52) - 1))
      
        x = np.int64(negative) << 63 | exponent << 52 | significand
        for i in range(8):
            tmp = int(x >> (56-i*8)) & 0xff
            write(input, tmp, 8)

    def parse_float(self, b0, b1, b2, b3, b4, b5, b6, b7):
        import numpy as np
        x = b0 << 56 | b1 << 48 | b2 << 40 | b3 << 32 | b4 << 24 | b5 << 16 | b6 << 8 | b7 
        n = np.abs(x).view(np.int64)
        s = x >> 63
        e = (n >> 52) & 0x7ff
        m = (n & np.int64((1 << 52) - 1))  | np.int64(1 << 52)
        return ((-1)**s*2.0**(e-1023-52)*m)
    
    def set_input_for_each_challenge(self, input, challenge):
        """ Write into the 'input' file of ELMO tool
                the 'challenge' for the simulation """
        for i in range(self.DIM):
            self.write_float(input, float(challenge[i]))

    def get_test_challenges(self, nb_challenges):
        return [float(i) for i in range(0, nb_challenges)]

    def get_random_challenges(self, nb_challenges=5):
        from random import uniform
        return [[uniform(-512, 512) for i in range(self.DIM) ] for _ in range(nb_challenges)]

    def get_traces(self):
        from decimal import Decimal
        nb_traces = self.get_number_of_traces()

        # Load the power traces
        if self._complete_results is None:
            self._complete_results = []
            for filename in self.get_results_filenames():
                with open(filename, 'r') as _file:
                    # nb = [Decimal(e) for e in _file.readlines()]
                    nb = [e for e in _file.readlines()]
                    self._complete_results.append(nb)
        return self._complete_results
