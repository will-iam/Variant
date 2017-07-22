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
#import pandas as pd

import config
import script.compiler as compiler
import script.io as io
from script.analytics import compare_data
import script.build_case as build_case
import script.sdd as sdd

parser = argparse.ArgumentParser(description="Regression test", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("-c", type = str, help = "Case to test")
args = parser.parse_args()

project_name = args.project_name
comp = 'mpi'
mode = 'release'
precision = 'double'
std = 'c++11'

parameters = {}
#parameters['nSDD_X'] = [1, 2, 5, 10]
#parameters['nSDD_Y'] = [1, 2, 5, 10]
#parameters['nSDS'] = [1, 5, 10]
#parameters['SDSgeom'] = ['line']
#parameters['nThreads'] = [1, 8, 32]

parameters['nSDD_X'] = [1, 2]
parameters['nSDD_Y'] = [1, 2]
parameters['nSDS'] = [1, 5]
parameters['SDSgeom'] = ['line']
parameters['nThreads'] = [1, 8]
this_dir = os.path.split(os.path.abspath(__file__))[0]

# Get case names from all directories in case/project_name/
case_dir = os.path.join("case", project_name)
if args.c != None:
    case_name = [args.c]
    print(case_name)
else :
    case_name = [name for name in os.listdir(case_dir)
            if os.path.isdir(os.path.join(case_dir, name))]
    print(case_name)

test_battery = [dict(itertools.izip(parameters, x)) for x in
        itertools.product(*parameters.itervalues())]

def gen_ref_result(cn):
    test = test_battery[0]
    io.make_sure_path_exists(ref_test_path)
    return launch_test(test, cn, "ref")

def check_test(test_path, ref_path):
    return compare_data(ref_path, test_path, ["rho"])

def launch_test(test, cn, output_path_in_case_dir = "tmp"):
    # Build case
    case_path = build_case.build_case(this_dir, project_name, cn,
            output_path_in_case_dir)

    # Add exec options
    io.write_exec_options(case_path, test['nSDD_X'] * test['nSDD_Y'],
            test['nSDD_X'], test['nSDD_Y'],
            test['nSDS'], test['SDSgeom'], test['nThreads'])

    # Split case for SDDs into tmp directory
    input_path = os.path.join(config.tmp_dir, "init")
    rmtree(input_path, ignore_errors=True)
    io.make_sure_path_exists(input_path)
    usc = sdd.split_domain(case_path, input_path, test['nSDD_X'],
            test['nSDD_Y'])
    usc_bc = sdd.split_bc(case_path, input_path)
    for q_str in ['rho', 'ux', 'uy']:
        sdd.split_quantity(case_path, input_path, q_str, usc)

    # Copying exec options in input path too
    io.write_exec_options(input_path, test['nSDD_X'] * test['nSDD_Y'],
            test['nSDD_X'], test['nSDD_Y'],
            test['nSDS'], test['SDSgeom'], test['nThreads'])
    copyfile(os.path.join(case_path, 'scheme_info.dat'),
             os.path.join(input_path, 'scheme_info.dat'))

    # Building output paths (the engine cannot create them itself)
    output_path = os.path.join(config.tmp_dir, "final")
    rmtree(output_path, ignore_errors=True)
    copytree(input_path, output_path)

    # Compile engine and call it
    engine = compiler.Engine(project_name, comp, mode, precision, std)
    nprocs = test['nSDD_X'] * test['nSDD_Y']
    engine.run(input_path, output_path, nprocs)

    final_path = os.path.join(case_dir, cn,
            output_path_in_case_dir, "final")

    # Copying perf results to final path
    copyfile(os.path.join(output_path, 'perfs.dat'),
             os.path.join(final_path, 'perfs.dat'))

    # Merge back
    sdd.merge_domain(output_path, final_path)
    sdd.merge_quantity(output_path, final_path, 'rho')

    return final_path

# Launching tests
for cn in case_name:
    ref_test_path = os.path.join(case_dir, cn, "ref", "final")
    if not os.path.isdir(ref_test_path):
        print("Reference case does not exist, create ?")
        if raw_input() != 'y':
            sys.exit(0)
        gen_ref_result(cn)
    # Launch tests and compare results
    print("Launching tests for case " + cn)
    for i, test in enumerate(test_battery):
        current_test_path = launch_test(test, cn)

        print("Results for test: " + str(test))
        result = check_test(current_test_path, ref_test_path)
        test_battery[i] = dict(test.items() + io.read_perfs(current_test_path).items())
        if result:
            print("OK.")
        else :
            print("ERROR: Different result!")
            sys.exit(1)
        #subprocess.check_call(['python', 'script/gnuplotize.py',
        #                       '--quantity', 'rho',
        #                       current_test_path])
        #subprocess.check_call(['gnuplot', '-persist', '-e',
        #    'splot "' + os.path.join(current_test_path, "gnuplot_rho.dat") + '" using 1:2:3'])

print("\nTest successfully passed\n")

# Results
print("Results")
print(np.matrix([test.values() for test in test_battery]))

