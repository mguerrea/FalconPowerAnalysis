#include "hidden.h"

static double **covariance_matrix(double **points, int n, int nb_points)
{
	double **G = malloc(sizeof(double *) * n);
	double *means = calloc(n, sizeof(double));

	for (int i = 0; i < nb_points; i++)
		for (int j = 0; j < n; j++)
			means[j] += points[i][j];

	for (int i = 0; i < n; i++)
		means[i] = means[i] / nb_points;

	for (int i = 0; i < n; i++)
	{
		G[i] = calloc(n, sizeof(double));
		for (int j = 0; j < n; j++)
		{
			for (int k = 0; k < nb_points; k++)
				G[i][j] += (points[k][i] - means[i]) * (points[k][j] - means[j]);

			G[i][j] = G[i][j] / (nb_points - 1);
		}
	}
	free(means);
	return G;
}

static int LUPDecompose(double **A, int N, double Tol, int *P)
{

	int i, j, k, imax;
	double maxA, *ptr, absA;

	for (i = 0; i <= N; i++)
		P[i] = i; //Unit permutation matrix, P[N] initialized with N

	for (i = 0; i < N; i++)
	{
		maxA = 0.0;
		imax = i;

		for (k = i; k < N; k++)
			if ((absA = fabs(A[k][i])) > maxA)
			{
				maxA = absA;
				imax = k;
			}
		if (maxA < Tol)
			return 0; //failure, matrix is degenerate

		if (imax != i)
		{
			j = P[i];
			P[i] = P[imax];
			P[imax] = j;
			ptr = A[i];
			A[i] = A[imax];
			A[imax] = ptr;
			P[N]++;
		}

		for (j = i + 1; j < N; j++)
		{
			A[j][i] /= A[i][i];

			for (k = i + 1; k < N; k++)
				A[j][k] -= A[j][i] * A[i][k];
		}
	}

	return 1; //decomposition done
}

static double **invert_matrix(double **A, int N)
{
	int *P = calloc(N + 1, sizeof(int));
	double **IA = malloc(sizeof(double *) * N);

	LUPDecompose(A, N, 0.000000001, P);

	for (int i = 0; i < N; i++)
		IA[i] = calloc(N, sizeof(double));

	for (int j = 0; j < N; j++)
	{
		for (int i = 0; i < N; i++)
		{
			IA[i][j] = P[i] == j ? 1.0 : 0.0;

			for (int k = 0; k < i; k++)
				IA[i][j] -= A[i][k] * IA[k][j];
		}

		for (int i = N - 1; i >= 0; i--)
		{
			for (int k = i + 1; k < N; k++)
				IA[i][j] -= A[i][k] * IA[k][j];

			IA[i][j] /= A[i][i];
		}
	}
	free(P);
	return IA;
}

static void gradient(double **points, double *w, int nb_points, int n, double *res)
{
	// memset(res, 0, n*sizeof(double));
	for (int i = 0; i < n; i++)
		res[i] = 0;

	for (int i = 0; i < nb_points; i++)
	{
		double tmp = inner_product(points[i], w, n);
		tmp = pow(tmp, 3);
		for (int j = 0; j < n; j++)
			res[j] += tmp * points[i][j];
	}
	for (int i = 0; i < n; i++)
		res[i] = 4 * res[i] / nb_points;
}

double moment(double **points, double *w, int nb_points, int n)
{
	double res = 0;
	for (int i = 0; i < nb_points; i++)
	{
		double inner = inner_product(points[i], w, n);
		res += pow(inner, 4);
	}
	return res / nb_points;
}

double *hypercube(double **points, int n, int nb_points, double d, int seed, int max_desc, double *average)
{
	double g[n], *w, w_new[n];
	w = calloc(n, sizeof(double));
	srand(seed);

	// while (1)
	// {
		double norm = 0;
		int descent = 0;

		// printf("average = %x\n", average);
		for (int i = 0; i < n; i++)
		{
			if (average[i] == 0)
				w[i] = ((float)rand() / (float)(RAND_MAX)) * 2 - 1;
			else
				w[i] = average[i];
			norm += w[i] * w[i];
		}
		norm = sqrt(norm);
		for (int i = 0; i < n; i++)
			w[i] = w[i] / norm;

		while (1)
		{
			descent += 1;
			gradient(points, w, nb_points, n, g);
			norm = 0;
			for (int i = 0; i < n; i++)
			{
				w_new[i] = w[i] - d * g[i];
				norm += w_new[i] * w_new[i];
			}
			norm = sqrt(norm);
			for (int i = 0; i < n; i++)
				w_new[i] = w_new[i] / norm;
			if (moment(points, w_new, nb_points, n) >= moment(points, w, nb_points, n))
			{
				printf("descent = %d\n", descent);
				return w;
			}
			else if (descent > max_desc && average[0] == 0)
			{
				free(w);
				return NULL;
			}
			else
				memcpy(w, w_new, sizeof(double) * n);
		}
	// }
}

double *parallelepiped(double **points, int n, int nb_points, int seed, int max_desc)
{
	double **G, **G_inv, **L, **L_inv, **new_points, *c, *v;

	G = covariance_matrix(points, n, nb_points);
	for (int i = 0; i < n; i++)
		for (int j = 0; j < n; j++)
			// 		G[i][j] = 3*G[i][j];
			G[i][j] = 4 * G[i][j];
	G_inv = invert_matrix(G, n);
	free_matrix(G, n);
	L = cholesky(G_inv, n);
	free_matrix(G_inv, n);

	new_points = malloc(sizeof(double *) * nb_points);
	for (int i = 0; i < nb_points; i++)
		new_points[i] = vec_mat_product(points[i], L, n);

	c = hypercube(new_points, n, nb_points, 0.7, seed, max_desc, NULL);
	// for (int i = 0; i < n; i++)
	// 	c[i] = c[i] * 2;
	L_inv = invert_matrix(L, n);
	free_matrix(L, n);
	v = vec_mat_product(c, L_inv, n);
	free_matrix(L_inv, n);
	return (v);
}
