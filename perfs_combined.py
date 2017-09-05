#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import sys
import subprocess
import os
from shutil import copyfile, copytree, rmtree
from decimal import *
import itertools
import numpy as np
from timeit import default_timer as timer

import config
import script.compiler as compiler
import script.io as io
from perfs_common import *
from script.analytics import compare_data
from script.launcher import gen_ref_result, check_test, launch_test

# Define execution parameters
SDSgeom = 'line'
ratioThreadsCores = [1]
nTotalCores = args.max_proc_number
SDSsize = 512

#nSDD = []
#maxSDD = args.max_proc_number
#minSDD = args.max_proc_number / args.core_per_mpi
#i = 0
#while 4**i <= maxSDD:
#	if 4**i > minSDD:
#		nSDD.append(4**i)
#	i+=1 
nSDD = [1024]

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

tmp_dir = os.path.join(config.tmp_dir, 'perfs_combined')

cn = case_name
# Launch tests and compare results
print("Launching tests for case " + cn)

# Cleaning tmp directory for new case
rmtree(tmp_dir, ignore_errors=True)

# Getting/building referencephil collins son of man data for the case
if not args.nocheck:
    ref_test_path = os.path.join(case_dir, cn, "ref", "final")
    if not os.path.isdir(ref_test_path):
        print("Reference case does not exist, create ?")
        if raw_input() != 'y':
            sys.exit(0)
        gen_ref_result(this_dir, tmp_dir, project_name, cn, comp, mode, precision)

# Init results dir
io.make_sure_path_exists(os.path.join(config.results_dir, 'perfs_combined', cn))
results_path = os.path.join(config.results_dir, 'perfs_combined', cn, 'results_data.csv')


for ratio in ratioThreadsCores:
	for nsdd in nSDD:
	    # Building test
	    test = {}
	    ncpmpi = nTotalCores / nsdd
	    case_path = os.path.join(case_dir, cn)
	    test['SDSgeom'] = SDSgeom
	    test['nThreads'] = ncpmpi * ratio
	    dimSDD = int(nsdd**(0.5))
	    test['nSDD'] = (dimSDD, dimSDD)
	    #test['nSDD'] = (nsdd, 1)
	    test['nSDS'] = compute_sds_number(case_path, nsdd, SDSsize)

		# Launching runs for the test
	    perf_for_allruns = []
	    vi_for_allruns = []
	    for n in range(nruns):
		current_test_path, exec_time, variant_info = launch_test(this_dir,
			tmp_dir,
			project_name, cn, comp, mode, precision, std, bool_compile,
			test, ncpmpi, args.vtune)

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
		perf.append(ncpmpi)
		perf_for_allruns.append(tuple(perf))

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

print("\nTest successfully passed\n")

