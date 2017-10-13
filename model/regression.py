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

import config
import script.io as io
from params import params
from script.launcher import gen_ref_result, check_test, launch_test
import script.compiler as compiler
from script.analytics import norm

parser = argparse.ArgumentParser(description="Regression test", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("-c", type = str, help = "Case to test")
parser.add_argument("--gdb", action='store_true',
        default=False, help = "Debug mode")
parser.add_argument("--vtune", action='store_true',
        default=False, help = "Execute with vtune")
parser.add_argument("--clean-compile", action='store_true',
        default=False, help = "Clean SCons compilation file")
parser.add_argument("--plot", action='store_true',
    default=False, help="Plot solutions")
parser.add_argument("--valgrind", action='store_true',
    default=False, help="Use valgrind memory leak checker")
parser.add_argument("--debug", action='store_true',
    default=False, help="Compile in debug mode")
args = parser.parse_args()

project_name = args.project_name
comp = 'mpi'
mode = 'debug' if args.debug else 'release'
precision = 'double'
std = 'c++11'
bool_compile = True


if args.clean_compile:
    engine = compiler.Engine(project_name, False, comp, mode, precision,
            std, True)
    print("Cleaned target")
    sys.exit(0)

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
        print("Reference case does not exist, create it.")
        gen_ref_result(this_dir, tmp_dir, project_name, cn, comp, mode, precision)
    # Launch tests and compare results
    print("Launching tests for case " + cn)
    for i, test in enumerate(test_battery):
        current_test_path, exec_time, variant_info = launch_test(this_dir,
                tmp_dir,
                project_name, cn, comp, mode, precision, std, bool_compile,
                test, 1, args.vtune, args.gdb, args.valgrind)
        if args.valgrind:
            raw_input()
        print("Results for test: " + str(test))
        result, qty, (dx, dy, error_data) = check_test(current_test_path, ref_test_path)
        test_battery[i] = dict(test.items() +
                io.read_perfs(current_test_path).items() + [('totalExecTime',
                    exec_time)])
        if args.plot:
            subprocess.check_call(['python', 'script/gnuplotize.py',
                                   '--quantity', 'rho', '-t', 'scalar',
                                   current_test_path])
            subprocess.check_call(['gnuplot', '-persist', '-e',
                'splot "' + os.path.join(current_test_path, "gnuplot_rho.dat") + '" using 1:2:3 '
                + 'with points palette'])
            subprocess.check_call(['gnuplot', '-persist', '-e',
                'plot "' + os.path.join(current_test_path, "gnuplot_rho.dat") + '" using 1:3 '
                + 'with lines'])
            subprocess.check_call(['python', 'script/gnuplotize.py',
                                   '--quantity', 'rhou', '-t', 'vector',
                                   current_test_path])
            subprocess.check_call(['gnuplot', '-persist', '-e',
                'plot "' + os.path.join(current_test_path, "gnuplot_rhou.dat")
                + '" using 1:2:3:4:5 with vectors head filled lt 2 palette'])
        if not result:
            print(norm(error_data, 2, dx, dy))
            raw_input()
            #sys.exit(1)

print("\nTest successfully passed\n")

