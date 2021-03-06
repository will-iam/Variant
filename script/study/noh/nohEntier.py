"""
based on https://github.com/gandalfcode/gandalf/blob/master/analysis/analytical.py
"""
from scipy.special import gamma as Gamma
from numpy import float64, pi, zeros, ones, sqrt, linspace, array

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
 
    X = linspace(0.0,radius,max(Nx,Ny))
    Y = linspace(0.0,radius,max(Nx,Ny))
    r=array([sqrt(X[i]**2+Y[i]**2)/sqrt(2.0) for i in range(max(Nx,Ny))])
    rho = zeros(npts, dtype=float)
    p = zeros(npts, dtype=float)
    u = zeros(npts, dtype=float)
    e = zeros(npts, dtype=float)
    if t > 0.0:
        u0=1.0
        rho0=1.0
        r_s = 1.0/2.0*(gamma-1.0)*t*u0
        inside = (r>1.0/2.0-r_s)*(r<1.0/2.0+r_s)
#        outside = (r<1.0/2.0-r_s)*(r>1.0/2.0+r_s)
        outside_gauche = r<1.0/2.0-r_s
        outside_droite = r>1.0/2.0+r_s
        rho[inside]=(gamma+1.0)**ndim/(gamma-1.0)**ndim*rho0
        p[inside]=(gamma+1.0)**ndim/(gamma-1.0)**(ndim-1)*rho0*u0**2/2.0
        u[inside]=0.0
        e[inside]=u0**2/2.0
        rho[outside_gauche]=rho0*(1.0-u0*t/(2*r[outside_gauche]-1.0))**(ndim-1)
        rho[outside_droite]=rho0*(1.0+u0*t/(2*r[outside_droite]-1.0))**(ndim-1)
        p[outside_gauche]=0.0
        p[outside_droite]=0.0
        u[outside_gauche]=-u0
        u[outside_droite]=-u0
        e[outside_gauche]=0.0
        e[outside_droite]=0.0

    return {'x':r, 'rho':rho, 'p':p, 'u':u, 'energy':e}


if __name__=='__main__':
    res = solve(1.0, 1.4, 3)
    for i in range(0,100):
        print(i, res['rho'][i])
    print(res['r_s'])
