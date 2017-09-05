#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import sys
import os
import subprocess
import argparse
from decimal import Decimal
import numpy as np
from shutil import rmtree
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from math import log, exp
import collections

import config
import script.io as io
from script.launcher import launch_test
import script.analytics as an

parser = argparse.ArgumentParser(description="Validation test for the advection\
upwind scheme", prefix_chars='-')
parser.add_argument("-c", type = str, help = "Case to test", required=True)
parser.add_argument("--plot", action='store_true',
    default=False, help="Plot solutions")
args = parser.parse_args()

project_name = 'transportUpwind'
case_name = args.c
comp = 'mpi'
mode = 'release'
precision = 'double'
std = 'c++11'
this_dir = os.path.split(os.path.abspath(__file__))[0]
tmp_dir = config.tmp_dir

bool_compile = True
gdb = False

this_dir = os.path.split(os.path.abspath(__file__))[0]
tmp_dir = config.tmp_dir

test = dict()
test['nSDD'] = (1, 1)
test['nSDS'] = 1
test['nThreads'] = 4
test['SDSgeom'] = 'line'

error_norms = collections.OrderedDict()

Ncells = [16, 32, 64, 128, 256]
for N in Ncells:
    cn = case_name + '_' + str(N)
    case_dir = os.path.join('case', project_name, cn)

    # Launch test
    rmtree(tmp_dir, ignore_errors=True)
    final_path, _, _ = launch_test(this_dir, tmp_dir,
        project_name, cn, comp, mode, precision, std, bool_compile,
        test, gdb)
    #final_path = os.path.join("tmp", "full_domain")

    # Compare to analytical solution
    sys.path.append(case_dir)
    import init as case
    case = reload(case)
    del sys.path[-1]

    # Generate analytical solution from case data
    analyt_sol = np.zeparser.add_argument("--conservative", action='store_true',
    default=False, help="Use the conservative scheme")
ros((case.Nx, case.Ny), dtype=np.dtype(Decimal))
    for i in range(analyt_sol.shape[0]):
        for j in range(analyt_sol.shape[1]):
            analyt_sol[i][j] = Decimal(str(case.rho_t(case.T,
                float(i) / case.Nx, float(j) / case.Ny)))
    dx, dy, computed_sol = io.read_quantity(final_path, "rho")

    del case

    # Gnuplotize solution
    if args.plot:
        #io.write_quantity_from_array(final_path, computed_sol, final_path, "error")
        subprocess.check_call(['python', 'script/gnuplotize.py',
                               '--quantity', 'rho', '-t', 'scalar',
                               final_path])
        gplt_command = 'set terminal postscript enhanced eps '
        gplt_command += 'font "Liberation Mono,20"; '
        gplt_command += 'set output "advection_' + str(N) + '.eps"; '
        gplt_command += 'set palette defined ( 0 0 0 0, 0.9 0.9 0.9 0.9 ); '
        gplt_command += 'splot "' + os.path.join(final_path, "gnuplot_rho.dat")
        gplt_command += '" using 1:2:3 with pm3d '
        gplt_command += 'title "' + str(N) + 'x' + str(N) + ' cells";'
        subprocess.check_call(['gnuplot', '-persist', '-e', gplt_command])

        if N == Ncells[-1]:
            io.write_quantity_from_array(final_path, analyt_sol, final_path,
                    "analytical_rho")
            subprocess.check_call(['python', 'script/gnuplotize.py',
                                   '--quantity', 'analytical_rho', '-t', 'scalar',
                                   final_path])
            gplt_command = 'set terminal postscript enhanced eps '
            gplt_command += 'font "Liberation Mono,20"; '
            gplt_command += 'set output "advection_analytical.eps"; '
            gplt_command += 'set palette defined (0 0 0 0, 0.9 0.9 0.9 0.9); '
            gplt_command += 'splot "' + os.path.join(final_path,
                    "gnuplot_analytical_rho.dat")
            gplt_command += '" using 1:2:3 with pm3d '
            gplt_command += 'title "Analytical solution";'
            subprocess.check_call(['gnuplot', '-persist', '-e', gplt_command])



    # Check norm of error
    error_norms[N] = an.norm(analyt_sol - computed_sol, 2, dx, dy)


# Compute order
print(error_norms)
print(error_norms.keys())
print(error_norms.values())
h = [1.0 / N for N in error_norms.keys()]
e = error_norms.values()
log_h = [log(he) for he in h]
log_e = [log(ee) for ee in e]
order, b = np.polyfit(log_h, log_e, 1)

# Plot norm results
plt.figure(1)
plt.xlabel("h")
plt.ylabel("L^2 norm of error")
ax = plt.gca()
ax.set_xscale('log')
ax.set_yscale('log')

plt.annotate("Order " + str(order)[:5], xy=(0.3, 0.5),
             xycoords="axes fraction")
plt.plot(h, e, marker='o', label='Computed values',
        linestyle='--')
plt.plot([min(h), max(h)], [exp(b + min(log_h) * order),
                            exp(b + max(log_h) * order)],
        label='Linear approximation')
plt.xlim([min(h) / 2, max(h) * 2])
plt.ylim([exp(b + min(log_h) * order) / 2,
          exp(b + max(log_h) * order) * 2])
plt.legend(loc='upper left')
#plt.plot([min(log_h), max(log_h)], [b + min(log_h) * order, b +\
#    max(log_h) * order])
plt.show()

print("Done")


