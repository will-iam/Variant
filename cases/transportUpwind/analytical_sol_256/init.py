#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import numpy as np
from math import sqrt, sin, pi
import sys
import os

sys.path.append(os.path.join(sys.path[0], 'case',
'transportUpwind'))
import analytical_sol as an
an = reload(an)
del sys.path[-1]
import script.io as io

# ------------------------------------------------------------------------------
# Analytical solution
# ------------------------------------------------------------------------------
ux = an.ux
uy = an.uy

rho_init = an.rho_init
rho_t = an.rho_t

# ------------------------------------------------------------------------------
# Scheme execution options
# ------------------------------------------------------------------------------
T = an.T
CFL = an.CFL

# ------------------------------------------------------------------------------
# Domain properties
# ------------------------------------------------------------------------------
lx = an.lx
ly = an.ly

Nx = 256
Ny = 256

dx = lx / Nx
dy = ly / Ny

coords_to_uid = io.gen_coords_to_uid(Nx, Ny)
coords_to_uid_bc = io.gen_coords_to_uid_bc(Nx, Ny)

# Init quantities
quantityDict = dict()

# ------------------------------------------------------------------------------
# rho initial state
# ------------------------------------------------------------------------------
rho_uid_to_val = dict()
for i in range(Nx):
    for j in range(Ny):
        x = float(i) / Nx
        y = float(j) / Ny
        rho_uid_to_val[coords_to_uid[(i, j)]] = an.rho_init(x, y)

# ------------------------------------------------------------------------------
# Boundary conditions
# ------------------------------------------------------------------------------
BCtype = an.BCtype
del an

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
# velocity (constant) states
# ------------------------------------------------------------------------------
ux_uid_to_val = dict()
uy_uid_to_val = dict()
for i in range(Nx):
    for j in range(Ny):
        ux_uid_to_val[coords_to_uid[(i, j)]] = ux
        uy_uid_to_val[coords_to_uid[(i, j)]] = uy

# Add quantities to the quantity dictionary
quantityDict['rho'] = rho_uid_to_val
quantityDict['ux'] = ux_uid_to_val
quantityDict['uy'] = uy_uid_to_val

