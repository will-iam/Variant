#!/bin/env python3
# -*- coding:utf-8 -*-

import __future__
from common import *
import math

towatch = args.quant #"energy" #"u"; # "rho"
axis = args.axis

# Check if refence results exist.
case_py = os.path.join(config.case_ic, args.project_name, args.case)
ref_path = os.path.join(config.case_ref, args.project_name, args.case, "ref", args.precision, args.rounding_mode)
print("Looking for results in %s ..." % ref_path)
if not os.path.isdir(ref_path):
    print("Can't file reference result directory.")
    sys.exit(1)

if not os.path.isfile(os.path.join(ref_path, 'rho.dat')):
    print("Can't file reference result file.")
    sys.exit(1)

# Load quantities.
mapQuantityName = {"rho" : "rho", "u" : "rhou_" + axis}

quantityListName = ["rho"]
if towatch == "u":
    if axis == 'xy':
        quantityListName = ["rho", "rhou_x", "rhou_y"] 
    else:
        quantityListName = ["rho", "rhou_" + axis] 
elif towatch == "energy":
    quantityListName = ["rho", "rhoE","rhou_x","rhou_y"] 


data = dict()
uid_to_coords = dict()
Nx, Ny, dx, dy = read_converter(ref_path, uid_to_coords)

for q in quantityListName:
    data[q] = np.zeros((Nx, Ny))
    start = timer()
    read_quantity(data[q], ref_path, uid_to_coords, q)
    end = timer()
    print("Time to load quantity", q, "%s second(s)" % int((end - start)))

if axis == 'x':
    axis_title="y = 0"
    Npoints = Nx
    x = np.linspace(0., Nx * float(dx), Nx)
    qty = np.zeros(Nx)
    if towatch == "u":
        for i in range(Nx):
            qty[i] = data['rhou_x'][i][0] / data['rho'][i][0]
    elif towatch == "energy":
        for i in range(Nx):
            #qty[i] = (data['rhoE'][i][0]) / data['rho'][i][0]
            qty[i] = data['rhoE'][i][0] / data['rho'][i][0] -(data['rhou_x'][i][0] / data['rho'][i][0])**2/2.0
    elif towatch == "rho":
        for i in range(Nx):
            qty[i] = data['rho'][i][0]

elif axis == 'y':
    axis_title="x = 0"
    Npoints = Ny
    x = np.linspace(0., Ny * float(dy), Ny)
    qty = np.zeros(Ny)
    if towatch == "u":
        for i in range(Ny):
            qty[i] = data['rhou_y'][0][i] / data['rho'][0][i]
    elif towatch == "energy":
        for i in range(Ny):
            qty[i] = data['rhoE'][0][i] / data['rho'][0][i] -(data['rhou_y'][0][i] / data['rho'][0][i])**2/2.0
    elif towatch == "rho":
        for i in range(Ny):
            qty[i] = data['rho'][0][i]

elif axis == 'xy':
    axis_title="y = x"
    Npoints = math.floor(max(Nx,Ny)/np.sqrt(2.0))+1
    x = np.linspace(0., max(Nx,Ny) * float(min(dx,dy)), Npoints)
    qtynormed = np.zeros(max(Nx,Ny))
    if towatch == "u":
        for i in range(max(Nx,Ny)):
            uy = data['rhou_y'][i][i] / data['rho'][i][i]
            ux = data['rhou_x'][i][i] / data['rho'][i][i]
            qtynormed[i] = np.sqrt(ux**2. + uy**2) if ux>=0 and uy>=0 else -np.sqrt(ux**2+uy**2)
    elif towatch == "energy":
        for i in range(max(Nx,Ny)):
            qtynormed[i] = data['rhoE'][i][i] / data['rho'][i][i] -(data['rhou_x'][i][i]**2 + data['rhou_y'][i][i]**2) / data['rho'][i][i]**2/2.0
    elif towatch == "rho":
        for i in range(max(Nx,Ny)):
            qtynormed[i] = data['rho'][i][i]
    if Nx>1 and Ny>1:      #2D, Nx=Ny
        qty = np.zeros(Npoints)
        for i in range(len(qtynormed)):
            if i/len(qtynormed)<=1.0/np.sqrt(2.0):
                qty[i] = qtynormed[i]
    else:      #1D
        qty = qtynormed 
if args.solver == 'sod':
    sys.path.insert(1, os.path.join(sys.path[0], 'sod'))
    from sod import solve
    if Nx>1 and Ny>1:      #2D, Nx=Ny
        if axis=='xy':
            positions, regions, values = solve(left_state=(1, 1, 0), right_state=(0.1, 0.125, 0.),
                        geometry=(0., 1., 0.5), t=0.2, gamma=1.4, npts=Npoints)
        else:
            positions, regions, values = solve(left_state=(1, 1, 0), right_state=(0.1, 0.125, 0.),
                        geometry=(0., 1., 0.5), t=0.2, gamma=1.4, npts=Npoints)
    else:       #1D
        positions, regions, values = solve(left_state=(1, 1, 0), right_state=(0.1, 0.125, 0.),
                    geometry=(0., 1., 0.5), t=0.2, gamma=1.4, npts=Npoints)
        
if args.solver == 'sedov':
    sys.path.insert(1, os.path.join(sys.path[0], 'sedov'))
    from sedov import solve
    values = solve(t=1.0, gamma=1.4, xpos=x)

if args.solver == 'noh':
    sys.path.insert(1, os.path.join(sys.path[0], 'noh'))
    from noh import solve
    if Nx==1:
        values = solve(t=0.6, gamma=5./3., npts=Ny, ndim=1, axis='y')
    if Ny==1:
        values = solve(t=0.6, gamma=5./3., npts=Nx, ndim=1, axis='x')
    if Nx>1 and Ny>1:      #2D, Nx=Ny
        if axis=='xy':
            values = solve(t=0.6, gamma=5./3., npts=math.floor(max(Nx,Ny)/np.sqrt(2.0))+1, ndim=2)
        else:
            values = solve(t=0.6, gamma=5./3., npts=Nx, ndim=2)
print("intégrale exacte de",towatch," : ", sum(values[towatch]/max(Nx,Ny)))
print("intégrale simulation de",towatch," : ", sum(qty/max(Nx,Ny)))

fig = plt.figure(0, figsize=(9, 6))
ax1 = fig.add_subplot(111)
color = 'blue'
#ax1.set_yscale('log')
ax1.plot(x, qty, color='black', linewidth=2, markersize=3, label="simul.")
ax1.plot(x, values[towatch], linewidth=1.5, color=color, linestyle='dashed', label="exact")
ax1.set_ylabel(towatch, color=color)
ax1.grid()
#ax1.axis([0, 1, 0, 1.1])
ax1.set(xlabel='x', title='%s value on %s' % (towatch, axis_title))
ax1.tick_params(axis='y', labelcolor=color)
ax1.legend()

color = 'red'
#ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
#ax2.plot(x, np.abs(qty - values[towatch]), linewidth=1.5, color=color, label="err.")
#ax2.set_ylabel('err.', color=color)  # we already handled the x-label with ax1
#ax2.tick_params(axis='y', labelcolor=color)

if not os.path.exists("plot"):
    os.makedirs("plot")
outputCurve("plot/simul-%s-%s-%s-%s.dat" % (args.project_name, args.case, args.precision, args.rounding_mode), x, qty)
outputCurve("plot/exact-%s-%s-%s-%s.dat" % (args.project_name, args.case, args.precision, args.rounding_mode), x, qty)
outputCurve("plot/err-%s-%s-%s-%s.dat" % (args.project_name, args.case, args.precision, args.rounding_mode), x, np.abs(qty - values[towatch]))

fig.tight_layout()
plt.show()
