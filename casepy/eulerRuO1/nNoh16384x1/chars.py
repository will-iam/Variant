import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '../../../'))
import script.rio as io
import script.initial_condition.noh1D as noh1D

# Domain properties
lx = 1.0
ly = 1.0

Nx = 16384
Ny = 1

# Scheme execution options
T = 0.6
CFL = 0.5

gamma = 5./3.
BClayer = 1

quantityList = ['rho', 'rhou_x', 'rhou_y', 'rhoE']

def buildme(quantityDict, coords_to_uid, coords_to_bc):
    noh1D.build(quantityDict, coords_to_uid, coords_to_bc, Nx, Ny, lx, ly, BClayer)
 
