import __future__
from common import *
sys.path.insert(1, os.path.join(sys.path[0], 'sod'))
sys.path.insert(1, os.path.join(sys.path[0], 'sedov'))
sys.path.insert(1, os.path.join(sys.path[0], 'noh'))
import error_norm

# Find all results you can get.
cases_dir = config.cases_dir
case_dir_path = os.path.join(cases_dir, args.project_name)

print("Looking for results in %s for case like %s ..." % (case_dir_path, args.case))

rawCaseList = [d for d in os.listdir(case_dir_path)
    if os.path.isdir(os.path.join(case_dir_path, d)) and d.startswith(args.case)]

q_name = "rho"

# Compute order values
rounding = ['average', 'upward', 'downward', 'toward_zero', 'farthest', 'nearest']
order = dict()
for m in rounding:
    order[m] = {'float': dict(), 'double': dict()}
    for o in order[m]:
        for d in rawCaseList:
            f = os.path.join(case_dir_path, d, 'ref', o, m)
            if not os.path.isdir(f):
                continue
            if not os.path.isfile(os.path.join(f, 'error.dat')):
                if not os.path.isfile(os.path.join(f, q_name + '.dat')):
                    continue
                err = error_norm.compute(f, ["rho"], args.solver)
                if err == None:
                    continue
                    
                print("err =", err)
                error_norm.save(f, err)
                order[m][o][err['N']] = err['rho']
            else:
                err_list = error_norm.load(f)
                #if err_list[0]['N'] == 4096:
                #    print("Found in file: %s\n%s" % (f, err_list))
                order[m][o][err_list[0]['N']] = err_list[0]['rho']
    print("%s: found %s references in simple precision, %s in double precision for the nearest rounding mode." % (m, len(order[m]['float']), len(order[m]['double'])))

# Compute order values
random = {'float': dict(), 'double': dict()}
sigma = {'float': dict(), 'double': dict()}
for o in random:
    for d in rawCaseList:
        f = os.path.join(case_dir_path, d, 'ref', o, 'random')
        if not os.path.isdir(f):
            continue

        if not os.path.isfile(os.path.join(f, 'error.dat')):
            continue
        
        err_list = error_norm.load(f)
        for err in err_list:
            random[o].setdefault(int(err['N']), list()).append(err['rho'])
        
        for N in random[o]:
            std = np.std(random[o][N])
            if std > 1e-10: #beyond it's neglectible.
                sigma[o][N] = np.std(random[o][N])

for o in random:
    for N in sigma[o]:        
        print("%s - N: %s (%s), std-deviation = %s, random point number: %s %s" % (o, N, np.sqrt(N), sigma[o][N], len(random[o][N]), '< 33' if len(random[o][N]) < 33 else ''))

print("Found %s references in simple precision, %s in double precision for the random rounding mode." % (len(random['float']), len(random['double'])))

fig = plt.figure(0, figsize=(9, 6))
ax1 = fig.add_subplot(111)
ax1.set_xscale('log')
ax1.set_yscale('log')

'''
if len(sigma['float']) > 0 or  len(sigma['double']) > 0:
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    ax2.set_yscale('log')
    ax2.plot(sorted(sigma['float']), [sigma['float'][v] for v in sorted(sigma['float'])], linewidth=1.0, color='red')
    ax2.plot(sorted(sigma['double']), [sigma['double'][v] for v in sorted(sigma['double'])], linewidth=1.0, color='orange')
    ax2.set_ylabel('sigma.', color='red')  # we already handled the x-label with ax1
    ax2.tick_params(axis='y', labelcolor='red')
'''

p = 'float' if len(order['nearest']['float']) > len(order['nearest']['double']) else 'double'
if len(order['nearest'][p]) == 0:
    print("No results found.")
    sys.exit(1)

first_N = int(sorted(order['nearest'][p])[0])
last_N = int(sorted(order['nearest'][p])[-1])
first_value = float(order['nearest'][p][first_N])
x = np.linspace(first_N, last_N, 30)
y = first_value / (x / first_N)

ax1.plot(x, y,linewidth=1.5, linestyle='dashed', color='black', label="extrap.")

for m in rounding:
    if len(order[m]['float']):
        ax1.plot(sorted(order[m]['float']), [order[m]['float'][v] for v in sorted(order[m]['float'])], marker='+', linewidth=1.0, label="float " + m)
    if len(order[m]['double']):
        ax1.plot(sorted(order[m]['double']), [order[m]['double'][v] for v in sorted(order[m]['double'])], marker='+', linewidth=1.1, label="double " + m)

for N in random['float']:
    ax1.plot(np.ones(len(random['float'][N])) * N, random['float'][N] , 'bx')

for N in random['double']:
    ax1.plot(np.ones(len(random['double'][N])) * N, random['double'][N] , 'gx')

ax1.set_ylabel('L^2-norm |sim. - exact|')
ax1.set(xlabel='dx', title='Order')
ax1.legend()
ax1.grid(True)

outputCurve("plot/order-%s-%s-%s.dat" % (args.project_name, args.case, 'float'), sorted(order['nearest']['float']), [order['nearest']['float'][v] for v in sorted(order['nearest']['float'])])
outputCurve("plot/order-%s-%s-%s.dat" % (args.project_name, args.case, 'double'), sorted(order['nearest']['double']), [order['nearest']['double'][v] for v in sorted(order['nearest']['double'])])
outputCurve("plot/sigma-%s-%s-%s.dat" % (args.project_name, args.case, 'float'), sorted(sigma['float']), [sigma['float'][v] for v in sorted(sigma['float'])])
outputCurve("plot/refline-%s-%s.dat" % (args.project_name, args.case), x, y)

outputPoint("plot/order-%s-%s-%s_dot.dat" % (args.project_name, args.case, 'float'), random['float'])
outputPoint("plot/order-%s-%s-%s_dot.dat" % (args.project_name, args.case, 'double'), random['double'])



fig.tight_layout()

plt.show()
