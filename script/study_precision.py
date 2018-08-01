#!/usr/bin/python3
# -*- coding:utf-8 -*-

import __future__
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
#plt.style.use('ggplot')
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
quantityListName = ["rho"]
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
rho_1D = np.zeros(Nx)
for i in range(Nx):
    rho_1D[i] = data['rho'][i][0]
  
gamma = 1.4
npts = Nx
positions, regions, values = solve(left_state=(1, 1, 0), right_state=(0.1, 0.125, 0.),
                        geometry=(0., 1., 0.5), t=0.2, gamma=gamma, npts=npts)

fig = plt.figure(0, figsize=(9, 6))
ax1 = fig.add_subplot(111)
color = 'blue'
ax1.plot(x, rho_1D, color='black', linewidth=2, markersize=3, label="simul.")
ax1.plot(values['x'], values['rho'], linewidth=1.5, color=color, linestyle='dashed', label="exact")
ax1.set_ylabel('density', color=color)
ax1.grid()
ax1.axis([0, 1, 0, 1.1])
ax1.set(xlabel='x', title='Rho value on y = 0')
ax1.tick_params(axis='y', labelcolor=color)
ax1.legend()

color = 'red'
ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
ax2.plot(values['x'], np.abs(rho_1D - values['rho']), linewidth=1.5, color=color, label="err.")
ax2.set_ylabel('err.', color=color)  # we already handled the x-label with ax1
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()
plt.show()
