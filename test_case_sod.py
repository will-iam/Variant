#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import sys
import os
import subprocess
import argparse
from decimal import Decimal
import numpy as np
from shutil import rmtree, copyfile
import matplotlib.pyplot as plt
from math import log
import collections

import config
import script.io as io
from script.launcher import launch_test
import script.analytics as an

parser = argparse.ArgumentParser(description="Regression test", prefix_chars='-')
parser.add_argument("--conservative", action='store_true',
    default=False, help="Use the conservative scheme")
parser.add_argument("--opt", action='store_true',
    default=False, help="Use the optimized scheme")
args = parser.parse_args()

project_name = ''
if args.opt:
    project_name = 'hydrodynamicsOpt'
elif args.conservative:
    project_name = 'conservativeHydrodynamics'
else:
    project_name = 'hydrodynamics'
case_name = 'sod'
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

result_path = []

Ncells = [64, 256, 1024]

for N in Ncells:#, 2048]:#, 4096]:#[16, 32]:#, 64, 128, 256, 512, 1024, 2048, 4096]:
    cn = case_name + '_' + str(N)
    case_dir = os.path.join('case', project_name, cn)

    # Launch test
    rmtree(tmp_dir, ignore_errors=True)
    final_path, _, _ = launch_test(this_dir, tmp_dir,
        project_name, cn, comp, mode, precision, std, bool_compile,
        test, gdb)
    #final_path = os.path.join("tmp", "full_domain")

    # Check quantity conservations
    init_path = os.path.join('case', project_name, cn, 'tmp', 'init')
    dx, dy, rho = io.read_quantity(final_path, 'rho')
    rho_final_mass = an.mass(rho, dx, dy)
    dx, dy, rho_init = io.read_quantity(init_path, 'rho')
    rho_init_mass = an.mass(rho_init, dx, dy)
    print(rho_final_mass - rho_init_mass)

    # Gnuplotize solution
    result_path.append(os.path.join('results', 'sod', cn))

    # Rho is already done

    # Velocity u_x
    _, _, rhou_x = io.read_quantity(final_path, 'rhou_x')
    u_x = np.copy(rhou_x)
    for i in range(u_x.shape[0]):
        for j in range(u_x.shape[1]):
            u_x[i][j] = rhou_x[i][j] / rho[i][j]
    io.write_quantity_from_array(final_path, u_x, final_path, 'u_x')

    # Energy and pressure
    _, _, rhoe = io.read_quantity(final_path, 'rhoe')
    e = np.copy(rhoe)
    P = np.copy(rhoe)
    for i in range(e.shape[0]):
        for j in range(e.shape[1]):
            e[i][j] = rhoe[i][j] / rho[i][j]
            P[i][j] = Decimal('0.4') * rhoe[i][j]
    io.write_quantity_from_array(final_path, e, final_path, 'e')
    io.write_quantity_from_array(final_path, P, final_path, 'P')

    # Gnuplotize all quantities
    for qty_name in ['rho', 'u_x', 'e', 'P']:
        subprocess.check_call(['python', 'script/gnuplotize.py',
                               '--quantity', qty_name, '-t', 'scalar',
                               final_path])
        copyfile(os.path.join(final_path, 'gnuplot_' + qty_name + '.dat'),
                result_path[-1] + '_' + qty_name +'.dat')

# Gnuplot all quantities

for i, qty in enumerate(['rho', 'u_x', 'P', 'e']):
    gplt_command = ''
    if qty in ['e', 'u_x']:
        gplt_command += 'set key left; '
    gplt_command += 'set terminal postscript enhanced dashed eps font'
    gplt_command += ' "DejaVu Serif,20";'
    gplt_command += 'set output "sod_' + qty + '.eps"; plot '

    # Computed results for various dx
    for j, rp in enumerate(result_path):
        gplt_command += '"' + rp + '_' + qty
        gplt_command += '.dat" using 1:3 with linespoints pt 0 lw 2 lt ' + str(j+2)
        gplt_command += 'lc "black" title "' + str(Ncells[j]) + ' cells", '
        #gplt_command += '.dat" using 1:3 lt -1 pt ' + str(j+3) + ', '
    # Analytical solution data
    gplt_command += '"' + os.path.join('results', 'sod', 'sod_as.dat')
    gplt_command += '" using 1:' + str(i + 2) + ' with lines pt 0 lc "red" lt 1 lw 3 title "Analytical solution";'

    subprocess.check_call(['gnuplot', '-persist', '-e',
                           gplt_command])


