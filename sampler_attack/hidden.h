#ifndef HIDDEN_H
#define HIDDEN_H

#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <time.h>
#include <string.h>

double inner_product(double *u, double *v, int n);
double *vec_mat_product(double *v, double **M, int n);
void free_matrix(double **M, int row);
double **cholesky(double **matrix, int n);
void normalize(double *v, int n);

#endif
