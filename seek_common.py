#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
import sys
import os
import numpy as np
import script.io as io
import config
import script.compiler as compiler
from collections import *
from shutil import copyfile, copytree, rmtree
from script.analytics import compare_data
from script.launcher import gen_ref_result, check_test, launch_test
from script.build_case import get_ref_name

COLOR_BLUE = '\x1b[1;36m'
COLOR_ENDC = '\x1b[0m'

# Performance attributes
perf_dtypes = [('initTime', int), ('finalizeTime', int), ('nIterations', int), ('loopTime', int), ('totalExecTime', int), ('computeTime', int), ('synchronizeTime', int)]

perf_attrnames = [t[0] for t in perf_dtypes]
vi_dtypes = [('nSizeX', 'int'), ('nSizeY', 'int'), ('nSDD', 'int'), ('nSDD_X', 'int'), ('nSDD_Y', 'int'),
              ('nNeighbourSDD', 'int'), ('nPhysicalCells', 'int'),
              ('nOverlapCells', 'int'), ('nBoundaryCells', 'int'),
              ('nSDS', 'int'), ('SDSgeom', 'S10'), ('nThreads', 'int'),
              ('thread_iteration_type', 'S10'), ('SoA_or_AoS', 'S10')]
vi_attrnames = [t[0] for t in vi_dtypes]

parser = argparse.ArgumentParser(description="Performance measures", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("-c", type = str, help = "Case to test",
        required=True)
parser.add_argument("--machine", type = str, help = "Hostname of the test", default='unknown')

parser.add_argument("--max_thread_number", type = int, help = "Max. number of threads",
	default=1)
parser.add_argument("--max_proc_number", type = int, help = "Max. number of procs",
	default=1)
parser.add_argument("--nocompile", action='store_true', default=False,
        help = "Never compiles project before calling it")
parser.add_argument("--clean-compile", action='store_true',
        default=False, help = "Clean SCons compilation file")
parser.add_argument("--nocheck", action='store_true', default=False,
        help = "Never compare computed results to reference")
parser.add_argument("--vtune", action='store_true', default=False,
        help = "Enable vtune tool")
args = parser.parse_args()

def compute_sds_number2(total_cells, nSDD, SDSsize):
    return total_cells / (nSDD * SDSsize)

def compute_sds_number(case_path, nSDD, SDSsize):
    sys.path.append(case_path)
    import chars
    chars = reload(chars)
    totalCells = chars.Nx * chars.Ny
    del sys.path[-1]
    del chars
    return compute_sds_number2(totalCells, nSDD, SDSsize)

def make_perf_data(perfPath, execTime, perf_info):
    perf_values = list(io.read_perfs(perfPath).values())
    perf_values.append(execTime)
    perf_values.append(np.mean(perf_info['computeTime']))
    perf_values.append(np.mean(perf_info['synchronizeTime']))
    return tuple(perf_values)

def join_result_data(resultPath, variant_info, perf_for_allruns, ncpmpi, machine):
	# Joining variant infos from SDD data
    variant_info = np.rec.array(variant_info, vi_dtypes)
    stats_dtype = [dtype for dtype in vi_dtypes
						if dtype[0] in ['nNeighbourSDD',
							 'nOverlapCells',
							 'nBoundaryCells']]
    vi = [variant_info[dtype[0]][0] if dtype not in stats_dtype
						else (np.mean(variant_info[dtype[0]]),
                              np.median(variant_info[dtype[0]]),
							  np.min(variant_info[dtype[0]]),
							  np.max(variant_info[dtype[0]]),
							  np.std(variant_info[dtype[0]]))
						for dtype in vi_dtypes]

    vi_dict = dict()
    for i, n in enumerate(vi_attrnames):
        vi_dict[n] = vi[i]

	# Doing statistics on the perf runs
    perf_for_allruns = np.rec.array(perf_for_allruns, dtype=perf_dtypes)

    perf_dict = dict()
    for n in perf_attrnames:
        perf_dict[n] = perf_for_allruns[n]

	# Final and file data
    tmp_data = OrderedDict(list(vi_dict.items()) + list(perf_dict.items()))
    final_data = OrderedDict([(k, tmp_data[k]) for k in sorted(tmp_data)])
    final_data["machineName"] = machine
    final_data["nCoresPerSDD"] = ncpmpi
    f = open(resultPath, 'a')
    if (os.stat(resultPath).st_size == 0):
        f.write(';'.join(final_data.keys()) + '\n')

    print(COLOR_BLUE + "Writing to results file" + COLOR_ENDC)
    f.write(';'.join([str(v) for v in final_data.values()]) + '\n')
    f.close()

def runTestBattery(compileDict, testBattery):
    tmp_dir = config.tmp_dir
    this_dir = os.path.split(os.path.abspath(__file__))[0]

    for cn, testList in testBattery.items():
	    # Cleaning tmp directory for new case
        rmtree(tmp_dir, ignore_errors=True)

	    # Init results dir
        io.make_sure_path_exists(os.path.join(config.results_dir, cn))
        results_path = os.path.join(config.results_dir, cn, 'results_data.csv')

        # Getting/building reference for the case
        if not args.nocheck:
            ref_test_path = os.path.join("cases", compileDict['project_name'], cn, get_ref_name() , "final")
            if not os.path.isdir(ref_test_path):
                print("Reference case does not exist, create it.")
                gen_ref_result(this_dir, tmp_dir, compileDict['project_name'], cn,
                       compileDict['comp'], compileDict['mode'], compileDict['precision'], compileDict['std'])

        # Launch tests and compare results
        print(COLOR_BLUE + "Start seeking optimal with case: " + COLOR_ENDC + cn)

        for test in testList:
            # Launching runs for the test
            perf_for_allruns = []
            for n in range(test['nRuns']):
                current_test_path, exec_time, variant_info, perf_info = launch_test(this_dir,
                            tmp_dir,
                            compileDict['project_name'], cn, compileDict['comp'], compileDict['mode'], compileDict['precision'], compileDict['std'], compileDict['bool_compile'],
                            test, test['ncpmpi'], compileDict['vtune'])

                # Check results and compare to reference.
                if not args.nocheck:
                    result, qty, error_data = check_test(current_test_path, ref_test_path)
                    if result:
                        print("Compared with reference: OK.")
                    else:
                        print("Compared with reference: ERROR, different result for quantity " + qty)
                        sys.exit(1)
                print("Total ExecTime:", exec_time)
                print("Results for test: " + str(test) + " on run " + str(n) + " on " + str(test['ncpmpi']) + " core(s).")
                perf_for_allruns.append(make_perf_data(current_test_path, exec_time, perf_info))
                print("perf_for_allruns", perf_for_allruns)

            # Join results
            join_result_data(results_path, variant_info, perf_for_allruns, test['ncpmpi'], test['machine'])
