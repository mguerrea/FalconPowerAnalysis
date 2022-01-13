#include "hidden.h"

double inner_product(double *u, double *v, int n)
{
    double res = 0;
    for (int i = 0; i < n; i++)
        res += u[i]*v[i];
    return res;
}

double *vec_mat_product(double *v, double **M, int n)
{
    double *res = calloc(n, sizeof(double));

    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            res[i] += v[j] * M[j][i];
    return res;
}

void free_matrix(double **M, int row)
{
    for (int i = 0; i < row; i++)
        free(M[i]);
    free(M);
}

double **cholesky(double **matrix, int n)
{
    double **lower = malloc(sizeof(double *) * n);

    for (int i = 0; i < n; i++) {
        lower[i] = calloc(n, sizeof(double));
        for (int j = 0; j <= i; j++) {
            int sum = 0;
 
            if (j == i) // summation for diagonals
            {
                for (int k = 0; k < j; k++)
                    sum += lower[j][k]*lower[j][k];
                lower[j][j] = sqrt(matrix[j][j] -
                                        sum);
            } else {
                for (int k = 0; k < j; k++)
                    sum += (lower[i][k] * lower[j][k]);
                lower[i][j] = (matrix[i][j] - sum) /
                                      lower[j][j];
            }
        }
    }
    return lower;
}

void normalize(double *v, int n)
{
    double norm = sqrt(inner_product(v,v,n));
    for (int i = 0; i < n; i++)
        v[i] = v[i] / norm;
}