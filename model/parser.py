#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import sys
import numpy as np
import argparse


'''
['SDSgeom', 'SoA_or_AoS', 'computeTime', 'finalizeTime', 'initTime', 'loopTime', 'nBoundaryCells', 'nIterations', 'nNeighbourSDD', 'nOverlapCells', 'nPhysicalCells', 'nSDD', 'nSDD_X', 'nSDD_Y', 'nSDS', 'nThreads', 'synchronizeTime', 'thread_iteration_type', 'totalExecTime', 'machineName', 'nCoresPerSDD']
'''

def fn(x):
    return (x-2)*2 + 2

# Retrouve la clef du cas test
def makeCaseKey(caseSizeX, caseSizeY):
    if caseSizeX == 64 and caseSizeY == 64:
        return '64x64x274'
    if caseSizeX == 64 and caseSizeY == 128:
        return '64x64x280'
    if caseSizeX == 128 and caseSizeY == 128:
        return '128x128x556'
    if caseSizeX == 128 and caseSizeY == 256:
        return '128x256x566'
    if caseSizeX == 256 and caseSizeY == 256:
        return '256x256x1121'
    elif caseSizeX == 256 and caseSizeY == 512:
        return '256x512x1138'
    elif caseSizeX == 512 and caseSizeY == 512:
        return '512x512x2252'
    raise ValueError("Could not find %sx%s" % (caseSizeX, caseSizeY))

def extractKey(key):
    firstSplit = key.split('x')
    Nx = int(firstSplit[0])
    Ny = int(firstSplit[1])
    secondSplit = firstSplit[2].split(':')

    Ni = int(secondSplit[0])
    R = int(secondSplit[1])
    Nt = int(secondSplit[2])
    Ns = int(secondSplit[3])

    return {"Nx":Nx, "Ny":Ny, "Ni":Ni, "R":R, "Nt":Nt, "Ns":Ns}

def makeKey(attrnames, data_line):
    '''
    Nx : nombre de mailles en abscisses
    Ny : nombre de mailles en ordonnées
    Ni : nombre d'itérations
    R = nx ny nc : nombre de ressources (en coeurs)
    Nt : nombre de threads par cœur
    Ns : nombre de SDS par thread
    '''

    nCoresPerSDD = int(data_line[attrnames.index('nCoresPerSDD')])
    nThreads = int(data_line[attrnames.index('nThreads')])
    # Cas particulier: si le nombre de threads alloué est inférieur, il remplace le nombre de coeurs par SDD.
    if nThreads < nCoresPerSDD:
        print("ERROR: nThreads < nCoresPerSDD = %s < %s" % (nThreads, nCoresPerSDD))
        raise ValueError

    nIterationsList = data_line[attrnames.index('nIterations')]
    if len(nIterationsList) == 0:
        print("Erreur dans le fichier de données")
        raise ValueError

    for n in nIterationsList:
        if n != nIterationsList[0]:
            print("Erreur dans le fichier de données")
            raise ValueError

    nPhysicalCells = int(data_line[attrnames.index('nPhysicalCells')])
    nSDD = int(data_line[attrnames.index('nSDD')])
    nx = int(data_line[attrnames.index('nSDD_X')])
    ny = int(data_line[attrnames.index('nSDD_Y')])
    No = data_line[attrnames.index('nOverlapCells')][0] * nSDD

    Nx = int(data_line[attrnames.index('nSizeX')])
    Ny = int(data_line[attrnames.index('nSizeY')])

    if Nx * Ny != nPhysicalCells * nSDD:
        print('nPhysicalCells * nSDD', nPhysicalCells * nSDD)
        print('nPhysicalCells * nSDD / from_case_name_ny', nPhysicalCells * nSDD / from_case_name_ny)
        print('from_case_name_ny', from_case_name_ny)
        print('No', No)
        print('fn(ny)', fn(ny))
        print('fn(nx)', fn(nx))
        print(nx, ny, Nx, Ny, nPhysicalCells * nSDD, Nx * Ny)
        print("Problem in case size conversion")
        raise ValueError

    Ni = int(nIterationsList[0])
    R = nCoresPerSDD * nSDD
    Nt = nThreads / nCoresPerSDD
    Ns = int(data_line[attrnames.index('nSDS')]) / (Nt * nCoresPerSDD)

    # Make unique key
    key = "%sx%sx%s:%s:%s:%s" % (Nx, Ny, Ni, R, Nt, Ns)
    #print "[DATA] - %s: %s run(s) ressources = %s" % (key, len(nIterationsList), R), " case: %sx%s" % (Nx, Ny)

    return key,  nPhysicalCells * nSDD * Ni


def parseData(filepath, data, filterKey):
    attrnames = []
    with open(filepath, 'r') as f:
        runAdded = 0
        attrnames = f.readline().replace('\n', '').split(';')
        previous_line = ''
        for line in f.readlines():
            line = previous_line + line
            if line == [] or line == '\0':
                print("empty line")
                break
            data_line = []
            for el in line.split(';'):
                if el[0] in ['(', '[']:
                    el = el[1:-1]
                    data_line.append([float(e) for e in el.replace(",", "").split()])
                else:
                    try:
                        data_line.append(int(el))
                    except ValueError:
                        data_line.append(el)
            try:
                key, normalizer = makeKey(attrnames, data_line)
            except IndexError:
                #print "failed to parse: ", line
                #print "result data_line: ", data_line
                previous_line = line
                continue
            except ValueError:
                print("Can't parse file.")
                sys.exit(1)
            # reset multiline parsing
            previous_line = ''

            # Passe tous les résultats qui ne sont pas en accord avec la clef.
            if not key.startswith(filterKey):
                #print "filtered:", key, filterKey
                continue

            if key not in data.keys():
                data[key] = []

            # Paramètres d'entrées, point de fonctionnement.
            # nSDD_X, nSDD_Y, nCoresPerSDD
            nSDD_X = int(data_line[attrnames.index('nSDD_X')])
            nSDD_Y = int(data_line[attrnames.index('nSDD_Y')])
            nCoresPerSDD = int(data_line[attrnames.index('nCoresPerSDD')])
            point = tuple([nSDD_X, nSDD_Y, nCoresPerSDD])

            minComputeSumList = data_line[attrnames.index('minComputeSum')]
            maxComputeSumList = data_line[attrnames.index('maxComputeSum')]
            maxIterationSumList = data_line[attrnames.index('maxIterationSum')]
            loopTimeList = data_line[attrnames.index('loopTime')]
            nNeighbourSDD = data_line[attrnames.index('nNeighbourSDD')]
            nPhysicalCells = int(data_line[attrnames.index('nPhysicalCells')])
            machine = data_line[attrnames.index('machineName')]

            runNumber = len(maxIterationSumList)

            if runNumber != len(loopTimeList) or runNumber != len(minComputeSumList) or runNumber != len(maxComputeSumList):
                print("Erreur dans le fichier de données")
                sys.exit(1)

            for i in range(0, runNumber):
                runAdded += 1
                loopTime = float(loopTimeList[i])/normalizer
                minComputeSum = float(minComputeSumList[i])/normalizer
                maxComputeSum = float(maxComputeSumList[i])/normalizer
                maxIterationSum = float(maxIterationSumList[i])/normalizer
                data[key].append({"point": point, "loopTime": loopTime, "minComputeSum": minComputeSum, "maxComputeSum": maxComputeSum, "maxIterationSum": maxIterationSum,
                         "meanNeighbour": nNeighbourSDD[0], "maxNeighbour": nNeighbourSDD[2], "nPhysicalCells": nPhysicalCells, "machine": machine})
                #print data_line
                #print i, nSDD_X, nSDD_Y, nCoresPerSDD, data[key][-1]

        print "\t - leaving file", filepath, "run added:", runAdded
        f.close()

def readData(projectName, caseName, data, filterKey):
    dirpath = os.path.join('data', projectName, str(caseName))
    for filename in os.listdir(dirpath):
        if not filename.endswith(".csv"):
            continue
        print "\t - parsing data from %s/%s:" % (caseName, filename)
        filepath = os.path.join(dirpath, filename)
        parseData(filepath, data, filterKey)

def getData(filterKey = ''):
    data = {}
    for projectName in os.listdir('data'):
        for caseName in os.listdir(os.path.join('data',projectName)):
            print "Start reading file list from %s/%s directory:" % (projectName, caseName)
            readData(projectName, caseName, data, filterKey)
    return data
