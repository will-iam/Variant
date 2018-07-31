#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
from rio import read_quantity, read_converter

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
plt.style.use('ggplot')
import numpy as np
from decimal import Decimal
from timeit import default_timer as timer
import argparse
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import config

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

# Now show them.

fig = plt.figure(0, figsize=(9, 6))
ax0 = fig.add_subplot(221)

im = ax0.pcolormesh(data['rho'].transpose())
fig.colorbar(im, ax=ax0)
ax0.set_title('rho pcolormesh with levels')
ax0.axis('tight')

#plt.title('Weak Scaling from')
#plt.xlabel('Core(s)')
#plt.ylabel('(Log) Loop Time / (cell x iteration)')
#plt.legend()

ax1 = fig.add_subplot(223)
cf1 = ax1.contourf(data['rho'].transpose())
fig.colorbar(cf1, ax=ax1)
ax1.set_title('rho contourf with levels')
ax1.axis('tight')

#plt.title('Weak Scaling from')
#plt.xlabel('Core(s)')
#plt.ylabel('(Log) Loop Time / (cell x iteration)')
#plt.legend()

ax2 = fig.add_subplot(222)
cf2 = ax2.contourf(data['rhoe'].transpose())
fig.colorbar(cf2, ax=ax2)
ax2.set_title('rhoe contourf with levels')
ax2.axis('tight')


x = np.linspace(0., Nx * float(dx), Nx)
y = np.linspace(0., Ny * float(dy), Ny)

Ux = np.zeros((Nx, Ny))
Uy = np.zeros((Nx, Ny))
Ek = np.zeros((Nx, Ny))
for i in range(Nx):
    for j in range(Ny):
        Ux[i][j] = data['rhou_x'][i][j] / data['rho'][i][j]
        Uy[i][j] = data['rhou_y'][i][j] / data['rho'][i][j]
        Ek[i][j] = np.sqrt(Ux[i][j]*Ux[i][j] + Uy[i][j]*Uy[i][j])

ax3 = fig.add_subplot(224)
#lw = 3 * Ek.transpose() / Ek.max()
#strm = ax3.streamplot(x, y, Ux.transpose(), Uy.transpose(), color=Ek.transpose(), cmap='autumn', linewidth=lw)
strm = ax3.streamplot(x, y, Ux.transpose(), Uy.transpose(),color=Ek.transpose())
fig.colorbar(strm.lines)
ax3.set_title('rhou')
ax3.axis('tight')

# adjust spacing between subplots so `ax1` title and `ax0` tick labels
# don't overlap
#fig.tight_layout()


plt.show()
