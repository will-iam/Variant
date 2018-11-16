"""
Peter Creasey
p.e.creasey.00@googlemail.com
solution to the Sedov problem
based on the C code by Aamer Haque
"""
from scipy.special import gamma as Gamma
from numpy import power, arange, empty, float64, log, exp, pi, diff, inner, outer, array, zeros, ones


def calc_a(g, nu=3):
    """ 
    exponents of the polynomials of the sedov solution
    g - the polytropic gamma
    nu - the dimension
    """
    a = [0]*8
   
    a[0] = 2.0 / (nu + 2)
    a[2] = (1-g) / (2*(g-1) + nu)
    a[3] = nu / (2*(g-1) + nu)
    a[5] = 2 / (g-2)
    a[6] = g / (2*(g-1) + nu)
   
    a[1] = (((nu+2)*g)/(2.0+nu*(g-1.0)) ) * ( (2.0*nu*(2.0-g))/(g*(nu+2.0)**2) - a[2])
    a[4] = a[1]*(nu+2) / (2-g)
    a[7] = (2 + nu*(g-1))*a[1]/(nu*(2-g))
    return a

def calc_beta(v, g, nu=3):
    """ 
    beta values for the sedov solution (coefficients of the polynomials of the similarity variables) 
    v - the similarity variable
    g - the polytropic gamma
    nu- the dimension
    """

    beta = (nu+2) * (g+1) * array((0.25, (g/(g-1))*0.5,
            -(2 + nu*(g-1))/2.0 / ((nu+2)*(g+1) -2*(2 + nu*(g-1))),
     -0.5/(g-1)), dtype=float64)

    beta = outer(beta, v)

    beta += (g+1) * array((0.0,  -1.0/(g-1),
                           (nu+2) / ((nu+2)*(g+1) -2.0*(2 + nu*(g-1))),
                           1.0/(g-1)), dtype=float64).reshape((4,1))

    return beta


def sedov(t, E0, rho0, g, n=1000, nu=3):
    """ 
    solve the sedov problem
    t - the time
    E0 - the initial energy
    rho0 - the initial density
    n - number of points
    nu - the dimension
    g - the polytropic gas gamma
    """

    # the similarity variable
    v_min = 2.0 / ((nu + 2) * g)
    v_max = 4.0 / ((nu + 2) * (g + 1))

    v = v_min + arange(n) * (v_max - v_min) / (n - 1)

    a = calc_a(g, nu)
    beta = calc_beta(v, g=g, nu=nu)
    lbeta = log(beta)
    
    r = exp(-a[0] * lbeta[0] - a[2] * lbeta[1] - a[1] * lbeta[2])
    rho = ((g + 1.0) / (g - 1.0)) * exp(a[3] * lbeta[1] + a[5] * lbeta[3] + a[4] * lbeta[2])
    p = exp(nu * a[0] * lbeta[0] + (a[5] + 1) * lbeta[3] + (a[4] - 2 * a[1]) * lbeta[2])
    u = beta[0] * r * 4.0 / ((g + 1) * (nu + 2))
    p *= 8.0 / ((g + 1) * (nu + 2) * (nu + 2))

    # we have to take extra care at v=v_min, since this can be a special point.
    # It is not a singularity, however, the gradients of our variables (wrt v) are.
    # r -> 0, u -> 0, rho -> 0, p-> constant

    u[0] = 0.0; rho[0] = 0.0; r[0] = 0.0; p[0] = p[1]

    # volume of an n-sphere
    vol = (pi ** (nu / 2.0) / Gamma(nu / 2.0 + 1)) * power(r, nu)


    # note we choose to evaluate the integral in this way because the
    # volumes of the first few elements (i.e near v=vmin) are shrinking 
    # very slowly, so we dramatically improve the error convergence by 
    # finding the volumes exactly. This is most important for the
    # pressure integral, as this is on the order of the volume.

    # (dimensionless) energy of the model solution
    de = rho * u * u * 0.5 + p / (g - 1)

    # integrate (trapezium rule)
    q = inner(de[1:] + de[:-1], diff(vol)) * 0.5

    # the factor to convert to this particular problem
    fac = (q * (t ** nu) * rho0 / E0) ** (-1.0 / (nu + 2))
    shock_speed = fac * (2.0 / (nu + 2))
    r_s = shock_speed * t * (nu + 2) / 2.0


    r *= fac * t
    u *= fac
    p *= fac * fac * rho0
    rho *= rho0



    return r, p, rho, u, r_s

def solve_raw(t, gamma, npts):
    r, p, rho, u, r_s = sedov(t, E0=0.244816, rho0=1, g=gamma, nu=2, n=npts)

    area = pi * r * r
    dv = area.copy()
    dv[1:] = diff(dv)

    te = p * dv / (gamma - 1.)
    ke = rho * u * u * 0.5 * dv
    energy = te + ke

    return {'rho': rho, 'u': u, 'energy': energy, 'x':r, 'r_s': r_s}

def solve(t, gamma, xpos):
    '''
    Solve with interpolation.
    '''
    rho_init = 1.0
    r, p, rho, u, r_s = sedov(t, E0=0.244816, rho0=rho_init, g=gamma, nu=2, n=len(xpos))

    area = pi * r * r
    dv = area.copy()
    dv[1:] = diff(dv)

    te = p * dv / (gamma - 1.)
    ke = rho * u * u * 0.5 * dv
    energy = te + ke

    # linear interpolation
    irho = ones(len(xpos)) * rho_init
    increment = 0
    last_value = rho[0]
    last_r = r[0]

    for i in range(len(xpos)):
        if xpos[i] > r_s:
            irho[i] = rho_init
            break

        while xpos[i] >= r[increment]:
            last_value = rho[increment]
            last_r = r[increment]
            increment = increment + 1

        dr = r[increment] - last_r
        v1 = last_value * (xpos[i] - last_r) / dr
        v2 = rho[increment] * (r[increment] - xpos[i]) / dr
        irho[i] = v1 + v2

    return {'rho': irho, 'u': u, 'energy': energy, 'x':r, 'r_s': r_s}


if __name__=='__main__':
    res = solve(1.0, 1.4, 100)
    for i in range(0,100):
        print i, res['x'][i], res['rho'][i]
    print res['r_s']
