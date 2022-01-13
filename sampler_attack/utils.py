def shift(f, i):
    if i == 0:
        return f
    elif i < 0:
        new = f[-i:] + [-e for e in f[:-i]]
    else:
        new = [-e for e in f[-i:]] + f[:-i]
    return new

def F_Matrix(f):
    n = len(f)
    if n == 2:
        F = [[f[0], f[1]], [-f[1], f[0]]]
        return F
    else:
        f0 = [f[2 * i + 0] for i in range(n // 2)]
        f1 = [f[2 * i + 1] for i in range(n // 2)]
        F00 = F_Matrix(f0)
        F01 = F_Matrix(f1)
        F10 = F_Matrix(shift(f1, 1))
        F11 = F_Matrix(f0)

        F = [[c for c in F00[i]] + [c for c in F01[i]] for i in range(n//2)] + [[c for c in F10[i]] + [c for c in F11[i]] for i in range(n//2)]
        return F

def conjugate(f):
    return [f[0]] + [-f[i] for i in range(len(f) - 1, 0, -1)]

def permute(f):
    n = len(f)
    f0 = [f[2 * i + 0] for i in range(n // 2)]
    f1 = [f[2 * i + 1] for i in range(n // 2)]
    if n == 4:  
        return(f0+f1)
    else:
        f0 = permute(f0)
        f1 = permute(f1)
        return f0+f1

def split(f):
    n = len(f)
    f0 = [f[2 * i + 0] for i in range(n // 2)]
    f1 = [f[2 * i + 1] for i in range(n // 2)]
    return(f0,f1)
