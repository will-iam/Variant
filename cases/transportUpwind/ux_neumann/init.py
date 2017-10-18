#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import numpy as np
from math import sqrt
import sys
import os

sys.path.insert(1, os.path.join(sys.path[0], '../../../'))
import script.io as io

# ------------------------------------------------------------------------------
# Domain properties
# ------------------------------------------------------------------------------
lx = 1.0
ly = 1.0

Nx = 50
Ny = 50

dx = lx / Nx
dy = ly / Ny

coords_to_uid = io.gen_coords_to_uid(Nx, Ny)

# ------------------------------------------------------------------------------
# Scheme execution options
# ------------------------------------------------------------------------------
T = 1.0
CFL = 0.5

# Init quantities
quantityDict = dict()

# ------------------------------------------------------------------------------
# rho initial state
# ------------------------------------------------------------------------------
rho_uid_to_val = dict()
for i in range(Nx):
    for j in range(Ny):
        if abs(i - Nx / 2) < Nx / 4 and abs(j - Ny / 2) < Ny / 4:
            rho_uid_to_val[coords_to_uid[(i, j)]] = 1#float(i) / Nx
        else:
            rho_uid_to_val[coords_to_uid[(i, j)]] = 0

# boundary conditions for rho
BCtype = 'P'
rho_uid_to_bc = dict()
# Start new uid after last domain cell
uid_tmp = max(coords_to_uid.itervalues()) + 1
# Left side
for j in range(-1, Ny):
    rho_uid_to_bc[uid_tmp] = [(-1, j), BCtype, 0]
    uid_tmp += 1
# Top side
for i in range(-1, Nx):
    rho_uid_to_bc[uid_tmp] = [(i, Ny), BCtype, 0]
    uid_tmp += 1
# Right side
for j in range(Ny, -1, -1):
    rho_uid_to_bc[uid_tmp] = [(Nx, j), BCtype, 0]
    uid_tmp += 1
# Bottom side
for i in range(Nx, -1, -1):
    rho_uid_to_bc[uid_tmp] = [(i, -1), BCtype, 0]
    uid_tmp += 1

# ------------------------------------------------------------------------------
# velocity (constant) states
# ------------------------------------------------------------------------------
ux_uid_to_val = dict()
uy_uid_to_val = dict()
for i in range(Nx):
    for j in range(Ny):
        x = i * dx - lx / 2
        y = j * dy - ly / 2
        if x != 0 or y != 0:
            ux_uid_to_val[coords_to_uid[(i, j)]] = 1.0#2 * (x - lx / 4)#-y / (sqrt(x**2 + y**2))
            uy_uid_to_val[coords_to_uid[(i, j)]] = 1.0#x / (sqrt(x**2 + y**2))
        else:
            ux_uid_to_val[coords_to_uid[(i, j)]] = 1.0#2 * (x - lx / 4)
            uy_uid_to_val[coords_to_uid[(i, j)]] = 1.0

# Add quantities to the quantity dictionary
quantityDict['rho'] = dict({'uid_to_val': rho_uid_to_val,
        'uid_to_bc': rho_uid_to_bc})
quantityDict['ux'] = dict({'uid_to_val': ux_uid_to_val})
quantityDict['uy'] = dict({'uid_to_val': uy_uid_to_val})

