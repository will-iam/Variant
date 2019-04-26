"""
based on https://github.com/gandalfcode/gandalf/blob/master/analysis/analytical.py
"""
from scipy.special import gamma as Gamma
from numpy import float64, pi, zeros, ones, sqrt, linspace, array
from math import floor

def solve(t, gamma, ndim, npts, axis='x'):
    '''1, 2, 3 dimensions'''

    radius=1.0
    if ndim==1:
        if axis=='x':
            Nx=npts
            Ny=1
        if axis=='y':
            Nx=1
            Ny=npts
    if ndim==2:
        Nx=npts
        Ny=npts

    X = linspace(0.0,radius,npts)
    Y = linspace(0.0,radius,npts)
    if ndim == 1:
        r=array([sqrt((X[i]**2+Y[i]**2)/2) for i in range(npts)])
    if ndim == 2:
        r=array([sqrt((X[i]**2+Y[i]**2)/2) for i in range(npts)])
    rho = zeros(npts, dtype=float)
    p = zeros(npts, dtype=float)
    u = zeros(npts, dtype=float)
    e = zeros(npts, dtype=float)
    if t > 0.0:
        u0=1.0
        rho0=1.0
        r_s = 1.0/2.0*(gamma-1.0)*t*u0
        inside = r<r_s
        outside = (r>=r_s)
        rho[inside]=(gamma+1.0)**ndim/(gamma-1.0)**ndim*rho0
        p[inside]=(gamma+1.0)**ndim/(gamma-1.0)**(ndim-1.0)*rho0*u0**2/2.0
        u[inside]=0.0
        e[inside]=u0**2/2.0
        rho[outside]=rho0*(1.0+u0*t/r[outside])**(ndim-1.0)
        p[outside]=0.0
        u[outside]=-u0
        e[outside]=0.0

    return {'x':r, 'rho':rho, 'p':p, 'u':u, 'energy':e}


if __name__=='__main__':
    res = solve(1.0, 1.4, 3)
    for i in range(0,100):
        print(i, res['rho'][i])
    print(res['r_s'])
