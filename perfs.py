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
from timeit import default_timer as timer
from scipy import stats
import matplotlib.pyplot as plt

import config
import script.compiler as compiler
import script.io as io
from script.analytics import compare_data
from script.launcher import gen_ref_result, check_test, launch_test

COLOR_BLUE = '\x1b[1;36m'
COLOR_ENDC = '\x1b[0m'

parser = argparse.ArgumentParser(description="Performance measures", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("-c", type = str, help = "Case to test")
parser.add_argument("-p", type = str, help = "Paramaters module", default =
'params')
parser.add_argument("--nruns", type = int, help = "Number of runs per variant",
        default=1)
parser.add_argument("--nocompile", action='store_true', default=False,
        help = "Never compiles project before calling it")
args = parser.parse_args()

project_name = args.project_name
comp = 'mpi'
mode = 'release'
precision = 'double'
std = 'c++11'
nruns = args.nruns
bool_compile = not args.nocompile

this_dir = os.path.split(os.path.abspath(__file__))[0]

# Get case names from all directories in case/project_name/
case_dir = os.path.join("case", project_name)
if args.c != None:
    case_name = [args.c]
else :
    case_name = [name for name in os.listdir(case_dir)
            if os.path.isdir(os.path.join(case_dir, name))]

# Loading parameters
param_module = __import__(args.p)
params = param_module.params
tmp_dir = os.path.join(config.tmp_dir, args.p)

# Building test battery from parameters
test_battery = [dict(itertools.izip(params, x)) for x in
        itertools.product(*params.itervalues())]

# Cleaning useless tests
test_battery = [test for test in test_battery if test['nThreads'] <= test['nSDS']]

# Perfomance attributes
perf_dtypes = [('initTime', int), ('computeTime', int),
            ('totalExecTime', int)]
perf_attrnames = [t[0] for t in perf_dtypes]
vi_dtypes = [('n_SDD', 'int'), ('n_SDD_X', 'int'), ('n_SDD_Y', 'int'),
              ('n_neighbourSDD', 'int'), ('n_physicalCells', 'int'),
              ('n_overlapCells', 'int'), ('n_boundaryCells', 'int'),
              ('n_SDS', 'int'), ('SDSgeom', 'S10'), ('n_threads', 'int'),
              ('thread_iteration_type', 'S10'), ('SoA_or_AoS', 'S10')]
vi_attrnames = [t[0] for t in vi_dtypes]

# Launching tests
for cnumber, cn in enumerate(case_name):
    # Cleaning tmp directory for new case
    rmtree(tmp_dir, ignore_errors=True)

    # Getting/building reference data for the case
    ref_test_path = os.path.join(case_dir, cn, "ref", "final")
    if not os.path.isdir(ref_test_path):
        print("Reference case does not exist, create ?")
        if raw_input() != 'y':
            sys.exit(0)
        gen_ref_result(this_dir, tmp_dir, project_name, cn, comp, precision)

    boxplots_data = dict()
    median_data = dict()

    # Init results dir
    io.make_sure_path_exists(os.path.join(config.results_dir, cn, args.p))
    results_path = os.path.join(config.results_dir, cn, args.p, 'results_data.csv')

    # Launch tests and compare results
    print("Launching tests for case " + cn)
    for i, test in enumerate(test_battery):

        # Launching runs for one test
        perf_for_allruns = []
        vi_for_allruns = []
        for n in range(nruns):
            current_test_path, exec_time, variant_info = launch_test(this_dir,
                tmp_dir,
                project_name, cn, comp, mode, precision, std, bool_compile,
                test)

            # Joining variant infos from SDD data
            if n == 0:
                variant_info = np.rec.array(variant_info, vi_dtypes)
                stats_dtype = [dtype for dtype in vi_dtypes
                        if dtype[0] in ['n_neighbourSDD',
                                 'n_overlapCells',
                                 'n_boundaryCells']]
                vi = [variant_info[dtype[0]][0] if dtype not in stats_dtype
                        else (np.median(variant_info[dtype[0]]),
                              np.min(variant_info[dtype[0]]),
                              np.max(variant_info[dtype[0]]),
                              np.std(variant_info[dtype[0]]))
                        for dtype in vi_dtypes]

            print("Results for test: " + str(test) + " on run " + str(n))
            result, qty, error_data = check_test(current_test_path, ref_test_path)
            perf = io.read_perfs(current_test_path).values()
            perf.append(exec_time)
            perf_for_allruns.append(tuple(perf))

            # Gnuplot final data
            #subprocess.check_call(['python', 'script/gnuplotize.py',
            #                       '--quantity', 'rho',
            #                       current_test_path])
            #subprocess.check_call(['gnuplot', '-persist', '-e',
            #    'splot "' + os.path.join(current_test_path, "gnuplot_rho.dat") + '" using 1:2:3'])

            if result:
                print("OK.")
            else :
                print("ERROR: Different result for quantity " + qty)
                #print(zip(*np.nonzero(error_data)))
                sys.exit(1)

        vi_dict = dict()
        for i, n in enumerate(vi_attrnames):
            vi_dict[n] = vi[i]

        # Doing statistics on the perf runs
        perf_for_allruns = np.rec.array(perf_for_allruns,
                dtype=perf_dtypes)
        perf_dict = dict()
        for n in perf_attrnames:
            perf_dict[n] = perf_for_allruns[n]

        # Final and file data
        final_data = dict(vi_dict.items() + perf_dict.items())
        f = open(results_path, 'a')
        if (os.stat(results_path).st_size == 0):
            f.write(';'.join(final_data.keys()) + '\n')
        print(COLOR_BLUE + "Writing to results file" + COLOR_ENDC)
        f.write(';'.join([str(v) for v in final_data.values()]) + '\n')
        f.close()

        # Pyplot data
        boxplots_data[tuple(test.values())] = perf_for_allruns['computeTime']
        median_data[tuple(test.values())] = np.median(perf_for_allruns['computeTime'])

    # Plotting boxplots for stats
    fig = plt.figure(cnumber, figsize=(9, 6))
    ax = fig.add_subplot(111)
    ax.set_xticklabels([test['nThreads'] for test in test_battery])
    ax.boxplot(boxplots_data.values())
    ax.plot([i + 1 for i in range(len(median_data.values()))],
            median_data.values(), color='g')
    plt.show()

print("\nTest successfully passed\n")

