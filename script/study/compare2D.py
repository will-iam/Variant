#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
from common import *


qname = "rho" #"u"; # "rho"
floatType = np.float64 if args.precision == 'double' else np.float32

# Check if refence results exist.
cases_dir = os.path.join(config.cases_dir, args.project_name, args.case)
case_path_ref = os.path.join(cases_dir, 'ref', args.precision, args.rounding_mode)
case_path_tmp = os.path.join('tmp', args.project_name, args.case, 'final')

print("Looking for results in %s and %s ..." % (case_path_ref, case_path_tmp))
if not os.path.isdir(case_path_ref) or not os.path.isdir(case_path_tmp):
    print("Can't file reference result directory.")
    sys.exit(1)

if not os.path.isfile(os.path.join(case_path_ref, 'rho.dat')) or not os.path.isfile(os.path.join(case_path_tmp, 'rho.dat')):
    print("Can't file reference result file.")
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
quantity_diff = quantity_ref - quantity_tmp
print "maximum difference: ", np.abs(np.max(quantity_diff))

fig = plt.figure(0, figsize=(9, 6))

ax0 = fig.add_subplot(221)
cfref = ax0.contourf(quantity_ref.transpose())
fig.colorbar(cfref, ax=ax0)
ax0.set_title('%s ref with levels' % qname)
ax0.axis('tight')

ax1 = fig.add_subplot(222)
cftmp = ax1.contourf(quantity_tmp.transpose())
fig.colorbar(cftmp, ax=ax1)
ax1.set_title('%s tmp with levels' % qname)
ax1.axis('tight')

ax2 = fig.add_subplot(223)
cftmp = ax2.contourf(quantity_diff.transpose())
fig.colorbar(cftmp, ax=ax2)
ax2.set_title('%s diff with levels' % qname)
ax2.axis('tight')

ax3 = fig.add_subplot(224)
cm = ax3.pcolormesh(quantity_diff.transpose())
fig.colorbar(cm, ax=ax3)
ax3.set_title('%s diff pcolormesh with levels' % qname)
ax3.axis('tight')



fig.tight_layout()
plt.legend()
plt.show()
