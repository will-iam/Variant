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
#import matplotlib.pyplot as plt

import config
import script.compiler as compiler
import script.io as io
from perfs_common import *
from script.analytics import compare_data
from script.launcher import gen_ref_result, check_test, launch_test

# Define execution parameters
params = {}
params['nSDS'] = [1]
params['SDSgeom'] = ['line']
params['nThreads'] = [1]
SDD_powersOfTwo = []
i = 0
while 2**i <= args.max_proc_number:
    SDD_powersOfTwo.append(i)
    i += 1
SDD_configs = []
nNeighbours = []

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
case_name = args.c

tmp_dir = os.path.join(config.tmp_dir, 'perfs_sdd_strongscal')

# Building test battery from parameters
test_battery = [dict(itertools.izip(params, x)) for x in
        itertools.product(*params.itervalues())]

boxplots_data = []
min_data = []
max_data = []

# nSDD = 2**p
for p in SDD_powersOfTwo:

    # Different SDD splits
    for i in range(p+1):
        SDD_config = (2**i, 2**(p-i))
        params['nSDD'] = [SDD_config]
        SDD_configs.append(2**p)

        # Cleaning tmp directory for new case
        rmtree(tmp_dir, ignore_errors=True)

        cn = case_name

        # Building test battery from parameters
        test_battery = [dict(itertools.izip(params, x)) for x in
                itertools.product(*params.itervalues())]

        # Getting/building referencephil collins son of man data for the case
        if not args.nocheck:
            ref_test_path = os.path.join(case_dir, cn, "ref", "final")
            if not os.path.isdir(ref_test_path):
                print("Reference case does not exist, create ?")
                if raw_input() != 'y':
                    sys.exit(0)
                gen_ref_result(this_dir, tmp_dir, project_name, cn, comp, precision)

        # Init results dir
        io.make_sure_path_exists(os.path.join(config.results_dir,
            'perfs_sdd_strongscal', cn))
        results_path = os.path.join(config.results_dir, 'perfs_sdd_strongscal', cn, 'results_data.csv')

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
                    test, args.core_per_mpi, args.vtune)

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
                perf = io.read_perfs(current_test_path).values()
                perf.append(exec_time)
		perf.append(args.core_per_mpi)
                perf_for_allruns.append(tuple(perf))

                # Gnuplot final data
                #subprocess.check_call(['python', 'script/gnuplotize.py',
                #                       '--quantity', 'rho',
                #                       current_test_path])
                #subprocess.check_call(['gnuplot', '-persist', '-e',
                #    'splot "' + os.path.join(current_test_path, "gnuplot_rho.dat") + '" using 1:2:3'])

                if not args.nocheck:
                    result, qty, error_data = check_test(current_test_path, ref_test_path)
                    if result:
                        print("OK.")
                    else :
                        print("ERROR: Different result for quantity " + qty)
                        #print(zip(*np.nonzero(error_data)))
                        sys.exit(1)

            vi_dict = dict()
            for i, n in enumerate(vi_attrnames):
                vi_dict[n] = vi[i]
            nNeighbours.append(vi_dict['n_neighbourSDD'][0])

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
            boxplots_data.append(perf_for_allruns['computeTime'])
            min_data.append(min(perf_for_allruns['computeTime']))
            max_data.append(max(perf_for_allruns['computeTime']))

# Plotting boxplots for stats
# fig = plt.figure(0, figsize=(9, 6))
# ax = fig.add_subplot(211)
# ax.boxplot(boxplots_data, positions=SDD_configs)
# ax.plot(SDD_configs, min_data)
# ax.plot(SDD_configs, max_data)
# ax.set_xlabel("Number of SDDs")
# ax.set_ylabel("Computing time")

# ax = fig.add_subplot(212)
# ax.boxplot(boxplots_data, positions=nNeighbours)
# ax.plot(nNeighbours, median_data)
# ax.set_xlabel("Average number of neighbour SDDs per SDD")
# ax.set_ylabel("Computing time")

# plt.legend()
# plt.show()

print("\nTest successfully passed\n")

