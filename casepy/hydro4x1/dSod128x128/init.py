#!/usr/bin/env python3
# -*- coding:utf-8 -*-

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
rhoe_uid_to_val = np.zeros((Nx*Ny), dtype = np.dtype(Decimal))
for i in range(Nx):
    for j in range(Ny):
        coords = coords_to_uid[(i, j)]
        P = 1.0
        if i <= Nx / 2 and j <= Ny / 2:
            rho_uid_to_val[coords] = 1#float(i) / Nx
        else:
            P = 0.1
            rho_uid_to_val[coords] = 0.125
        rhoe_uid_to_val[coords] = P / (gamma - 1.0)

# ------------------------------------------------------------------------------
# Boundary conditions
# ------------------------------------------------------------------------------
coords_to_bc = dict()
# Start new uid after last domain cell
for k in range(1, BClayer + 1):
    # Left border
    for j in range(-k, Ny - 1 + k):
        uy = 1 if j >= 0 and j < Ny else -1
        coords_to_bc[(-k, j)] = {BCtype: {"rho": 1, "rhoe": 1, "rhou_x": -1, "rhou_y": uy}}

    # Top border
    for i in range(-k, Nx - 1 + k):
        ux = 1 if i >= 0 and i < Nx else -1
        coords_to_bc[(i, Ny - 1 + k)] = {BCtype: {"rho": 1, "rhoe": 1, "rhou_x": ux, "rhou_y": -1}}

    # Right border
    for j in range(Ny, -k, -1):
        uy = 1 if j >= 0 and j < Ny else -1
        coords_to_bc[(Nx - 1 + k, j)] = {BCtype: {"rho": 1, "rhoe": 1, "rhou_x": -1, "rhou_y": uy}}

    # Bottom border
    for i in range(Nx, -k, -1):
        ux = 1 if i >= 0 and i < Nx else -1
        coords_to_bc[(i, -k)] = {BCtype: {"rho": 1, "rhoe": 1, "rhou_x": ux, "rhou_y": -1}}


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
quantityDict['rhoe'] = rhoe_uid_to_val
