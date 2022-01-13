from random import randint, uniform
import numpy as np
from ctypes import *
from multiprocessing import Process, connection, Manager, Event, sharedctypes
import gc

def gradient(V, w):
    tmp = np.zeros(len(w))
    for i in range(len(V)):
        tmp += (np.inner(V[i],w))**3*V[i]

    return 4*tmp/len(V)

def moment(V,w):
    tmp = 0
    for i in range(len(V)):
        tmp += (np.inner(V[i],w))**4

    return tmp / len(V)

def hypercube(points, d, max_desc):
    w = np.array([uniform(-1,1) for _ in range(len(points[0]))])
    w = w / np.linalg.norm(w)
    descent = 0

    while (True):
        descent += 1
        g = gradient(points, w)
        w_new = w - d*g 
        w_new = w_new / np.linalg.norm(w_new)
        if moment(points, w_new) >= moment(points, w) or descent > max_desc:
            print("descent:", descent)
            return w
        else:
            w = w_new

def hypercube_c(points, n, d, max_desc, list_vectors, quit, average):
    nb_sigs = len(points)
    lib = cdll.LoadLibrary("./hidden.so")
    lib.hypercube.restype = POINTER(c_double)
    grad = (c_double)(d)

    res = None
    while not res:
        res = lib.hypercube(points, n, nb_sigs, grad, randint(0,1000), max_desc, average)
        if quit.is_set():
            return
    list_vectors.append(np.array([res[i] for i in range(n)]))


def parallelepiped(points, average, max_desc=100, nb_cpu=2):
    nb_sigs = len(points)
    n = len(points[0])
    G = np.cov(points.T)*3

    G_inv = np.linalg.inv(G)
    L = np.linalg.cholesky(G_inv)

    double_P = POINTER(c_double)
    pointer_array = sharedctypes.RawArray(double_P, nb_sigs)
    for i in range(len(points)):
        pointer_array[i] = (c_double * n)(*np.dot(points[i],L))

    average = sharedctypes.RawArray(c_double, average)
    manager = Manager()
    quit = Event()
    list_vectors = manager.list()

    lib = cdll.LoadLibrary("./hidden.so")
    lib.hypercube.restype = double_P

    del points
    gc.collect()

    pool = [Process(target=hypercube_c, args=(pointer_array, n, 0.7, max_desc, list_vectors, quit, average)) for _ in range(nb_cpu)]
    for p in pool:
        p.start()
    
    connection.wait(p.sentinel for p in pool)
    quit.set()

    c = list(list_vectors)[0]
    L_inv = np.linalg.inv(L)
    # v = np.dot(c*2, L_inv)
    v = np.dot(c, L_inv)

    return v
