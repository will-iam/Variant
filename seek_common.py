#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
import argparse
import sys
import os
import numpy as np
import config
from collections import *
from shutil import rmtree
from script.launcher import launch_test, case_exist
import script.rio as io
import datetime
import copy

COLOR_BLUE = '\x1b[1;36m'
COLOR_ENDC = '\x1b[0m'
COLOR_GREEN = '\033[92m'
COLOR_WARNING = '\033[93m'

# Performance attributes
perf_dtypes = [('initTime', int), ('finalizeTime', int), ('nIterations', int), ('loopTime', int), ('totalExecTime', int), ('minComputeSum', int), ('maxComputeSum', int), ('maxIterationSum', int), ('endTime', 'S10')]

perf_attrnames = [t[0] for t in perf_dtypes]
vi_dtypes = [('nSizeX', 'int'), ('nSizeY', 'int'), ('nSDD', 'int'), ('nSDD_X', 'int'), ('nSDD_Y', 'int'),
              ('nNeighbourSDD', 'int'), ('nPhysicalCells', 'int'),
              ('nOverlapCells', 'int'), ('nBoundaryCells', 'int'),
              ('nSDS', 'int'), ('SDSgeom', 'S10'), ('nThreads', 'int'), ('nCommonSDS', 'int'),
              ('thread_iteration_type', 'S10'), ('SoA_or_AoS', 'S10')]
vi_attrnames = [t[0] for t in vi_dtypes]

parser = argparse.ArgumentParser(description="Performance measures", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("--case", type = str, help = "Case to test", required=True)
parser.add_argument("--machine", type = str, help = "Hostname of the test", default='unknown')
parser.add_argument("--core", type = int, help = "Max. number of cores available", default=1)
parser.add_argument("--nocompile", action='store_true', default=False, help = "Never compiles project before calling it")
parser.add_argument("--clean-compile", action='store_true', default=False, help = "Clean SCons compilation file")
parser.add_argument("--nocheck", action='store_true', default=False, help = "Never compare computed results to reference")
parser.add_argument("--fastref", action='store_true', default=False, help = "Build ref only with given parameters")
parser.add_argument("--forceref", action='store_true', default=False, help = "Build ref even if already present")
parser.add_argument("--vtune", action='store_true', default=False, help = "Enable vtune tool")
parser.add_argument("--debug", action='store_true', default=False, help = "Enable debugging compilation option -g -O0")
parser.add_argument("--gdb", action='store_true', default=False, help = "Enable debugging tool")
parser.add_argument("--test", action='store_true', default=False, help = "Show test to be run")
parser.add_argument("--jobname", type = str, help = "On script to rule them all (the jobs).", default='unknown')
parser.add_argument("--valgrind", action='store_true', default=False, help = "Run with valgrind memory check")
parser.add_argument("--verrou", type = str, default='', help = "Enable verrou tool: nearest \
    (default), upward, downward, toward zero are IEEE-754 compliant modes,\
    random (asynchronous CESTAC method), average \"uniform_absolute output randomization\"\
    in the MCA literature")

args = parser.parse_args()

# Get case names from all directories in case/project_name/
case_name = args.case
engineOptionDict = {
'project_name': args.project_name,
'compiler': 'mpi',
'mode': 'release' if not args.debug else 'debug',
'precision': 'double',
'std': 'c++14',
'must_compile': not args.nocompile,
'vtune': args.vtune,
'gdb' : args.gdb,
'valgrind' : args.valgrind,
'node_number' : int(np.ceil(float(args.core) /config.core_per_node)),
'verrou' : None if not args.verrou else args.verrou
}

# Define execution parameters
nTotalCores = args.core
nCoresPerNode = config.core_per_node

# Define les min/max SDDs
minSdd = int(np.log2(nTotalCores // nCoresPerNode)) if nTotalCores >= nCoresPerNode else nTotalCores
maxSdd = int(np.log2(nTotalCores)) + 1

# Clean compile if requested.
if args.clean_compile:
    import script.compiler as compiler
    compiler.Engine(engineOptionDict, False, True)
    print("Cleaned target")
    sys.exit(0)

def compileTestBattery(testList, SDSgeom, nruns = 1):
    battery = dict()
    for e in testList:
        for k, tl in e.items():
            if k not in battery:
                battery[k] = tl
            else:
                battery[k] = battery[k] + tl

    totalTestNumber = 0
    for k, tl in battery.items():
        print("%s test type(s) on case %s" % (len(tl), k))
        for t in tl:
            # add the number of tests.
            t['nRuns'] = nruns

            # add the machine on which is run the test
            t['machine'] = args.machine

            # add SDS geometry here
            t['SDSgeom'] = SDSgeom

            totalTestNumber += t['nRuns']
            print("\t%s" % t)
    print("%s run(s) to perform." % totalTestNumber)

    return battery

def weakSDD(initSize, ratioThreadsCores, SDSratioList, square = True):
    testBattery = {}
    caseSizeX = initSize // 2
    caseSizeY = initSize
    for p in [0, 1, 2, 3, 4, 5, 6]:
    	# Defining case directory
        if p % 2 == 1:
            caseSizeY = caseSizeY * 2
        else:
            caseSizeX = caseSizeX * 2
        cn = case_name + str(caseSizeX) + 'x' + str(caseSizeY)

        for ratio in ratioThreadsCores:
            initP = 0
            if square == True:
                initP = p // 2
            for i in range(initP, p // 2 + 1):
                test = {}
                test['nSDD'] = (2**i, 2**(p-i))
                nsdd = test['nSDD'][0] * test['nSDD'][1]
                for SDSratio in SDSratioList:
                    # Exploration strong SDS, nCoresPerSDD = nTotalCores / nsdd
                    test['nCoresPerSDD'] = 1

                    # Pour un calcul à charge/ressource constante
                    test['nThreads'] = np.max([1, int(test['nCoresPerSDD'] * ratio)])

                    # Définition du nombre de SDS
                    test['nSDS'] = test['nThreads']

                    # add the common SDS size
                    test['nCommonSDS'] = 0

                    # Finally add the test in the battery
                    if cn not in testBattery.keys():
                        testBattery[cn] = []
                    testBattery[cn].append(copy.copy(test))
    return testBattery

def weakSDS(initSize, ratioThreadsCores, SDSratioList, SDScommonDivider, exploredPower = range(0, 7)):
    testBattery = {}
    caseSizeX = initSize // 2
    caseSizeY = initSize
    for p in range(0, 7):
    	# Defining case directory
        if p % 2 == 1:
            caseSizeY = caseSizeY * 2
        else:
            caseSizeX = caseSizeX * 2

        if p not in exploredPower:
            continue

        cn = case_name + str(caseSizeX) + 'x' + str(caseSizeY)

        for ratio in ratioThreadsCores:
            test = {}
            test['nSDD'] = (1, 1)
            for SDSratio in SDSratioList:
                # Exploration strong SDS, nCoresPerSDD = nTotalCores / nsdd
                nCoresPerSDD = 2**p

                # élimine cas impossible
                if nCoresPerSDD > nTotalCores:
                    continue

                test['nCoresPerSDD'] = nCoresPerSDD

                # Pour un calcul à charge/ressource constante
                test['nThreads'] = int(nCoresPerSDD * ratio)
                if test['nThreads'] <= 0:
                    continue

                # Définition du nombre de SDS
                test['nSDS'] = int(test['nThreads'] * SDSratio)

                # the maximum number is the number of cells.
                if test['nSDS'] > caseSizeX * caseSizeY:
                    continue

                # Finally add the test in the battery
                if cn not in testBattery.keys():
                    testBattery[cn] = []

                # add the common SDS size
                for divider in SDScommonDivider:
                    test['nCommonSDS'] = int(test['nSDS'] * divider)
                    testBattery[cn].append(copy.copy(test))

    return testBattery

def strongSDS(caseSizeXY, ratioThreadsCores, SDSratioList, SDScommonDivider, corePerSDDList = [nTotalCores]):
    """
    Exploration strong SDS, nCoresPerSDD = nTotalCores / nSDD avec nSDD = 1
    """
    testBattery = {}
    for nCoresPerSDD in corePerSDDList:
    	# Defining case directory
        cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
        for ratio in ratioThreadsCores:
            test = {}
            test['nSDD'] = (1, 1)
            for SDSratio in SDSratioList:

                # élimine cas impossible
                if nCoresPerSDD > nTotalCores:
                    continue

                test['nCoresPerSDD'] = nCoresPerSDD

                # Pour un calcul à charge/ressource constante
                test['nThreads'] = int(nCoresPerSDD * ratio)
                if test['nThreads'] <= 0:
                    continue

                # Définition du nombre de SDS
                test['nSDS'] = int(test['nThreads'] * SDSratio)

                # the maximum number is the number of cells.
                if test['nSDS'] > caseSizeXY[0] * caseSizeXY[1]:
                    continue

                # Finally add the test in the battery
                if cn not in testBattery.keys():
                    testBattery[cn] = []

                # add the common SDS size
                for divider in SDScommonDivider:
                    test['nCommonSDS'] = int(test['nSDS'] * divider)
                    testBattery[cn].append(copy.copy(test))

    return testBattery

def strongSDD(caseSizeXY, ratioThreadsCores, SDDSizeList, SDSratioList, square = False):

    testBattery = {}
    # Defining case directory
    cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
    for ratio in ratioThreadsCores:
        for p in SDDSizeList:
            initP = 0
            if square == True:
                initP = p // 2
            for i in range(initP, p // 2 + 1):
                test = {}
                test['nSDD'] = (2**i, 2**(p-i))
                nsdd = test['nSDD'][0]*test['nSDD'][1]
                for SDSratio in SDSratioList:
                    nCoresPerSDD = 1

                    # élimine cas impossible
                    if nCoresPerSDD > nTotalCores / nsdd:
                        continue

                    test['nCoresPerSDD'] = nCoresPerSDD
                    # Pour un calcul à charge/ressource constante
                    test['nThreads'] = int(nCoresPerSDD * ratio)
                    if test['nThreads'] <= 0:
                        continue

                    # Définition du nombre de SDS
                    test['nSDS'] = test['nThreads']

                    # add the common SDS size
                    test['nCommonSDS'] = 0

                    # Finally add the test in the battery
                    if cn not in testBattery.keys():
                        testBattery[cn] = []
                    testBattery[cn].append(copy.copy(test))
    return testBattery

def explore(caseSizeXY, ratioThreadsCores, SddSizeList, SDSratioList, SDScommonDivider, square = True):

    testBattery = {}
    # Defining case directory
    cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
    for ratio in ratioThreadsCores:
        for p in SddSizeList:
            # Different SDD splits, nSDD = 2**p
            initP = 0
            if square == True:
                initP = p // 2
            for i in range(initP, p // 2 + 1):
                test = {}
                test['nSDD'] = (2**i, 2**(p-i))

                nsdd = test['nSDD'][0]*test['nSDD'][1]
                for SDSratio in SDSratioList:
                    # Exploration strong SDS, nCoresPerSDD = nTotalCores / nsdd
                    test['nCoresPerSDD'] = float(nTotalCores) / nsdd

                    # Pour un calcul à charge/ressource constante
                    test['nThreads'] = np.max([1, int(test['nCoresPerSDD'] * ratio)])

                    # Définition du nombre de SDS
                    test['nSDS'] = int(test['nThreads'] * SDSratio)

                    # the maximum number is the number of cells.
                    if test['nSDS'] > caseSizeXY[0] * caseSizeXY[1]:
                        continue

                    if cn not in testBattery.keys():
                        testBattery[cn] = []

                    # add the common SDS size
                    for divider in SDScommonDivider:
                        test['nCommonSDS'] = int(test['nSDS'] * divider)
                        # Finally add the test in the battery
                        testBattery[cn].append(copy.copy(test))

    return testBattery

def exploreCaseSize(initSize, ratioThreadsCores, SddSizeList, SDSratioList, SDScommonDivider):
    testBattery = {}
    caseSizeX = initSize // 2
    caseSizeY = initSize
    for p in range(0, 7):
    	# Defining case directory
        if p % 2 == 1:
            caseSizeY = caseSizeY * 2
        else:
            caseSizeX = caseSizeX * 2

        for k, tl in explore((caseSizeX, caseSizeY), ratioThreadsCores, SddSizeList, SDSratioList, SDScommonDivider).items():
            testBattery[k] = tl

    return testBattery

def make_perf_data(perfPath, execTime, perf_info, endTime):
    perf_values = list(io.read_perfs(perfPath).values())
    perf_values.append(execTime)

    iterationTimeDict = perf_info['iterationTime']
    computeTimeDict = perf_info['computeTime']

    sumComputeTimeMatrix = np.empty((len(perf_info['iterationTime']), len(iterationTimeDict[0])))
    iterationTimeMatrix = np.empty((len(perf_info['iterationTime']), len(iterationTimeDict[0])))

    # Detect the ratio between computeTime and iterationTime.
    if len(computeTimeDict[0]) <  len(iterationTimeDict[0]):
        print("There is more iteration time vallues than computation time values. You didn't get what an iteration time is.")
        sys.exit(1)
    ratioCperI = len(computeTimeDict[0]) // len(iterationTimeDict[0])
 
    for sdd in iterationTimeDict:
        # First Sum the compute time to make a new array.
        if len(computeTimeDict[sdd]) // ratioCperI !=  len(iterationTimeDict[sdd]):
            print('The list sizes do not correspond.')
            sys.exit(1)

        counter = 0
        partialSum = 0
        index = 0
        iterationTimeMatrix[sdd] = iterationTimeDict[sdd]
        for t in computeTimeDict[sdd]:
            partialSum += t
            counter += 1
            if counter == ratioCperI:
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

    perf_values.append(endTime)

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
    if args.test == True:
        return

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
        restultTag = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        results_path = os.path.join(config.results_dir, project_name, cn, 'data-' + args.jobname + '-' + restultTag + '.csv')

        # Launch tests and compare results
        print(COLOR_BLUE + "Start seeking optimal with case: " + COLOR_ENDC + project_name + '/' + cn)
        # Cleaning tmp directory for new case
        rmtree(tmp_dir, ignore_errors=True)
        for test in testList:
            # Launching runs for the test
            perf_for_allruns = []
            variant_info = None
            for n in range(test['nRuns']):
                # Check results and compare to reference (one check for all runs).
                if not args.nocheck and n == test['nRuns'] - 1:
                    compare_with_ref = True
                else:
                    compare_with_ref = False

                # Launch Test
                tmp_test_path, exec_time = launch_test(tmp_dir, engineOptionDict, cn, test, compare_with_ref, args.fastref, args.forceref)
                if tmp_test_path is None:
                    # This test was not performed.
                    continue

                totalSDDNumber = test['nSDD'][0] * test['nSDD'][1]

                # Variant info
                variant_info = io.read_variant_info(tmp_test_path, totalSDDNumber)

                # Perfs info
                perf_info = io.read_perf_info(tmp_test_path, totalSDDNumber)

                endTime = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
                print("endTime:", endTime)
                print("Total ExecTime:", exec_time)
                print("Results for test: " + str(test) + " on run " + str(n) + " on " + str(test['nCoresPerSDD']) + " core(s).")
                perf_for_allruns.append(make_perf_data(tmp_test_path, exec_time, perf_info, endTime))
                print("perf_for_allruns", perf_for_allruns)

            # Join results
            if variant_info is not None:
                join_result_data(results_path, variant_info, perf_for_allruns, test['nCoresPerSDD'], test['machine'])

    # Finally
    print(COLOR_GREEN + "\nTest successfully passed\n" + COLOR_ENDC)
