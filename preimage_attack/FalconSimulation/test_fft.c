#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>

#include "inner.h"
#include "falcon.h"

static void *
xmalloc(size_t len)
{
	void *buf;

	if (len == 0) {
		return NULL;
	}
	buf = malloc(len);
	if (buf == NULL) {
		fprintf(stderr, "memory allocation error\n");
		exit(EXIT_FAILURE);
	}
	return buf;
}

static void
xfree(void *buf)
{
	if (buf != NULL) {
		free(buf);
	}
}

static void
mk_rand_poly(prng *p, fpr *f, unsigned logn)
{
	size_t u, n;

	n = (size_t)1 << logn;
	for (u = 0; u < n; u ++) {
		int32_t x;
		
		x = prng_get_u8(p);
		x = (x << 8) + prng_get_u8(p);
		x &= 0x3FF;
		f[u] = fpr_of(x - 512);
	}
}

static void
print_poly(fpr *f, unsigned logn)
{
	size_t u, n;

	n = (size_t)1 << logn;
	for (u = 0; u < n; u ++) {
        printf("%lf ", f[u]);
	}
    printf("\n");
}

static void
test_poly_inner(unsigned logn, uint8_t *tmp, size_t tlen)
{
	unsigned long ctr, num;
	inner_shake256_context rng;
	prng p;
	uint8_t xb;
	size_t n;

	printf("[%u]", logn);
	fflush(stdout);

	n = (size_t)1 << logn;
	if (tlen < 5 * n * sizeof(fpr)) {
		fprintf(stderr, "Insufficient buffer size\n");
		exit(EXIT_FAILURE);
	}
	inner_shake256_init(&rng);
	xb = logn;
	inner_shake256_inject(&rng, &xb, 1);
	inner_shake256_flip(&rng);
	Zf(prng_init)(&p, &rng);
	num = 131072UL >> logn;
    // num = 1024;
    // printf("num = %d\n", num);
	for (ctr = 0; ctr < num; ctr ++) {
		fpr *f, *g, *h;
		fpr *f0, *f1, *g0, *g1;
		size_t u;

		f = (fpr *)tmp;
		g = f + n;
		h = g + n;
		f0 = h + n;
		f1 = f0 + (n >> 1);
		g0 = f1 + (n >> 1);
		g1 = g0 + (n >> 1);
		mk_rand_poly(&p, f, logn);
        // print_poly(f, logn);
		memcpy(g, f, n * sizeof *f);
		Zf(FFT)(g, logn);
        // print_poly(g, logn);

        for (size_t i = 0; i < n; i++)
            g[i] = fpr_of(fpr_trunc(g[i]));

        // print_poly(g, logn);

		Zf(iFFT)(g, logn);

        for (size_t i = 0; i < n; i++)
            g[i] = fpr_of(roundl(g[i].v));

        // print_poly(g, logn);

		for (u = 0; u < n; u ++) {
			if (f[u].v != g[u].v) {
                // if (abs(fpr_rint(f[u]) - fpr_rint(g[u])) > 1)
				fprintf(stderr, "FFT/iFFT error: %f vs %f\n", f[u].v, g[u].v);
				// exit(EXIT_FAILURE);
			}
		}

		mk_rand_poly(&p, g, logn);
		for (u = 0; u < n; u ++) {
			h[u] = fpr_of(0);
		}
		for (u = 0; u < n; u ++) {
			size_t v;

			for (v = 0; v < n; v ++) {
				fpr s;
				size_t k;

				s = fpr_mul(f[u], g[v]);
				k = u + v;
				if (k >= n) {
					k -= n;
					s = fpr_neg(s);
				}
				h[k] = fpr_add(h[k], s);
			}
		}
		Zf(FFT)(f, logn);
        for (size_t i = 0; i < n; i++)
            f[i] = fpr_of(fpr_trunc(f[i]));
		Zf(FFT)(g, logn);
		Zf(poly_mul_fft)(f, g, logn);
		Zf(iFFT)(f, logn);
        for (size_t i = 0; i < n; i++)
            f[i] = fpr_of(roundl(f[i].v));
		for (u = 0; u < n; u ++) {
			if (fpr_rint(f[u]) != fpr_rint(h[u])) {
                if (abs(fpr_rint(f[u]) - fpr_rint(h[u])) > 2048|| abs(fpr_rint(h[u])) < 1024)
				fprintf(stderr, "FFT mul error:%f vs %f\n", f[u].v, h[u].v);
				// exit(EXIT_FAILURE);
			}
		}

		mk_rand_poly(&p, f, logn);
		memcpy(h, f, n * sizeof *f);
		Zf(FFT)(f, logn);
		Zf(poly_split_fft)(f0, f1, f, logn);

		memcpy(g0, f0, (n >> 1) * sizeof *f0);
		memcpy(g1, f1, (n >> 1) * sizeof *f1);
		Zf(iFFT)(g0, logn - 1);
		Zf(iFFT)(g1, logn - 1);
		for (u = 0; u < (n >> 1); u ++) {
			if (fpr_rint(g0[u]) != fpr_rint(h[(u << 1) + 0])
				|| fpr_rint(g1[u]) != fpr_rint(h[(u << 1) + 1]))
			{
				fprintf(stderr, "split error\n");
				exit(EXIT_FAILURE);
			}
		}

		Zf(poly_merge_fft)(g, f0, f1, logn);
		Zf(iFFT)(g, logn);
		for (u = 0; u < n; u ++) {
			if (fpr_rint(g[u]) != fpr_rint(h[u])) {
				fprintf(stderr, "split/merge error\n");
				exit(EXIT_FAILURE);
			}
		}

		if (((ctr + 1) & 0xFF) == 0) {
			printf(".");
			fflush(stdout);
		}
	}
}

static void
test_poly(void)
{
	unsigned logn = 2;
	uint8_t *tmp;
	size_t tlen;

	printf("Test polynomials: ");
	fflush(stdout);
	tlen = 40960;
	tmp = xmalloc(tlen);
	for (logn = 9; logn <= 10; logn ++) {
		test_poly_inner(logn, tmp, tlen);
	}
	xfree(tmp);
	printf(" done.\n");
	fflush(stdout);
}

int main()
{
	fpr f[] = {6, 13, 5, 6, 13, 17, 20, 17};
	Zf(FFT)(f, 3);
	print_poly(f, 3);
    // test_poly();
    return (0);
}