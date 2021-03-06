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
    rho_uid_to_val = np.ones((Nx*Ny), dtype = np.dtype(Decimal))
    rhoe_uid_to_val = np.zeros((Nx*Ny), dtype = np.dtype(Decimal))

    coords = coords_to_uid[(0, 0)]
    rhoe_uid_to_val[coords] = 0.244816 / (dx * dy)

    # ------------------------------------------------------------------------------
    # Boundary conditions
    # ------------------------------------------------------------------------------
    # Start new uid after last domain cell
    for k in range(1, BClayer + 1):
        # Left border
        for j in range(-k, Ny - 1 + k):
            uy = 1 if j >= 0 and j < Ny else -1
            coords_to_bc[(-k, j)] = {'N': {"rho": 1, "rhoE": 1, "pressure": 1, "rhou_x": -1, "rhou_y": uy}}

        # Top border
        for i in range(-k, Nx - 1 + k):
            ux = 1 if i >= 0 and i < Nx else -1
            coords_to_bc[(i, Ny - 1 + k)] = {'N': {"rho": 1, "rhoE": 1, "pressure": 1, "rhou_x": ux, "rhou_y": -1}}

        # Right border
        for j in range(Ny, -k, -1):
            uy = 1 if j >= 0 and j < Ny else -1
            coords_to_bc[(Nx - 1 + k, j)] = {'N': {"rho": 1, "rhoE": 1, "pressure": 1,"rhou_x": -1, "rhou_y": uy}}

        # Bottom border
        for i in range(Nx, -k, -1):
            ux = 1 if i >= 0 and i < Nx else -1
            coords_to_bc[(i, -k)] = {'N': {"rho": 1, "rhoE": 1, "pressure": 1, "rhou_x": ux, "rhou_y": -1}}

    # ------------------------------------------------------------------------------
    # velocity states
    # ------------------------------------------------------------------------------

    # Add quantities to the quantity dictionary
    quantityDict['rho'] = rho_uid_to_val
    quantityDict['rhoE'] = rhoe_uid_to_val
