#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import sys
import subprocess
import os
import argparse
from shutil import copyfile, copytree, rmtree
from decimal import *
import itertools
import numpy as np
from scipy import stats

import config
import script.io as io
from params import params
from script.launcher import gen_ref_result, check_test, launch_test

parser = argparse.ArgumentParser(description="Regression test", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("-c", type = str, help = "Case to test")
parser.add_argument("--gdb", action='store_true',
        default=False, help = "Debug mode")
args = parser.parse_args()

project_name = args.project_name
comp = 'mpi'
mode = 'debug'
precision = 'double'
std = 'c++11'
bool_compile = True
gdb = args.gdb

this_dir = os.path.split(os.path.abspath(__file__))[0]
tmp_dir = config.tmp_dir

# Get case names from all directories in case/project_name/
case_dir = os.path.join("case", project_name)
if args.c != None:
    case_name = [args.c]
else :
    case_name = [name for name in os.listdir(case_dir)
            if os.path.isdir(os.path.join(case_dir, name))]

test_battery = [dict(itertools.izip(params, x)) for x in
        itertools.product(*params.itervalues())]

# Cleaning useless tests
test_battery = [test for test in test_battery if test['nThreads'] <= test['nSDS']]

# Launching tests
for cn in case_name:
    ref_test_path = os.path.join(case_dir, cn, "ref", "final")
    if not os.path.isdir(ref_test_path):
        print("Reference case does not exist, create ?")
        if raw_input() != 'y':
            sys.exit(0)
        gen_ref_result(this_dir, tmp_dir, project_name, cn, comp, precision)
    # Launch tests and compare results
    print("Launching tests for case " + cn)
    for i, test in enumerate(test_battery):
        current_test_path, exec_time, variant_info = launch_test(this_dir,
                tmp_dir,
                project_name, cn, comp, mode, precision, std, bool_compile,
                test, gdb)
        print("Results for test: " + str(test))
        result, qty, error_data = check_test(current_test_path, ref_test_path)
        test_battery[i] = dict(test.items() +
                io.read_perfs(current_test_path).items() + [('totalExecTime',
                    exec_time)])
        #subprocess.check_call(['python', 'script/gnuplotize.py',
        #                       '--quantity', 'rho', '-t', 'scalar',
        #                       current_test_path])
        #subprocess.check_call(['gnuplot', '-persist', '-e',
        #    'splot "' + os.path.join(current_test_path, "gnuplot_rho.dat") + '" using 1:2:3'
        #    + 'with points palette'])
        #subprocess.check_call(['gnuplot', '-persist', '-e',
        #    'plot "' + os.path.join(current_test_path, "gnuplot_rho.dat") + '" using 1:3'
        #    + 'with lines'])
        #subprocess.check_call(['python', 'script/gnuplotize.py',
        #                       '--quantity', 'rhou', '-t', 'vector',
        #                       current_test_path])
        #subprocess.check_call(['gnuplot', '-persist', '-e',
        #    'plot "' + os.path.join(current_test_path, "gnuplot_rhou.dat")
        #    + '" using 1:2:3:4:5 with vectors head filled lt 2 palette'])
        if result:
            print("OK.")
        else :
            print("ERROR: Different result for quantity " + qty)
            #print(zip(*np.nonzero(error_data)))
            sys.exit(1)

print("\nTest successfully passed\n")

