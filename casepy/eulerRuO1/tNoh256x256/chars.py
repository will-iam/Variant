import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '../../../'))
import script.rio as io
#import script.initial_condition.noh2D as noh2D
import numpy as np
from decimal import Decimal
from math import sqrt, sin

# Domain properties
lx = 1.0
ly = 1.0

Nx = 256
Ny = 256

# Scheme execution options
T = 0.6
CFL = 0.5

gamma = 5./3.
BClayer = 1

quantityList = ['rho', 'rhou_x', 'rhou_y', 'rhoE']
def buildme(quantityDict, coords_to_uid, coords_to_bc):
    # ------------------------------------------------------------------------------
    # Domain properties
    # ------------------------------------------------------------------------------
    dx = lx / Nx
    dy = ly / Ny

    # ------------------------------------------------------------------------------
    # rho initial state
    # ------------------------------------------------------------------------------
    rho_uid_to_val = np.zeros((Nx*Ny), dtype = np.dtype(Decimal))
    rhou_x_uid_to_val = np.zeros((Nx*Ny), dtype = np.dtype(Decimal))
    rhou_y_uid_to_val = np.zeros((Nx*Ny), dtype = np.dtype(Decimal))
    rhoE_uid_to_val = np.zeros((Nx*Ny), dtype = np.dtype(Decimal))

    u0=1.0
    rho0=1.0

    for i in range(Nx):
        for j in range(Ny):
            x = (i + 0.5) * dx
            y = (j + 0.5) * dy
            coords = coords_to_uid[(i, j)]
            rho_uid_to_val[coords] = 10**(-12)
            if (x+0.5*dx)**2 + (y+0.5*dy)**2 <= 1.0:
                #coords = coords_to_uid[(i, j)]
                rho_uid_to_val[coords] = rho0
                if i>0 or j>0:
                    rhou_x_uid_to_val[coords] = -u0*x/sqrt(x**2+y**2)*rho0
                    rhou_y_uid_to_val[coords] = -u0*y/sqrt(x**2+y**2)*rho0
                    rhoE_uid_to_val[coords] = 1.0/2.0*u0**2*rho0          #Kinetic energy at t=0

    # ------------------------------------------------------------------------------
    # Boundary conditions
    # ------------------------------------------------------------------------------
    # Start new uid after last domain cell
    for k in range(1, BClayer + 1):
        # Left border
        for j in range(-k, Ny - 1 + k):
            coords_to_bc[(-k, j)] = {'N': {"rho": 1, "rhoE": 1, "pressure": 1, "rhou_x": -1, "rhou_y": 1}}

        # Top border
        for i in range(-k, Nx - 1 + k):
            x=(i+1.0/2.0)*dx
            y=(Ny+1.0/2.0)*dy
            coords_to_bc[(i, Ny - 1 + k)] = {'T': {"rho": u0 / (lx + 0.5 * dx)}, 'D': {"rhoE": 1/2*u0**2*rho0, "pressure": 0,"rhou_x": -u0*x/sqrt(x**2+y**2)*rho0, "rhou_y": -u0*y/sqrt(x**2+y**2)*rho0}}
            #coords_to_bc[(i, Ny - 1 + k)] = {'D': {"rho": u0, "rhoE": 1/2*u0**2*rho0, "pressure": 0,"rhou_x": -u0*x/sqrt(x**2+y**2)*rho0, "rhou_y": -u0*y/sqrt(x**2+y**2)*rho0}}

        # Right border
        for j in range(Ny, -k, -1):
            x=(Nx+1.0/2.0)*dx
            y=(j+1.0/2.0)*dy
            coords_to_bc[(Nx - 1 + k, j)] = {'T': {"rho": u0 / (ly + 0.5 * dy)}, 'D': {"rhoE": 1/2*u0**2*rho0, "pressure": 0,"rhou_x": -u0*x/sqrt(x**2+y**2)*rho0, "rhou_y": -u0*y/sqrt(x**2+y**2)*rho0}}
            #coords_to_bc[(Nx - 1 + k, j)] = {'D': {"rho": u0, "rhoE": 1/2*u0**2*rho0, "pressure": 0,"rhou_x": -u0*x/sqrt(x**2+y**2)*rho0, "rhou_y": -u0*y/sqrt(x**2+y**2)*rho0}}

        # Bottom border
        for i in range(Nx, -k, -1):
            coords_to_bc[(i, -k)] = {'N': {"rho": 1, "rhoE": 1, "pressure": 1, "rhou_x": 1, "rhou_y": -1}}

    # ------------------------------------------------------------------------------
    # velocity states
    # ------------------------------------------------------------------------------

    # Add quantities to the quantity dictionary
    quantityDict['rho'] = rho_uid_to_val
    quantityDict['rhou_x'] = rhou_x_uid_to_val
    quantityDict['rhou_y'] = rhou_y_uid_to_val
    quantityDict['rhoE'] = rhoE_uid_to_val
