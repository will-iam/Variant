#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from common import *
sys.path.insert(1, os.path.join(sys.path[0], 'sod'))
sys.path.insert(1, os.path.join(sys.path[0], 'sedov'))
sys.path.insert(1, os.path.join(sys.path[0], 'noh'))
import error_norm

# Find all results you can get.
ref_path = os.path.join(config.case_ref, args.project_name)

print("Looking for results in %s for case like %s ..." % (ref_path, args.case))
rawCaseList = [d for d in os.listdir(ref_path) if os.path.isdir(os.path.join(ref_path, d)) and d.startswith(args.case)]
q_name =  "rho" # args.quant # energy, u, rho

precisionList = [ 'weak8', 'weak9', 'weak10', 'weak11', 'weak12', 'weak13',
                  'weak14', 'weak15', 'weak16', 'weak17', 'weak18', 'weak19',
                  'weak20', 'weak21', 'weak22', 'weak23', 'weak24', 'weak25',
                  'weak26', 'weak27', 'weak28', 'weak29', 'weak30', 'weak31',
                  'weak32', 'float', 'double', 'long_double', 'quad']

# Compute order values
rounding = ['average', 'upward', 'downward', 'toward_zero', 'farthest', 'nearest']
order = dict()
for m in rounding:
    order[m] = {}
    for pr in precisionList:
        order[m][pr] = dict()

    for o in order[m]:
        for d in rawCaseList:
            f = os.path.join(ref_path, d, 'ref', o, m)
            if not os.path.isdir(f):
                continue
            if args.force or not os.path.isfile(os.path.join(f, 'error.dat')):
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
random = dict()
sigma = dict()
for pr in precisionList:
    random[pr] = dict()
    sigma[pr] = dict()

for o in random:
    for d in rawCaseList:
        f = os.path.join(ref_path, d, 'ref', o, 'random')
        if not os.path.isdir(f):
            continue

        if not args.force and not os.path.isfile(os.path.join(f, 'error.dat')):
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

for pr in random:
    print("Found %s references in %s precision for the random rounding mode." % (len(random[pr]), pr))

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

rounding_marker = {'average' : '8', 'upward': '^', 'downward':'v', 'toward_zero':'o', 'farthest':'>', 'nearest':'x'}
for m in rounding:
    for pr in precisionList:
        if pr in ['float, double']:
            lw = 1.2
        else:
            lw = 0.5
        if len(order[m][pr]):
            #ax1.plot(sorted(order[m][pr]), [order[m][pr][v] for v in sorted(order[m][pr])], marker=rounding_marker[m], linewidth=lw, label="%s %s" % (pr, m))
            ax1.plot(sorted(order[m][pr]), [order[m][pr][v] for v in sorted(order[m][pr])], marker=rounding_marker[m], linewidth=lw)
        

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
