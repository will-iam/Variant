import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '../../../'))
import script.rio as io
import script.initial_condition.noh2D as noh2D

# Domain properties
lx = 1.0
ly = 1.0

Nx = 64
Ny = 64

# Scheme execution options
T = 0.6
CFL = 0.5

gamma = 5./3.
BClayer = 2

quantityList = ['rho', 'rhou_x', 'rhou_y', 'rhoE']

def buildme(quantityDict, coords_to_uid, coords_to_bc):
    noh2D.build(quantityDict, coords_to_uid, coords_to_bc, Nx, Ny, lx, ly, BClayer)
 
