from fft_constants import fpr_gm_tab, fpr_p2_tab


def FPC_ADD(a_re, a_im, b_re, b_im):
	return (a_re + b_re, a_im + b_im)


def FPC_SUB(a_re, a_im, b_re, b_im):
	return (a_re - b_re, a_im - b_im)


def FPC_MUL(a_re, a_im, b_re, b_im):
	return (a_re * b_re - a_im * b_im, a_re * b_im + a_im * b_re)


def iFFT(f, logn):
	n = 1 << logn
	t = 1
	m = n
	hn = n >> 1
	for u in range(logn, 1, -1):
		hm = m >> 1
		dt = t << 1

		i1 = 0
		j1 = 0
		while j1 < hn:
			j2 = j1 + t

			s_re = fpr_gm_tab[((hm + i1) << 1) + 0]
			s_im = -fpr_gm_tab[((hm + i1) << 1) + 1]
			for j in range(j1, j2):
				x_re = f[j]
				x_im = f[j + hn]
				y_re = f[j + t]
				y_im = f[j + t + hn]
				f[j], f[j + hn] = FPC_ADD(x_re, x_im, y_re, y_im)
				x_re, x_im = FPC_SUB(x_re, x_im, y_re, y_im)
				f[j + t], f[j + t + hn] = FPC_MUL(x_re, x_im, s_re, s_im)

			i1 += 1
			j1 += dt

		t = dt
		m = hm

	if logn > 0:
		ni = fpr_p2_tab[logn]
		for u in range(0, n):
			f[u] = f[u] * ni


def FFT(f, logn):
	n = 1 << logn
	hn = n >> 1
	t = hn

	u = 1
	m = 2
	while u < logn:
		ht = t >> 1
		hm = m >> 1

		i1 = 0
		j1 = 0
		while i1 < hm:
			j2 = j1 + ht
			s_re = fpr_gm_tab[((m + i1) << 1) + 0]
			s_im = fpr_gm_tab[((m + i1) << 1) + 1]

			for j in range(j1, j2):
				x_re = f[j]
				x_im = f[j + hn]
				y_re = f[j + ht]
				y_im = f[j + ht + hn]
				y_re, y_im = FPC_MUL(y_re, y_im, s_re, s_im)
				f[j], f[j + hn] = FPC_ADD(x_re, x_im, y_re, y_im)
				f[j + ht], f[j + ht + hn] = FPC_SUB(x_re, x_im, y_re, y_im)

			i1 += 1
			j1 += t

		t = ht

		u += 1
		m <<= 1
