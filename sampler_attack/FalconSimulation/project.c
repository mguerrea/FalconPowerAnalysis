#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>

#include "inner.h"
#include "falcon.h"

#include "elmoasmfunctionsdef-extension.h"

#define LOGN 4
#define DIM (1 << LOGN)

// #define FALCON_FPEMU

// ELMO API :
//  - printbyte(addr): Print single byte located at address 'addr' to output file;
//  - randbyte(addr): Load byte of random to memory address 'addr';
//  - readbyte(addr): Read byte from input file to address 'addr'.
// ELMO API (extension) :
//  - print2bytes, rand2bytes and read2bytes: idem, but for an address pointing on 2 bytes;
//  - print4bytes, rand4bytes and read4bytes: idem, but for an address pointing on 4 bytes.


static int masked_sampler(prng *p)
{
	static uint32_t dist[] = {
		10745844u,  3068844u,  3741698u,
		 5559083u,  1580863u,  8248194u,
		 2260429u, 13669192u,  2736639u,
		  708981u,  4421575u, 10046180u,
		  169348u,  7122675u,  4136815u,
		   30538u, 13063405u,  7650655u,
		    4132u, 14505003u,  7826148u,
		     417u, 16768101u, 11363290u,
		      31u,  8444042u,  8086568u,
		       1u, 12844466u,   265321u,
		       0u,  1232676u, 13644283u,
		       0u,    38047u,  9111839u,
		       0u,      870u,  6138264u,
		       0u,       14u, 12545723u,
		       0u,        0u,  3104126u,
		       0u,        0u,    28824u,
		       0u,        0u,      198u,
		       0u,        0u,        1u
	};

	uint32_t v0, v1, v2, hi;
	uint64_t lo;
	size_t u;
	int z;

	/*
	 * Get a random 72-bit value, into three 24-bit limbs v0..v2.
	 */
	lo = prng_get_u64(p);
	hi = prng_get_u8(p);
	v0 = (uint32_t)lo & 0xFFFFFF;
	v1 = (uint32_t)(lo >> 24) & 0xFFFFFF;
	v2 = (uint32_t)(lo >> 48) | (hi << 16);

	/*
	 * Sampled value is z, such that v0..v2 is lower than the first
	 * z elements of the table.
	 */
	z = 0;
	
	for (u = 0; u < (sizeof dist) / sizeof(dist[0]); u += 3) {
		uint32_t w0, w1, w2, cc;
		uint32_t mask = 0xffffff;
		
		starttrigger();
		w0 = dist[u + 2];
		w1 = dist[u + 1];
		w2 = dist[u + 0];
		
		cc = (v0 - w0) >> 31;
		cc = (v1 - w1 - cc) >> 31;
		
		
		mask = mask - v2 + w2 + cc;
		mask >>= 24;
		
		
		z += (int)mask;

		endtrigger();
	}
	return z;
}

static int sampler(prng *p)
{
	static uint32_t dist[] = {
		10745844u,  3068844u,  3741698u,
		 5559083u,  1580863u,  8248194u,
		 2260429u, 13669192u,  2736639u,
		  708981u,  4421575u, 10046180u,
		  169348u,  7122675u,  4136815u,
		   30538u, 13063405u,  7650655u,
		    4132u, 14505003u,  7826148u,
		     417u, 16768101u, 11363290u,
		      31u,  8444042u,  8086568u,
		       1u, 12844466u,   265321u,
		       0u,  1232676u, 13644283u,
		       0u,    38047u,  9111839u,
		       0u,      870u,  6138264u,
		       0u,       14u, 12545723u,
		       0u,        0u,  3104126u,
		       0u,        0u,    28824u,
		       0u,        0u,      198u,
		       0u,        0u,        1u
	};

	uint32_t v0, v1, v2, hi;
	uint64_t lo;
	size_t u;
	int z;

	/*
	 * Get a random 72-bit value, into three 24-bit limbs v0..v2.
	 */
	lo = prng_get_u64(p);
	hi = prng_get_u8(p);
	v0 = (uint32_t)lo & 0xFFFFFF;
	v1 = (uint32_t)(lo >> 24) & 0xFFFFFF;
	v2 = (uint32_t)(lo >> 48) | (hi << 16);

	/*
	 * Sampled value is z, such that v0..v2 is lower than the first
	 * z elements of the table.
	 */
	z = 0;
	
	for (u = 0; u < (sizeof dist) / sizeof(dist[0]); u += 3) {
		uint32_t w0, w1, w2, cc;

		starttrigger();
		w0 = dist[u + 2];
		w1 = dist[u + 1];
		w2 = dist[u + 0];
		
		cc = (v0 - w0) >> 31;
		cc = (v1 - w1 - cc) >> 31;
		cc = (v2 - w2 - cc) >> 31;
		
		z += (int)cc;

		endtrigger();
	}
	return z;
}

int main(void)
{
	uint16_t num_challenge, nb_challenges;

	read2bytes(&nb_challenges);

	inner_shake256_context sc;
	prng p;
	int z0;
	uint8_t seed = 0;

	// randbyte(&seed);

	inner_shake256_init(&sc);
	inner_shake256_inject(&sc, &seed, 1);
	inner_shake256_flip(&sc);
	Zf(prng_init)(&p, &sc);

	for (num_challenge = 0; num_challenge < nb_challenges; num_challenge++)
	{
		// Set variables for the current challenge

		// starttrigger(); // To start a new trace
		// Do the leaking operations here...
		z0 = sampler(&p);

		// endtrigger(); // To end the current trace

		printbyte((uint8_t *)&z0);

	}
	endprogram(); // To indicate to ELMO that the simulation is finished

	return 0;
}
