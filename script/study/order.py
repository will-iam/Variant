import __future__
from common import *


# Find all results you can get.
case_dir_path = os.path.join(config.cases_dir, args.project_name)

print("Looking for results in %s for case like %s ..." % (case_dir_path, args.case))

rawCaseList = [d for d in os.listdir(case_dir_path)
    if os.path.isdir(os.path.join(case_dir_path, d)) and d.startswith(args.case)]

caseList = list()
for d in rawCaseList:
    f = os.path.join(case_dir_path, d,'ref','final')
    if not os.path.isdir(f):
        continue
    if not os.path.isfile(os.path.join(f, 'rho.dat')):
        continue
    caseList.append(f)

print("Found %s references." % len(caseList))

# Compute order values
q_name = "rho"
order = dict()
for d in caseList:
    uid_to_coords = dict()
    start = timer()
    Nx, Ny, dx, dy = read_converter(d, uid_to_coords)
    data = np.zeros((Nx, Ny))
    read_quantity(data, d, uid_to_coords, q_name)
    q = data[:,0]
    end = timer()
    print("Time to load quantity", q_name, "of %s elements" % len(data), "%s second(s)" % int((end - start)))
    gamma = 1.4
    positions, regions, values = solve(left_state=(1, 1, 0), right_state=(0.1, 0.125, 0.),
                        geometry=(0., 1., 0.5), t=0.2, gamma=gamma, npts=Nx)
    print("Time to compute exact", q_name, "of %s elements" % len(values['rho']), "%s second(s)" % int((end - start)))
    order[float(dx)] = np.linalg.norm((q - values['rho']), ord=2) / Nx

print(sorted(order))
print([order[x] for x in sorted(order)])

fig = plt.figure(0, figsize=(9, 6))
ax1 = fig.add_subplot(111)
ax1.set_xscale('log')
ax1.set_yscale('log')

color = 'tab:blue'
last_dx = sorted(order)[-1]
last_value = order[last_dx]
x = np.linspace(0., last_dx, 30)
y = (last_value / last_dx) * x

ax1.plot(sorted(order), [order[x] for x in sorted(order)], marker='+', linewidth=1.5, color=color, label="order")
ax1.plot(x, y, linewidth=1.0, linestyle='dashed', color='black', label="extrap.")
ax1.set_ylabel('L^2-norm |sim. - exact|')
ax1.grid()
ax1.set(xlabel='dx', title='Order')

ax1.legend()
fig.tight_layout()
plt.show()
