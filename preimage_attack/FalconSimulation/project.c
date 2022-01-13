#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>

#include "inner.h"
#include "falcon.h"

#include "elmoasmfunctionsdef-extension.h"

#define LOGN 4 // change this before compilation
#define DIM (1 << LOGN)

// #define FALCON_FPEMU

// ELMO API :
//  - printbyte(addr): Print single byte located at address 'addr' to output file;
//  - randbyte(addr): Load byte of random to memory address 'addr';
//  - readbyte(addr): Read byte from input file to address 'addr'.
// ELMO API (extension) :
//  - print2bytes, rand2bytes and read2bytes: idem, but for an address pointing on 2 bytes;
//  - print4bytes, rand4bytes and read4bytes: idem, but for an address pointing on 4 bytes.

int main(void)
{
	uint16_t num_challenge, nb_challenges;
	uint64_t coeff;
	fpr f[DIM], h[DIM], r[DIM];

	read2bytes(&nb_challenges);

	for (int i = 0; i < DIM; i++)
	{
		read8bytes(&(h[i]));
	}

	Zf(FFT)(h, LOGN);

	for (num_challenge = 0; num_challenge < nb_challenges - 1; num_challenge++)
	{
		// Set variables for the current challenge
		for (int i = 0; i < DIM; i++)
		{
			read8bytes(&(f[i]));
		}

		starttrigger(); // To start a new trace
		// Do the leaking operations here...
		Zf(poly_mul_fft)(f, h, LOGN);

		endtrigger(); // To end the current trace

	}
	endprogram(); // To indicate to ELMO that the simulation is finished

	return 0;
}
