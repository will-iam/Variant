import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '../../../'))
import script.rio as io
import script.initial_condition.sod as sod

# Domain properties
lx = 1.0
ly = 1.0

Nx = 524288
Ny = 1

# Scheme execution options
T = 0.2
CFL = 0.5

gamma = 1.4
BCtype = 'N'
BClayer = 1

quantityList = ['rho', 'rhou_x', 'rhou_y', 'rhoE']
def buildme(quantityDict, coords_to_uid, coords_to_bc):
    sod.build(quantityDict, coords_to_uid, coords_to_bc, Nx, Ny, lx, ly, BClayer, BCtype, gamma)
