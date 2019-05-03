#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
import numpy as np
from math import sqrt, sin
import sys
import os
from decimal import Decimal
sys.path.insert(1, os.path.join(sys.path[0], '../../../'))
import script.rio as io
from chars import *

# ------------------------------------------------------------------------------
# Domain properties
# ------------------------------------------------------------------------------
dx = lx / Nx
dy = ly / Ny

coords_to_uid = io.gen_coords_to_uid(Nx, Ny)
coords_to_uid_bc = io.gen_coords_to_uid_bc(Nx, Ny, BClayer)

# Init quantities
quantityDict = dict()

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
        x=(i+1.0/2.0)*dx
        y=(j+1.0/2.0)*dy
        coords = coords_to_uid[(i, j)]
        rho_uid_to_val[coords] = rho0
        if i>0 or j>0:
            rhou_x_uid_to_val[coords] = -u0*x/sqrt(x**2+y**2)*rho0
            rhou_y_uid_to_val[coords] = -u0*y/sqrt(x**2+y**2)*rho0
            rhoE_uid_to_val[coords] = 1.0/2.0*u0**2*rho0          #Kinetic energy at t=0

# ------------------------------------------------------------------------------
# Boundary conditions
# ------------------------------------------------------------------------------
coords_to_bc = dict()
# Start new uid after last domain cell
for k in range(1, BClayer + 1):
    # Left border
    for j in range(-k, Ny - 1 + k):
        coords_to_bc[(-k, j)] = {BCtype: {"rho": 1, "rhoE": 1, "pressure": 1, "rhou_x": -1, "rhou_y": 1}}

    # Top border
    for i in range(-k, Nx - 1 + k):
        x=(i+1.0/2.0)*dx
        y=(Ny+1.0/2.0)*dy
        coords_to_bc[(i, Ny - 1 + k)] = {'D': {"rho": rho0, "rhoE": 1/2*u0**2*rho0, "pressure": 0,"rhou_x": -u0*x/sqrt(x**2+y**2)*rho0, "rhou_y": -u0*y/sqrt(x**2+y**2)*rho0}}

    # Right border
    for j in range(Ny, -k, -1):
        x=(Nx+1.0/2.0)*dx
        y=(j+1.0/2.0)*dy
        coords_to_bc[(Nx - 1 + k, j)] = {'D': {"rho": rho0, "rhoE": 1/2*u0**2*rho0, "pressure": 0,"rhou_x": -u0*x/sqrt(x**2+y**2)*rho0, "rhou_y": -u0*y/sqrt(x**2+y**2)*rho0}}

    # Bottom border
    for i in range(Nx, -k, -1):
        coords_to_bc[(i, -k)] = {BCtype: {"rho": 1, "rhoE": 1, "pressure": 1, "rhou_x": 1, "rhou_y": -1}}


# Merging uid and bc dictionaries
ds = [coords_to_uid_bc, coords_to_bc]
coords_to_uid_and_bc = dict()
for coord in coords_to_bc:
    coords_to_uid_and_bc[coord] = tuple(d.get(coord) for d in ds)


# ------------------------------------------------------------------------------
# velocity states
# ------------------------------------------------------------------------------

# Add quantities to the quantity dictionary



quantityDict['rho'] = rho_uid_to_val
quantityDict['rhou_x'] = rhou_x_uid_to_val
quantityDict['rhou_y'] = rhou_y_uid_to_val
quantityDict['rhoE'] = rhoE_uid_to_val
