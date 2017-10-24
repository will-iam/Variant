#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
import sys
import os
import numpy as np
import config
from collections import *
from shutil import rmtree
from script.launcher import launch_test, case_exist
import script.io as io

COLOR_BLUE = '\x1b[1;36m'
COLOR_ENDC = '\x1b[0m'

# Performance attributes
perf_dtypes = [('initTime', int), ('finalizeTime', int), ('nIterations', int), ('loopTime', int), ('totalExecTime', int), ('minComputeSum', int), ('maxComputeSum', int), ('maxIterationSum', int)]

perf_attrnames = [t[0] for t in perf_dtypes]
vi_dtypes = [('nSizeX', 'int'), ('nSizeY', 'int'), ('nSDD', 'int'), ('nSDD_X', 'int'), ('nSDD_Y', 'int'),
              ('nNeighbourSDD', 'int'), ('nPhysicalCells', 'int'),
              ('nOverlapCells', 'int'), ('nBoundaryCells', 'int'),
              ('nSDS', 'int'), ('SDSgeom', 'S10'), ('nThreads', 'int'),
              ('thread_iteration_type', 'S10'), ('SoA_or_AoS', 'S10')]
vi_attrnames = [t[0] for t in vi_dtypes]

parser = argparse.ArgumentParser(description="Performance measures", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("--case", type = str, help = "Case to test", required=True)
parser.add_argument("--machine", type = str, help = "Hostname of the test", default='unknown')
parser.add_argument("--max_thread_number", type = int, help = "Max. number of threads", default=1)
parser.add_argument("--max_proc_number", type = int, help = "Max. number of procs", default=1)
parser.add_argument("--nocompile", action='store_true', default=False, help = "Never compiles project before calling it")
parser.add_argument("--clean-compile", action='store_true', default=False, help = "Clean SCons compilation file")
parser.add_argument("--nocheck", action='store_true', default=False, help = "Never compare computed results to reference")
parser.add_argument("--vtune", action='store_true', default=False, help = "Enable vtune tool")
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

    iterationTimeDict = perf_info['iterationTime']
    computeTimeDict = perf_info['computeTime']

    sumComputeTimeMatrix = np.empty((len(perf_info['iterationTime']), len(iterationTimeDict[0])))
    iterationTimeMatrix = np.empty((len(perf_info['iterationTime']), len(iterationTimeDict[0])))

    for sdd in iterationTimeDict:
        # First Sum the compute time to make a new array.
        if len(computeTimeDict[sdd]) // 3 !=  len(iterationTimeDict[sdd]):
            print('The list sizes do not correspond.')
            sys.exit(1)

        counter = 0
        partialSum = 0
        index = 0
        iterationTimeMatrix[sdd] = iterationTimeDict[sdd]
        for t in computeTimeDict[sdd]:
            partialSum += t
            counter += 1
            if counter == 3:
                sumComputeTimeMatrix[sdd][index] = partialSum
                index += 1
                counter = 0
                partialSum = 0

    # For each value, find the min and the max.
    minComputeSum = np.sum(np.amin(sumComputeTimeMatrix, axis=0))
    maxComputeSum = np.sum(np.amax(sumComputeTimeMatrix, axis=0))
    maxIterationSum = np.sum(np.amax(iterationTimeMatrix, axis=0))

    perf_values.append(minComputeSum)
    perf_values.append(maxComputeSum)
    perf_values.append(maxIterationSum)

    return tuple(perf_values)

def join_result_data(resultPath, variant_info, perf_for_allruns, nCoresPerSDD, machine):
	# Joining variant infos from SDD data
    variant_info = np.rec.array(variant_info, vi_dtypes)
    stats_dtype = [dtype for dtype in vi_dtypes if dtype[0] in ['nNeighbourSDD', 'nOverlapCells', 'nBoundaryCells']]
    vi = [variant_info[dtype[0]][0] if dtype not in stats_dtype else
                            (np.mean(variant_info[dtype[0]]),
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
    final_data["nCoresPerSDD"] = nCoresPerSDD
    f = open(resultPath, 'a')
    if (os.stat(resultPath).st_size == 0):
        f.write(';'.join(final_data.keys()) + '\n')

    print(COLOR_BLUE + "Writing to results file" + COLOR_ENDC)
    f.write(';'.join([str(v) for v in final_data.values()]) + '\n')
    f.close()

def runTestBattery(engineOptionDict, testBattery):
    tmp_dir = config.tmp_dir
    project_name = engineOptionDict['project_name']

    # Checkt that all cases do exist
    for cn in testBattery:
        if not case_exist(project_name, cn):
            print('Test ', project_name, cn, "doesn't exist")
            sys.exit(1)

    for cn, testList in testBattery.items():
	    # Init results dir
        io.make_sure_path_exists(os.path.join(config.results_dir, project_name, cn))
        results_path = os.path.join(config.results_dir, project_name, cn, 'results_data.csv')

        # Launch tests and compare results
        print(COLOR_BLUE + "Start seeking optimal with case: " + COLOR_ENDC + project_name + '/' + cn)
        # Cleaning tmp directory for new case
        rmtree(tmp_dir, ignore_errors=True)
        for test in testList:
            # Launching runs for the test
            perf_for_allruns = []
            for n in range(test['nRuns']):
                # Check results and compare to reference (one check for all runs).
                if not args.nocheck and n == test['nRuns'] - 1:
                    compare_with_ref = True
                else:
                    compare_with_ref = False

                # Launch Test
                tmp_test_path, exec_time = launch_test(tmp_dir, engineOptionDict, cn, test, compare_with_ref)

                totalSDDNumber = test['nSDD'][0] * test['nSDD'][1]

                # Variant info
                variant_info = io.read_variant_info(tmp_test_path, totalSDDNumber)

                # Perfs info
                perf_info = io.read_perf_info(tmp_test_path, totalSDDNumber)

                print("Total ExecTime:", exec_time)
                print("Results for test: " + str(test) + " on run " + str(n) + " on " + str(test['nCoresPerSDD']) + " core(s).")
                perf_for_allruns.append(make_perf_data(tmp_test_path, exec_time, perf_info))
                print("perf_for_allruns", perf_for_allruns)

            # Join results
            join_result_data(results_path, variant_info, perf_for_allruns, test['nCoresPerSDD'], test['machine'])
