#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import numpy as np
from math import sqrt, sin
import sys
import os

sys.path.insert(1, os.path.join(sys.path[0], '../../../'))
import script.io as io

# ------------------------------------------------------------------------------
# Domain properties
# ------------------------------------------------------------------------------
lx = 1.0
ly = 1.0

Nx = 64
Ny = 1

dx = lx / Nx
dy = ly / Ny

coords_to_uid = io.gen_coords_to_uid(Nx, Ny)
coords_to_uid_bc = io.gen_coords_to_uid_bc(Nx, Ny)

# ------------------------------------------------------------------------------
# Scheme execution options
# ------------------------------------------------------------------------------
T = 0.2
CFL = 0.5#0.0001

# Init quantities
quantityDict = dict()

# ------------------------------------------------------------------------------
# rho initial state
# ------------------------------------------------------------------------------
gamma = 1.4
rho_uid_to_val = dict()
rhoe_uid_to_val = dict()
for i in range(Nx):
    for j in range(Ny):
        coords = coords_to_uid[(i, j)]
        P = 1.0
        if i <= Nx / 2:
            rho_uid_to_val[coords] = 1#float(i) / Nx
        else:
            P = 0.1
            rho_uid_to_val[coords] = 0.125
        rhoe_uid_to_val[coords] = 2.5 * P

# ------------------------------------------------------------------------------
# Boundary conditions
# ------------------------------------------------------------------------------
BCtype = 'N'
coords_to_bc = dict()
# Start new uid after last domain cell
# Left border
for j in range(-1, Ny):
    coords_to_bc[(-1, j)] = (BCtype, 0)
# Top border
for i in range(-1, Nx):
    coords_to_bc[(i, Ny)] = (BCtype, 0)
# Right border
for j in range(Ny, -1, -1):
    coords_to_bc[(Nx, j)] = (BCtype, 0)
# Bottom border
for i in range(Nx, -1, -1):
    coords_to_bc[(i, -1)] = (BCtype, 0)

# Merging uid and bc dictionaries
ds = [coords_to_uid_bc, coords_to_bc]
coords_to_uid_and_bc = dict()
for coord in coords_to_bc:
    coords_to_uid_and_bc[coord] = tuple(d.get(coord) for d in ds)

# ------------------------------------------------------------------------------
# velocity states
# ------------------------------------------------------------------------------
rhou_x_uid_to_val = dict()
rhou_y_uid_to_val = dict()
for i in range(Nx):
    for j in range(Ny):
        x = i * dx - lx / 2
        y = j * dy - ly / 2
        if x != 0 or y != 0:
            rhou_x_uid_to_val[coords_to_uid[(i, j)]] = 0#2 * (x - lx / 4)#-y / (sqrt(x**2 + y**2))
            rhou_y_uid_to_val[coords_to_uid[(i, j)]] = 0#x / (sqrt(x**2 + y**2))
        else:
            rhou_x_uid_to_val[coords_to_uid[(i, j)]] = 0#2 * (x - lx / 4)
            rhou_y_uid_to_val[coords_to_uid[(i, j)]] = 0

# Add quantities to the quantity dictionary
quantityDict['rho'] = rho_uid_to_val
quantityDict['rhou_x'] = rhou_x_uid_to_val
quantityDict['rhou_y'] = rhou_y_uid_to_val
quantityDict['rhoe'] = rhoe_uid_to_val

