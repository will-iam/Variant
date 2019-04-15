from numpy import sqrt

# Domain properties
lx = 1.0
ly = 1.0

Nx = 8192
Ny = 1

# Scheme execution options
T = 0.6
CFL = 0.5

gamma = 5./3.
BCtype = 'N'
BClayer = 1

quantityList = ['rho', 'rhou_x', 'rhou_y', 'rhoE']
