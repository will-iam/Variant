import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '../../../'))
import script.rio as io
import script.initial_condition.sedov as sedov

# Domain properties
lx = 1.2
ly = 1.2

Nx = 1024
Ny = 1024

# Scheme execution options
T = 1.0
CFL = 0.5

gamma = 1.4
BClayer = 1

quantityList = ['rho', 'rhou_x', 'rhou_y', 'rhoE']
def buildme(quantityDict, coords_to_uid, coords_to_bc):
    sedov.build(quantityDict, coords_to_uid, coords_to_bc, Nx, Ny, lx, ly, BClayer)
