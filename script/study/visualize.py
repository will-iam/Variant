#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
from common import *

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
sys.path.append(case_py)
import chars
quantityListName = chars.quantityList
print(quantityListName)

data = dict()
uid_to_coords = dict()
Nx, Ny, dx, dy = read_converter(ref_path, uid_to_coords)

for q in quantityListName:
    data[q] = np.zeros((Nx, Ny))
    start = timer()
    read_quantity(data[q], ref_path, uid_to_coords, q)
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
    for j in range(Ny):
        if data['rho'][i][j] == 0.:
            continue
        Ux[i][j] = data['rhou_x'][i][j] / data['rho'][i][j]
        Uy[i][j] = data['rhou_y'][i][j] / data['rho'][i][j]
        Ek[i][j] = np.sqrt(Ux[i][j]*Ux[i][j] + Uy[i][j]*Uy[i][j])
        Ei[i][j] = data['rhoE'][i][j] / data['rho'][i][j]-Ek[i][j]


if args.solver == 'sod':
    for i in range(Nx):
        rho_1D[i] = data['rho'][i][0]
    exact_title='Rho value on y = 0'
    sys.path.insert(1, os.path.join(sys.path[0], 'sod'))
    from sod import solve
    positions, regions, values = solve(left_state=(1, 1, 0), right_state=(0.1, 0.125, 0.),
                                           geometry=(0., 1., 0.5), t=0.2, gamma=1.4, npts=500)

if args.solver == 'sedov':
    for i in range(Nx):
        rho_1D[i] = data['rho'][i][i]
    exact_title='Rho value on y = x'
    sys.path.insert(1, os.path.join(sys.path[0], 'sedov'))
    from sedov import solve
    values = solve(t=1.2, gamma=1.4, xpos=x)

if args.solver == 'noh':
    if Nx==1: 
        for i in range(Ny):
            rho_1D[i] = data['rho'][0][i]
    if Ny==1: 
        for i in range(Nx):
            rho_1D[i] = data['rho'][i][0]
    if Nx>1 and Ny>1:      #2D, with Nx=Ny
        for i in range(Nx):
            rho_1D[i] = data['rho'][i][i]
    exact_title='Rho value on y = x'
    sys.path.insert(1, os.path.join(sys.path[0], 'noh'))
    from noh import solve
    if Nx==1:
        values = solve(t=0.6, gamma=5./3., ndim=1,npts=Ny,axis='y')
    if Ny==1:
        values = solve(t=0.6, gamma=5./3., ndim=1,npts=Nx,axis='x')
    if Nx>1 and Ny>1:     #2D, with Nx=Ny
        values = solve(t=0.6, gamma=5./3., ndim=2,npts=Nx)
print("intégrale de rho sur tout le domaine (simulation) : ", sum(sum(data['rho'])/(Nx*Ny)))
#print("intégrale de rho exacte : ", sum(sum(values['rho'])/(Nx*Ny)))

# Now show them.
fig = plt.figure(0, figsize=(9, 6))

########## rho ################
ax0 = fig.add_subplot(221)
cf = ax0.contourf(data['rho'].transpose())
fig.colorbar(cf, ax=ax0)
ax0.set_title('rho contourf with levels')
ax0.axis('tight')

########## rho 1D vs exact ################
ax1 = fig.add_subplot(223)
ax1.plot(x, rho_1D, 'b+-', linewidth=2, markersize=3, label="simul.")
plt.plot(values['x'], values['rho'], linewidth=1.5, color='r', linestyle='dashed', label="exact")
ax1.set(xlabel='x', ylabel='density', title=exact_title)
ax1.grid()
#ax1.axis([0, 1, 0, 1.1])
#ax1.axis('tight')

########## internal energy ################
ax2 = fig.add_subplot(222)
cm = ax2.pcolormesh(Ei.transpose())
fig.colorbar(cm, ax=ax2)
ax2.set_title('Energy pcolormesh with levels')
ax2.axis('tight')

########## velocity field ################
ax3 = fig.add_subplot(224)
#lw = 3 * Ek.transpose() / Ek.max()
#strm = ax3.streamplot(x, y, Ux.transpose(), Uy.transpose(), color=Ek.transpose(), cmap='autumn', linewidth=lw)
strm = ax3.streamplot(x, y, Ux.transpose(), Uy.transpose(), color=Ek.transpose())
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
