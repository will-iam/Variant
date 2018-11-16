#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
from common import *


qname = "rho" #"u"; # "rho"
axis = 'y'
floatType = np.float64 if args.precision == 'double' else np.float32

# Check if refence results exist.
cases_dir = os.path.join(config.workspace, 'empty_cases', args.project_name, args.case)
case_path_ref = os.path.join(cases_dir, 'ref', args.precision, args.rounding_mode)
case_path_tmp = os.path.join('tmp', args.project_name, args.case, 'final')

print("Looking for results in %s and %s ..." % (case_path_ref, case_path_tmp))
if not os.path.isdir(case_path_ref) or not os.path.isdir(case_path_tmp):
    print("Can't file reference result directory.")
    sys.exit(1)

if not os.path.isfile(os.path.join(case_path_ref, 'rho.dat')) or not os.path.isfile(os.path.join(case_path_tmp, 'rho.dat')):
    print("Can't file reference result file.")
    sys.exit(1)

if not os.path.isfile(os.path.join(case_path_tmp, 'rho.dat')):
    print("Can't file temporary result file.")
    sys.exit(1)

# Get quantity's name.
sys.path.append(cases_dir)
import chars
quantityListName = chars.quantityList
if qname not in quantityListName:
    print("Requested quantity %s does not exist in %s." % (qname, quantityListName))
    sys.exit(1)

# Load quantities.
uid_to_coords_ref = dict()
Nx, Ny, dx, dy = read_converter(case_path_ref, uid_to_coords_ref)
quantity_ref = np.zeros((Nx, Ny), dtype = floatType)
start = timer()
read_quantity(quantity_ref, case_path_ref, uid_to_coords_ref, qname)
end = timer()
print("Time to load quantity ref", qname, "%s second(s)" % int((end - start)))

uid_to_coords_tmp = dict()
Nx, Ny, dx, dy = read_converter(case_path_tmp, uid_to_coords_tmp)
quantity_tmp = np.zeros((Nx, Ny), dtype = floatType)
start = timer()
read_quantity(quantity_tmp, case_path_tmp, uid_to_coords_tmp, qname)
end = timer()
print("Time to load quantity tmp", qname, "%s second(s)" % int((end - start)))

# Build comp values.
if axis == 'x':
    quantity_diff = np.zeros(Nx, dtype = floatType)
    for i in range(Nx):
        quantity_diff[i] = quantity_ref[i][0] - quantity_tmp[i][0]
else:
    quantity_diff = np.zeros(Ny, dtype = floatType)
    for i in range(Ny):
        quantity_diff[i] = quantity_ref[0][i] - quantity_tmp[0][i]

if axis == 'x':
    Npoints = Nx
    x = np.linspace(0., Nx * float(dx), Nx)
else:
    Npoints = Ny
    x = np.linspace(0., Ny * float(dy), Ny)

print "maximum difference: ", np.abs(np.max(quantity_diff))

fig = plt.figure(0, figsize=(9, 6))
ax1 = fig.add_subplot(111)
color = 'blue'
ax1.plot(x, quantity_ref[:, 0], color='black', linewidth=1, markersize=2, label="simul. ref.")
ax1.plot(x, quantity_tmp[:, 0], color='blue', linewidth=1, markersize=2, label="simul. tmp.")
ax1.set_ylabel(qname, color=color)
ax1.grid()
ax1.axis([0, 1, 0, 1.1])
ax1.set(xlabel='x', title=qname + ' value on ' + axis + ' = 0')
ax1.tick_params(axis='y', labelcolor=color)
ax1.legend()

color = 'red'
ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
ax2.plot(x, quantity_diff, linewidth=1.5, color=color, label="err.")
ax2.set_ylabel('err.', color=color)  # we already handled the x-label with ax1
ax2.tick_params(axis='y', labelcolor=color)
fig.tight_layout()
plt.show()
