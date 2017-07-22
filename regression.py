#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import sys
import subprocess
import os
import argparse
from decimal import *

import script.compiler as compiler
import script.io as io
from script.analytics import compare_data
import script.build_case as build_case

parser = argparse.ArgumentParser(description="Regression test", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("-c", type = str, help = "Case to test")
args = parser.parse_args()

project_name = args.project_name
comp = 'intel'
mode = 'debug'
precision = 'double'
nSDS = [1, 5, 10]
nSDD = [1, 2, 5, 10, 25]
SDSgeom = ['line']
nThreads = [1, 8, 32]

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

test_battery = []
for nsds in nSDS:
    for nsdd in nSDD:
        for sdsgeom in SDSgeom:
            for nthreads in nThreads:
                test_battery.append({'nSDS': nsds,
                                     'nSDD': nsdd,
                                     'SDSgeom': sdsgeom,
                                     'nThreads': nthreads})

def gen_ref_result(cn):
    test = {'nSDS': 1,
            'nSDD': 1,
            'SDSgeom': 'line',
            'nThreads': 1}
    return launch_test(test, cn, "ref")

def launch_test(test, cn, output_path_in_case_dir = "tmp"):
    # Build case
    input_path = build_case.build_case(this_dir, project_name, cn,
            output_path_in_case_dir)

    # Add exec options
    io.write_exec_options(input_path, test['nSDD'], 1, test['nSDD'],
            test['nSDS'], test['SDSgeom'], test['nThreads'])

    # Compile engine and call it
    output_path = os.path.join(case_dir, cn,
            output_path_in_case_dir, "final")
    io.make_sure_path_exists(output_path)
    engine = compiler.Engine(project_name, comp, mode, precision)
    engine.run(input_path, output_path)

    return output_path

def check_test(test_path, ref_path):
    result = compare_data(ref_path, test_path, ["rho"])
    return result

# Launching tests
for cn in case_name:
    ref_test_path = os.path.join(case_dir, cn, "ref", "final")
    if not os.path.isdir(ref_test_path):
        print("Reference case does not exist, create ?")
        if raw_input() != 'y':
            sys.exit(0)
        io.make_sure_path_exists(ref_test_path)
        gen_ref_result(cn)
    # Launch tests and compare results
    print("Launching tests for case " + cn)
    for test in test_battery:
        current_test_path = launch_test(test, cn)
        print("Results for test: " + str(test))
        result = check_test(current_test_path, ref_test_path)
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

