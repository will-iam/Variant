#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import sys
import itertools
from decimal import *
from seek_common import *

compileDict = {
'project_name': args.project_name,
'comp': 'mpi',
'mode': 'release',
'precision': 'double',
'std': 'c++14',
'bool_compile': not args.nocompile,
'vtune': args.vtune
}

# Define execution parameters
machine = args.machine
nTotalCores = args.max_proc_number
SDSgeom = 'line'
#caseSizeList = [128, 192, 256, 320, 384, 448, 512, 576, 640, 704, 768, 1024]
#caseSizeList = [(256, 512), (512, 256)]
caseSizeList = [(256, 256)]
ratioThreadsCores = [1]
SDSratioList = [4]
nruns = 5

#nSDD = [1, 4, 16, 64, 256] en puissance de 2 = [0, 2, 4, 6, 8]
#SDD_powersOfTwo = [0, 2, 4, 6]#
SDD_powersOfTwo = [0, 1, 2, 3, 4, 5, 6]
#SDD_powersOfTwo = [6]
#SDD_powersOfTwo = [2]
#SDD_powersOfTwo = [0]
#SDD_powersOfTwo = [2, 3, 4, 5, 6, 7, 8]



# Clean compile if requested.
if args.clean_compile:
    engine = compiler.Engine(compileDict['project_name'], False, compileDict['comp'], compileDict['mode'], compileDict['precision'], compileDict['std'], True)
    print("Cleaned target")
    sys.exit(0)

# Get case names from all directories in case/project_name/
case_name = args.c

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
            #for i in range(0, p/2 + 1):
            for i in range(p//2, p//2 + 1):
                test = {}
                test['SDSgeom'] = SDSgeom
                test['nSDD'] = (2**i, 2**(p-i))
                nsdd = test['nSDD'][0]*test['nSDD'][1]
                for SDSratio in SDSratioList:
                    # Exploration strong SDS, ncpmpi = nTotalCores / nsdd
                    ncpmpi = 1

                    # élimine cas impossible
                    if ncpmpi > nTotalCores / nsdd:
                        continue

                    test['ncpmpi'] = ncpmpi

                    # Pour un calcul à charge/ressource constante
                    test['nThreads'] = ncpmpi * ratio
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
                # Exploration strong SDS, ncpmpi = nTotalCores / nsdd
                ncpmpi = 2**p

                # élimine cas impossible
                if ncpmpi > nTotalCores:
                    continue

                test['ncpmpi'] = ncpmpi

                # Pour un calcul à charge/ressource constante
                test['nThreads'] = ncpmpi * ratio
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

def explore():
    testBattery = {}
    for caseSizeXY in caseSizeList:
    	# Defining case directory
        cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
        print cn
        for ratio in ratioThreadsCores:
            for p in SDD_powersOfTwo:
                # Different SDD splits, nSDD = 2**p
                for i in range(0, p/2 + 1):
                #for i in range(p/2, p/2 + 1):
                    test = {}
                    test['SDSgeom'] = SDSgeom
                    test['nSDD'] = (2**i, 2**(p-i))
                    nsdd = test['nSDD'][0]*test['nSDD'][1]
                    for SDSratio in SDSratioList:
                        # Exploration strong SDS, ncpmpi = nTotalCores / nsdd
                        ncpmpi = nTotalCores / nsdd

                        # élimine cas impossible
                        if ncpmpi > nTotalCores / nsdd:
                            continue

                        test['ncpmpi'] = ncpmpi
                        # Pour un calcul à charge/ressource constante
                        test['nThreads'] = ncpmpi * ratio
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

# Weak Comparaison
#testBattery = weakSDD(128)
#testBattery = weakSDS(64)
testBattery = explore()

totalTestNumber = 0
for k, tl in testBattery.items():
    print("%s test(s) on case %s" % (len(tl), k))
    totalTestNumber += len(tl)
    for t in tl:
        print("\t%s" % t)
print(totalTestNumber, "will be run")

runTestBattery(compileDict, testBattery)
print("\nTest successfully passed\n")
