##!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import sys
import itertools
import copy
from decimal import *
from seek_common import *
import script.compiler as compiler

# Get case names from all directories in case/project_name/
case_name = args.c
engineOptionDict = {
'project_name': args.project_name,
'compiler': 'mpi',
'mode': 'release' if not args.debug else 'debug',
'precision': 'double',
'std': 'c++14',
'must_compile': not args.nocompile,
'vtune': args.vtune,
'gdb' : args.debug,
'valgrind' : False,
'node_number' : int(np.ceil(float(args.max_core_number) /args.core_per_node))
}

# Define execution parameters
machine = args.machine
nTotalCores = args.max_core_number
SDSgeom = 'line'
#ratioThreadsCores = [1., 3.97]
ratioThreadsCores = [1]
SDSratioList = [4]
SDScommonDivider = 5./32.
nruns = 1
nCoresPerNode = args.core_per_node

# Clean compile if requested.
if args.clean_compile:
    compiler.Engine(engineOptionDict, False, True)
    print("Cleaned target")
    sys.exit(0)

def weakSDD(initSize, square = False):
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
                test['SDSgeom'] = SDSgeom
                test['nSDD'] = (2**i, 2**(p-i))
                nsdd = test['nSDD'][0] * test['nSDD'][1]
                for SDSratio in SDSratioList:
                    # Exploration strong SDS, nCoresPerSDD = nTotalCores / nsdd
                    test['nCoresPerSDD'] = 1

                    # Pour un calcul à charge/ressource constante
                    test['nThreads'] = np.max([1, int(test['nCoresPerSDD'] * ratio)])

                    # Définition du nombre de SDS
                    test['nSDS'] = test['nThreads']

                    # add the number of tests.
                    test['nRuns'] = nruns

                    # add the machine on which is run the test
                    test['machine'] = machine

                    # add the common SDS size
                    test['nCommonSDS'] = 0

                    # Finally add the test in the battery
                    if cn not in testBattery.keys():
                        testBattery[cn] = []
                    testBattery[cn].append(copy.copy(test))
    return testBattery

def weakSDS(initSize):
    testBattery = {}
    caseSizeX = initSize // 2
    caseSizeY = initSize
    for p in range(0, 7):
    	# Defining case directory
        if p % 2 == 1:
            caseSizeY = caseSizeY * 2
        else:
            caseSizeX = caseSizeX * 2
        cn = case_name + str(caseSizeX) + 'x' + str(caseSizeY)

        if caseSizeX != 512 or caseSizeY != 1024:
            continue

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
                test['nThreads'] = int(nCoresPerSDD * ratio)
                if test['nThreads'] <= 0:
                    continue

                # Définition du nombre de SDS
                test['nSDS'] = int(test['nThreads'] * SDSratio)

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

                # add the common SDS size
                test['nCommonSDS'] = int(test['nSDS'] * SDScommonDivider)
                testBattery[cn].append(copy.copy(test))

                test['nCommonSDS'] = 0
                testBattery[cn].append(copy.copy(test))

    return testBattery

def strongSDS(caseSizeXY, startPower = 0, endPower = 7):
    testBattery = {}
    for p in range(startPower, endPower):
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
                test['nThreads'] = int(nCoresPerSDD * ratio)
                if test['nThreads'] <= 0:
                    continue

                # Définition du nombre de SDS
                test['nSDS'] = int(test['nThreads'] * SDSratio)

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

                # add the common SDS size
                test['nCommonSDS'] = int(test['nSDS'] * SDScommonDivider)
                testBattery[cn].append(copy.copy(test))

    return testBattery

def strongSDD(caseSizeXY, square = False):
    minSdd = int(np.log2(nTotalCores // nCoresPerNode))
    maxSdd = int(np.log2(nTotalCores))

    testBattery = {}
    # Defining case directory
    cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
    for ratio in ratioThreadsCores:
        for p in range(minSdd, maxSdd + 1):
            initP = 0
            if square == True:
                initP = p // 2
            for i in range(initP, p // 2 + 1):
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
                    test['nThreads'] = int(nCoresPerSDD * ratio)
                    if test['nThreads'] <= 0:
                        continue

                    # Définition du nombre de SDS
                    test['nSDS'] = test['nThreads']

                    # add the number of tests.
                    test['nRuns'] = nruns

                    # add the machine on which is run the test
                    test['machine'] = machine

                    # add the common SDS size
                    test['nCommonSDS'] = 0

                    # Finally add the test in the battery
                    if cn not in testBattery.keys():
                        testBattery[cn] = []
                    testBattery[cn].append(copy.copy(test))
    return testBattery

def ratio(caseSizeXY):
    testBattery = {}
    # Defining case directory
    cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
    for ratio in ratioThreadsCores:
        # Different SDD splits, nSDD = 2**p
        test = {}
        test['SDSgeom'] = SDSgeom
        test['nSDD'] = (1, 1)

        # add the number of tests.
        test['nRuns'] = nruns

        # add the machine on which is run the test
        test['machine'] = machine

        nsdd = test['nSDD'][0]*test['nSDD'][1]
        for SDSratio in SDSratioList:
            # Exploration strong SDS, nCoresPerSDD = nTotalCores / nsdd
            nCoresPerSDD = nTotalCores / nsdd

            # élimine cas impossible
            if nCoresPerSDD > nTotalCores / nsdd:
                continue

            test['nCoresPerSDD'] = nCoresPerSDD
            # Pour un calcul à charge/ressource constante
            test['nThreads'] = int(nCoresPerSDD * ratio)
            if test['nThreads'] <= 0:
                continue

            # Définition du nombre de SDS
            # test['nSDS'] = compute_sds_number(case_path, nsdd, SDSsize)
            test['nSDS'] = int(test['nThreads'] * SDSratio)

            # the maximum number is the number of cells.
            if test['nSDS'] > caseSizeXY[0] * caseSizeXY[1]:
                continue

            if cn not in testBattery.keys():
                testBattery[cn] = []

            # add the common SDS size
            test['nCommonSDS'] = int(test['nSDS'] * SDScommonDivider)
            testBattery[cn].append(copy.copy(test))

    return testBattery

def commonSDS(caseSizeXY):
    testBattery = {}
    # Defining case directory
    cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
    for ratio in ratioThreadsCores:
        # Different SDD splits, nSDD = 2**p
        test = {}
        test['SDSgeom'] = SDSgeom
        test['nSDD'] = (1, 1)

        # add the number of tests.
        test['nRuns'] = nruns

        # add the machine on which is run the test
        test['machine'] = machine

        nsdd = test['nSDD'][0]*test['nSDD'][1]
        for SDSratio in SDSratioList:
            # Exploration strong SDS, nCoresPerSDD = nTotalCores / nsdd
            nCoresPerSDD = nTotalCores / nsdd

            # élimine cas impossible
            if nCoresPerSDD > nTotalCores / nsdd:
                continue

            test['nCoresPerSDD'] = nCoresPerSDD
            # Pour un calcul à charge/ressource constante
            test['nThreads'] = int(nCoresPerSDD * ratio)
            if test['nThreads'] <= 0:
                continue

            # Définition du nombre de SDS
            # test['nSDS'] = compute_sds_number(case_path, nsdd, SDSsize)
            test['nSDS'] = int(test['nThreads'] * SDSratio)

            # the maximum number is the number of cells.
            if test['nSDS'] > caseSizeXY[0] * caseSizeXY[1]:
                continue

            if cn not in testBattery.keys():
                testBattery[cn] = []

            if test['nThreads'] == 1:
                print("Are you kidding ")
                sys.exit(1)

            # add the common SDS size
            #for commonSize in range(0, int(test['nSDS'] / 2), int(test['nSDS'] * SDScommonDivider / 4)):
            for commonSize in [0, SDScommonDivider - 0.02, SDScommonDivider, SDScommonDivider + 0.02]:
                test['nCommonSDS'] = commonSize
                # Finally add the test in the battery
                testBattery[cn].append(copy.copy(test))

    return testBattery

def explore(caseSizeXY, square = False):
    minSdd = int(np.log2(nTotalCores // nCoresPerNode))
    maxSdd = int(np.log2(nTotalCores)) + 1

    testBattery = {}
    # Defining case directory
    cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
    for ratio in ratioThreadsCores:
        for p in range(minSdd, maxSdd + 1):
            # Different SDD splits, nSDD = 2**p
            initP = 0
            if square == True:
                initP = p // 2
            for i in range(initP, p // 2 + 1):
                test = {}
                test['SDSgeom'] = SDSgeom
                test['nSDD'] = (2**i, 2**(p-i))

                # add the number of tests.
                test['nRuns'] = nruns

                # add the machine on which is run the test
                test['machine'] = machine

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
                    test['nCommonSDS'] = int(test['nSDS'] * SDScommonDivider)

                    # Finally add the test in the battery
                    testBattery[cn].append(copy.copy(test))

    return testBattery

def exploreCaseSize(initSize):
    testBattery = {}
    caseSizeX = initSize // 2
    caseSizeY = initSize
    for p in range(0, 3):
    	# Defining case directory
        if p % 2 == 1:
            caseSizeY = caseSizeY * 2
        else:
            caseSizeX = caseSizeX * 2

        for k, tl in explore((caseSizeX, caseSizeY), True).items():
            if k not in battery:
                testBattery[k] = tl
            else:
                testBattery[k] = battery[k] + tl

    return testBattery

battery = dict()

'''
for k, tl in weakSDS(512).items():
    if k not in battery:
        battery[k] = tl
    else:
        battery[k] = battery[k] + tl

for k, tl in weakSDD(256, True).items():
    if k not in battery:
        battery[k] = tl
    else:
        battery[k] = battery[k] + tl

for k, tl in strongSDS((2048, 2048), 0, 4).items():
    if k not in battery:
        battery[k] = tl
    else:
        battery[k] = battery[k] + tl


for k, tl in strongSDD((2048, 2048), True).items():
    if k not in battery:
        battery[k] = tl
    else:
        battery[k] = battery[k] + tl


for k, tl in ratio((8192, 8192)).items():
    if k not in battery:
        battery[k] = tl
    else:
        battery[k] = battery[k] + tl


for k, tl in commonSDS((4096, 4096)).items():
    if k not in battery:
        battery[k] = tl
    else:
        battery[k] = battery[k] + tl
'''
for k, tl in explore((128, 128), True).items():
    if k not in battery:
        battery[k] = tl
    else:
        battery[k] = battery[k] + tl
'''
for k, tl in exploreCaseSize(2048).items():
    if k not in battery:
        battery[k] = tl
    else:
        battery[k] = battery[k] + tl
'''

totalTestNumber = 0
for k, tl in battery.items():
    print("%s test type(s) on case %s" % (len(tl), k))
    for t in tl:
        totalTestNumber += t['nRuns']
        print("\t%s" % t)

print("%s run(s) to perform." % totalTestNumber)
if args.test == False:
    runTestBattery(engineOptionDict, battery)
    print("\nTest successfully passed\n")

#srun: error: Unable to create job step: More processors requested than permitted

#ccc_mprun -n 128 -x -c 1 hydro4x1-release-mpi.exec -i cases/hydro4x1/n2dsod8192x8192/init/8x16 -o /ccc/scratch/cont002/m7/weens4x/BATCH/batch.840510.thom113/Variant/tmp/hydro4x1/n2dsod8192x8192/final --dry
#ccc_mprun -p knl -N 2 -n 256 -E -O
