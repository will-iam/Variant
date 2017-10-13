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
args = parser.parse_args()

project_name = 'conservativeHydrodynamics' if args.conservative else 'hydrodynamics'
case_name = '2dsod'
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

cn = case_name
case_dir = os.path.join('case', project_name, cn)

# Launch test
rmtree(tmp_dir, ignore_errors=True)
final_path, _, _ = launch_test(this_dir, tmp_dir,
    project_name, cn, comp, mode, precision, std, bool_compile,
    test, gdb)

# Check quantity conservations
init_path = os.path.join('case', project_name, cn, 'tmp', 'init')
dx, dy, rho = io.read_quantity(final_path, 'rho')
rho_final_mass = an.mass(rho, dx, dy)
dx, dy, rho_init = io.read_quantity(init_path, 'rho')
rho_init_mass = an.mass(rho_init, dx, dy)
print(rho_final_mass - rho_init_mass)

# Gnuplotize solution
result_path = os.path.join('results', '2dsod', '2dsod')
io.make_sure_path_exists(os.path.join('results', '2dsod'))
subprocess.check_call(['python', 'script/gnuplotize.py',
                       '--quantity', 'rho', '-t', 'scalar',
                       final_path])
copyfile(os.path.join(final_path, 'gnuplot_rho.dat'),
        result_path + '_rho.dat')

# Gnuplot result
gplt_command = 'set nokey; \
set palette model CMY rgbformulae 7,5,15; set xrange [0:1];\
set yrange [0:1]; set terminal postscript enhanced eps font "Liberation\
 Mono,20";\
set output "2dsod.eps"; plot "'
gplt_command += result_path + '_rho.dat" using 1:2:3 with image'

subprocess.check_call(['gnuplot', '-persist', '-e',
                       gplt_command])


