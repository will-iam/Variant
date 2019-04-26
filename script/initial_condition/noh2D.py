#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import numpy as np
from math import sqrt, sin
import sys
import os
from decimal import Decimal
sys.path.insert(1, os.path.join(sys.path[0], '../../../'))

def build(quantityDict, coords_to_uid, coords_to_bc, Nx, Ny, lx, ly, BClayer):

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
            rho_uid_to_val[coords] = rho0
            rhou_x_uid_to_val[coords] = -u0*x/sqrt(x**2+y**2)*rho0
            rhou_y_uid_to_val[coords] = -u0*y/sqrt(x**2+y**2)*rho0
            rhoE_uid_to_val[coords] = 0.5*rho0*u0**2          #Kinetic energy at t=0

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
            x = (i + 0.5) * dx
            y = (Ny + 0.5) * dy
            ir = 1. / np.sqrt(x**2 + y**2)
            # rho_exact = rho0 * (1 + t * u0 / r) => (rho0, u0 / r)
            # rhoE_exact = rho_exact * 0.5 * u0**2 = rho0 * (1 + t * u0 / r) * 0.5 * u0**2 => (rho0 * 0.5 * u0**2, u0 / r)
            # rhou_x_exact = -u0 * rho_exact * x / r = rho0 * (1 + t * u0 / r) * (-u0 * x / r) => (-u0 * rho0 * x / r, u0 / r)
            # rhou_y_exact = -u0 * rho_exact * y / r = rho0 * (1 + t * u0 / r) * (-u0 * y / r) => (-u0 * rho0 * y / r, u0 / r)
            coords_to_bc[(i, Ny - 1 + k)] = {
                'D': {"rho": rho0, "rhoE": 0.5 * rho0 * u0**2, "pressure": 0, "rhou_x": -u0 * rho0 * x * ir, "rhou_y": -u0 * rho0 * y * ir},
                'T': {"rho": u0 * ir, "rhoE": u0 * ir, "rhou_x": u0 * ir, "rhou_y": u0 * ir}
            }
            #coords_to_bc[(i, Ny - 1 + k)] = {'D': {"rho": u0, "rhoE": 1/2*u0**2*rho0, "pressure": 0,"rhou_x": -u0*x/sqrt(x**2+y**2)*rho0, "rhou_y": -u0*y/sqrt(x**2+y**2)*rho0}}

        # Right border
        for j in range(Ny, -k, -1):
            x = (Nx + 0.5) * dx
            y = (j + 0.5) * dy
            ir = 1. / np.sqrt(x**2 + y**2)
            coords_to_bc[(Nx - 1 + k, j)] = {
                'D': {"rho": rho0, "rhoE": 0.5 * rho0 * u0**2, "pressure": 0,"rhou_x": -u0 * rho0 * x * ir, "rhou_y": -u0 * rho0 * y * ir},
                'T': {"rho": u0 * ir, "rhoE": u0 * ir, "rhou_x": u0 * ir, "rhou_y": u0 * ir}
            }
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

