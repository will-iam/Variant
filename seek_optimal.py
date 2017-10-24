#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import sys
import itertools
from decimal import *
from seek_common import *
import script.compiler as compiler

# Get case names from all directories in case/project_name/
case_name = args.case

engineOptionDict = {
'project_name': args.project_name,
'compiler': 'mpi',
'mode': 'release',
'precision': 'double',
'std': 'c++14',
'must_compile': not args.nocompile,
'vtune': args.vtune,
'gdb' : False,
'valgrind' : False
}

# Define execution parameters
machine = args.machine
nTotalCores = args.max_proc_number
SDSgeom = 'line'
ratioThreadsCores = [1]
SDSratioList = [4]
nruns = 5
nCoresPerNode = 8

# Clean compile if requested.
if args.clean_compile:
    compiler.Engine(engineOptionDict, False, True)
    print("Cleaned target")
    sys.exit(0)

def weakSDD(initSize):
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
            # Different SDD splits, nSDD = 2**p
            for i in range(0, p/2 + 1):
                test = {}
                test['SDSgeom'] = SDSgeom
                test['nSDD'] = (2**i, 2**(p-i))
                nsdd = test['nSDD'][0]*test['nSDD'][1]
                for SDSratio in SDSratioList:
                    # Exploration strong SDS, nCoresPerSDD = nTotalCores / nsdd
                    nCoresPerSDD = 1

                    # élimine cas impossible
                    if nCoresPerSDD > nTotalCores / nsdd:
                        continue

                    test['nCoresPerSDD'] = nCoresPerSDD

                    # Pour un calcul à charge/ressource constante
                    test['nThreads'] = nCoresPerSDD * ratio
                    if test['nThreads'] <= 0:
                        continue

                    # Définition du nombre de SDS
                    test['nSDS'] = test['nThreads'] * SDSratio

                    # the maximum number is the number of cells.
                    if test['nSDS'] > caseSizeX * caseSizeY:
                        continue

                    # add the number of tests.
                    test['nRuns'] = nruns

                    # add the machine on which is run the test
                    test['machine'] = machine

                    # Finally add the test in the battery
                    if cn not in testBattery.keys():
                        testBattery[cn] = []
                    testBattery[cn].append(test)
    return testBattery

def weakSDS(initSize):
    testBattery = {}
    caseSizeX = initSize / 2
    caseSizeY = initSize
    for p in [0, 1, 2, 3, 4, 5, 6]:
    	# Defining case directory
        if p % 2 == 1:
            caseSizeY = caseSizeY * 2
        else:
            caseSizeX = caseSizeX * 2
        cn = case_name + str(caseSizeX) + 'x' + str(caseSizeY)

        for ratio in ratioThreadsCores:
            test = {}
            test['SDSgeom'] = SDSgeom
            test['nSDD'] = (1, 1)
            for SDSratio in SDSratioList:
                # Exploration strong SDS, nCoresPerSDD = nTotalCores / nsdd
                nCoresPerSDD = 2**p

                # élimine cas impossible
                if nCoresPerSDD > nTotalCores:
                    continue

                test['nCoresPerSDD'] = nCoresPerSDD

                # Pour un calcul à charge/ressource constante
                test['nThreads'] = nCoresPerSDD * ratio
                if test['nThreads'] <= 0:
                    continue

                # Définition du nombre de SDS
                test['nSDS'] = test['nThreads'] * SDSratio

                # the maximum number is the number of cells.
                if test['nSDS'] > caseSizeX * caseSizeY:
                    continue

                # add the number of tests.
                test['nRuns'] = nruns

                # add the machine on which is run the test
                test['machine'] = machine

                # Finally add the test in the battery
                if cn not in testBattery.keys():
                    testBattery[cn] = []
                testBattery[cn].append(test)
    return testBattery

def strongSDS(caseSizeXY):
    testBattery = {}
    for p in [0, 1, 2, 3, 4, 5, 6]:
    	# Defining case directory
        cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
        for ratio in ratioThreadsCores:
            test = {}
            test['SDSgeom'] = SDSgeom
            test['nSDD'] = (1, 1)
            for SDSratio in SDSratioList:
                # Exploration strong SDS, nCoresPerSDD = nTotalCores / nsdd
                nCoresPerSDD = 2**p

                # élimine cas impossible
                if nCoresPerSDD > nTotalCores:
                    continue

                test['nCoresPerSDD'] = nCoresPerSDD

                # Pour un calcul à charge/ressource constante
                test['nThreads'] = nCoresPerSDD * ratio
                if test['nThreads'] <= 0:
                    continue

                # Définition du nombre de SDS
                test['nSDS'] = test['nThreads'] * SDSratio

                # the maximum number is the number of cells.
                if test['nSDS'] > caseSizeXY[0] * caseSizeXY[1]:
                    continue

                # add the number of tests.
                test['nRuns'] = nruns

                # add the machine on which is run the test
                test['machine'] = machine

                # Finally add the test in the battery
                if cn not in testBattery.keys():
                    testBattery[cn] = []
                testBattery[cn].append(test)
    return testBattery

def strongSDD(caseSizeXY):
    minSdd = int(np.log2(nTotalCores // nCoresPerNode))
    maxSdd = int(np.log2(nTotalCores))

    testBattery = {}
    # Defining case directory
    cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
    for ratio in ratioThreadsCores:
        for p in range(minSdd, maxSdd + 1):
            # Different SDD splits, nSDD = 2**p
            for i in range(0, p/2 + 1):
            #for i in range(p/2, p/2 + 1):
                test = {}
                test['SDSgeom'] = SDSgeom
                test['nSDD'] = (2**i, 2**(p-i))
                nsdd = test['nSDD'][0]*test['nSDD'][1]
                for SDSratio in SDSratioList:
                    nCoresPerSDD = 1

                    # élimine cas impossible
                    if nCoresPerSDD > nTotalCores / nsdd:
                        continue

                    test['nCoresPerSDD'] = nCoresPerSDD
                    # Pour un calcul à charge/ressource constante
                    test['nThreads'] = nCoresPerSDD * ratio
                    if test['nThreads'] <= 0:
                        continue

                    # Définition du nombre de SDS
                    # test['nSDS'] = compute_sds_number(case_path, nsdd, SDSsize)
                    test['nSDS'] = test['nThreads'] * SDSratio

                    # the maximum number is the number of cells.
                    if test['nSDS'] > caseSizeXY[0] * caseSizeXY[1]:
                        continue

                    # add the number of tests.
                    test['nRuns'] = nruns

                    # add the machine on which is run the test
                    test['machine'] = machine

                    # Finally add the test in the battery
                    if cn not in testBattery.keys():
                        testBattery[cn] = []
                    testBattery[cn].append(test)
    return testBattery

def explore(caseSizeXY):
    minSdd = int(np.log2(nTotalCores // nCoresPerNode))
    maxSdd = int(np.log2(nTotalCores))

    testBattery = {}
    # Defining case directory
    cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
    for ratio in ratioThreadsCores:
        for p in range(minSdd, maxSdd + 1):
            # Different SDD splits, nSDD = 2**p
            for i in range(0, p/2 + 1):
            #for i in range(p/2, p/2 + 1):
                test = {}
                test['SDSgeom'] = SDSgeom
                test['nSDD'] = (2**i, 2**(p-i))
                nsdd = test['nSDD'][0]*test['nSDD'][1]
                for SDSratio in SDSratioList:
                    # Exploration strong SDS, nCoresPerSDD = nTotalCores / nsdd
                    nCoresPerSDD = nTotalCores / nsdd

                    # élimine cas impossible
                    if nCoresPerSDD > nTotalCores / nsdd:
                        continue

                    test['nCoresPerSDD'] = nCoresPerSDD
                    # Pour un calcul à charge/ressource constante
                    test['nThreads'] = nCoresPerSDD * ratio
                    if test['nThreads'] <= 0:
                        continue

                    # Définition du nombre de SDS
                    # test['nSDS'] = compute_sds_number(case_path, nsdd, SDSsize)
                    test['nSDS'] = test['nThreads'] * SDSratio

                    # the maximum number is the number of cells.
                    if test['nSDS'] > caseSizeXY[0] * caseSizeXY[1]:
                        continue

                    # add the number of tests.
                    test['nRuns'] = nruns

                    # add the machine on which is run the test
                    test['machine'] = machine

                    # Finally add the test in the battery
                    if cn not in testBattery.keys():
                        testBattery[cn] = []
                    testBattery[cn].append(test)
    return testBattery

#testBattery = weakSDD(64)
#testBattery = weakSDS(64)
#testBattery = strongSDD((256, 256))
#testBattery = strongSDS((256, 256))
#testBattery = explore((256, 256))

testBattery = {'n2dsod128x128' : [{'SDSgeom': 'line', 'nThreads': 1, 'nSDD': (2, 2), 'machine': 'unknown', 'nCoresPerSDD': 1, 'nSDS': 16, 'nRuns': 1}]}
testBattery = {'n2dsod128x128' : [{'SDSgeom': 'line', 'nThreads': 1, 'nSDD': (4, 4), 'machine': 'unknown', 'nCoresPerSDD': 1, 'nSDS': 16, 'nRuns': 1}]}
testBattery = {'n2dsod128x128' : [{'SDSgeom': 'line', 'nThreads': 1, 'nSDD': (1, 2), 'machine': 'unknown', 'nCoresPerSDD': 1, 'nSDS': 16, 'nRuns': 1}]}

totalTestNumber = 0
for k, tl in testBattery.items():
    print("%s test(s) on case %s" % (len(tl), k))
    totalTestNumber += len(tl)
    for t in tl:
        print("\t%s" % t)
print(totalTestNumber, "will be run")

runTestBattery(engineOptionDict, testBattery)
print("\nTest successfully passed\n")
