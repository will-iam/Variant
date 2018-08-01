#!/usr/bin/python3
# -*- coding:utf-8 -*-

import __future__
import sys
import os
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
#plt.style.use('ggplot')
import numpy as np
from decimal import Decimal
from timeit import default_timer as timer
import argparse
from rio import read_quantity, read_converter
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import config
sys.path.insert(1, os.path.join(sys.path[0], 'sod_shocktube'))
from sod import solve

parser = argparse.ArgumentParser(description="Visualize reference results from simulation", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("--case", type = str, help = "Case to visualize", required=True)
args = parser.parse_args()

# Check if refence results exist.
case_path = os.path.join(config.cases_dir, args.project_name, args.case, 'ref', 'final')
#case_path = os.path.join(config.cases_dir, 'hydro4x1', 'n2dsod512x512', 'ref', 'final')
print("Looking for results in %s ..." % case_path)

if not os.path.isdir(case_path):
    print("Can't file reference result directory.")
    sys.exit(1)

if not os.path.isfile(os.path.join(case_path, 'rho.dat')):
    print("Can't file reference result file.")
    sys.exit(1)

# Load quantities.
quantityListName = ["rho", "rhou_x", "rhou_y", "rhoe"]
data = dict()
uid_to_coords = dict()
Nx, Ny, dx, dy = read_converter(case_path, uid_to_coords)

for q in quantityListName:
    data[q] = np.zeros((Nx, Ny))
    start = timer()
    read_quantity(data[q], case_path, uid_to_coords, q)
    end = timer()
    print("Time to load quantity", q, "%s second(s)" % int((end - start)))

x = np.linspace(0., Nx * float(dx), Nx)
y = np.linspace(0., Ny * float(dy), Ny)
Ux = np.zeros((Nx, Ny))
Uy = np.zeros((Nx, Ny))
Ek = np.zeros((Nx, Ny))
Ei = np.zeros((Nx, Ny))
rho_1D = np.zeros(Nx)
for i in range(Nx):
    rho_1D[i] = data['rho'][i][0]
    for j in range(Ny):
        if data['rho'][i][j] == 0.:
            continue
        Ux[i][j] = data['rhou_x'][i][j] / data['rho'][i][j]
        Uy[i][j] = data['rhou_y'][i][j] / data['rho'][i][j]
        Ek[i][j] = np.sqrt(Ux[i][j]*Ux[i][j] + Uy[i][j]*Uy[i][j])
        Ei[i][j] = data['rhoe'][i][j] / data['rho'][i][j]

gamma = 1.4
npts = 500
positions, regions, values = solve(left_state=(1, 1, 0), right_state=(0.1, 0.125, 0.),
                                           geometry=(0., 1., 0.5), t=0.2, gamma=gamma, npts=npts)

# Now show them.
fig = plt.figure(0, figsize=(9, 6))

########## rho ################
ax0 = fig.add_subplot(221)
cf = ax0.contourf(data['rho'].transpose())
fig.colorbar(cf, ax=ax0)
ax0.set_title('rho contourf with levels')
ax0.axis('tight')

########## rho 1D border ################
ax1 = fig.add_subplot(223)
ax1.plot(x, rho_1D, 'b+-', linewidth=2, markersize=3, label="simul.")
plt.plot(values['x'], values['rho'], linewidth=1.5, color='r', linestyle='dashed', label="exact")
ax1.set(xlabel='x', ylabel='density', title='Rho value on y = 0')
ax1.grid()
ax1.axis([0, 1, 0, 1.1])
#ax1.axis('tight')
    
########## internal energy ################
ax2 = fig.add_subplot(222)
cm = ax2.pcolormesh(Ei.transpose())
fig.colorbar(cm, ax=ax2)
ax2.set_title('rho pcolormesh with levels')
ax2.axis('tight')

########## velocity field ################
ax3 = fig.add_subplot(224)
#lw = 3 * Ek.transpose() / Ek.max()
#strm = ax3.streamplot(x, y, Ux.transpose(), Uy.transpose(), color=Ek.transpose(), cmap='autumn', linewidth=lw)
strm = ax3.streamplot(x, y, Ux.transpose(), Uy.transpose(),color=Ek.transpose())
#strm = ax3.streamplot(x, y, Ux.transpose(), Uy.transpose())
#fig.colorbar(strm.lines)
#strm = ax3.contourf(Ux.transpose())
#fig.colorbar(strm, ax=ax3)

ax3.set_title('u field')
ax3.axis('tight')

# adjust spacing between subplots so `ax1` title and `ax0` tick labels don't overlap
fig.tight_layout()
plt.legend()
plt.show()
