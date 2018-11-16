#Main Sedov Code Module
#Ported to python from fortran code written by James R Kamm and F X Timmes
#Original Paper and code found at http://cococubed.asu.edu/papers/la-ur-07-2849.pdf

import numpy as np
from globalvars import comvars as gv
from sedov_1d import sed_1d
from matplotlib import pyplot as plt

gv.its = 10

# define sedov_main as a function
def sedov_main(geom_in, omega_in, time_in, blast_energy, gamma_in):
    ##Explicitly set variables
    ##Standard Cases
    ##Spherical constant density should reach r=1 at t=1
    nstep = 1024
    eblast = blast_energy
    gv.xgeom = geom_in
    gv.omega = omega_in

    ##input parameters
    time = time_in
    rho0 = 1.
    vel0 = 0.
    ener0 = 0.0
    pres0 = 0.0
    gv.gamma = gamma_in

    ##number of grid points, spatial domain, spatial stepsize.
    ##to match hydrocode output, use the mid-sell points.
    #zpos = array of spatial points
    zlo = 0.0
    zhi = 1.2
    zstep = (zhi - zlo)/float(nstep)
    zpos = np.arange(zlo + zstep, zhi + zstep, zstep)
    den, vel, pres, enertot, zpos = sed_1d(time, nstep, zpos, eblast, rho0, vel0, ener0, pres0, gv)

    #create final dictionary to pickle
    ###dictionary is a flexible array
    single_time_output = {'density': den, 'velocity': vel, 'pressure': pres,
                          'total_energy': enertot, 'position': zpos}

    zmax = 1.5 * gv.r2
    plt.plot(zpos, den)
    plt.axis([0,  zmax, 0, max(den)])
    plt.title('Density vs. Position')
    plt.ylabel('Density (kg/m^3)')
    plt.xlabel('Position (m)')
    plt.show()

    plt.plot(zpos, vel)
    plt.axis([0, zmax, 0, max(vel)])
    plt.title('Velocity vs. Position')
    plt.ylabel('Velocity (m/s)')
    plt.xlabel('Position (m)')
    plt.show()

    plt.plot(zpos, enertot)
    plt.axis([0,  zmax, 0, max(enertot)])
    plt.title('Total Energy vs. Position')
    plt.ylabel('Energy (J)')
    plt.xlabel('Position (m)')
    plt.show()

    '''
    plt.plot(zpos, pres)
    plt.axis([0,  zmax, 0, max(pres)])
    plt.title('Pressure vs. Position')
    plt.ylabel('Pressure (Pa)')
    plt.xlabel('Position (m)')
    plt.show()
    '''

def solve():
    # Planar 1.0, Cylindrical = 2.0, Spherical = 3.0
    sedov_main(2.0, 0.0, 1.0, 0.311357, 1.4)


solve()

