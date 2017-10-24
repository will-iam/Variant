#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import sys
import numpy as np
import argparse

parser = argparse.ArgumentParser(description="Performance measures", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("--case", type = str, help = "Case to test", required=True)
parser.add_argument("--machine", type = str, help = "Hostname of the test", default='unknown')
args = parser.parse_args()


def fn(x):
    return (x-2)*2 + 2
'''
# Retrouve la clef du cas test
def makeCaseKey(caseSizeX, caseSizeY):
    if caseSizeX == 64 and caseSizeY == 64:
        return '%s/%s/64x64x274' % (args.project_name, args.case)
    if caseSizeX == 64 and caseSizeY == 128:
        return '64x64x280' % (args.project_name, args.case)
    if caseSizeX == 128 and caseSizeY == 128:
        return '128x128x556' % (args.project_name, args.case)
    if caseSizeX == 128 and caseSizeY == 256:
        return '128x256x566' % (args.project_name, args.case)
    if caseSizeX == 256 and caseSizeY == 256:
        return '256x256x1121' % (args.project_name, args.case)
    elif caseSizeX == 256 and caseSizeY == 512:
        return '256x512x1138'
    elif caseSizeX == 512 and caseSizeY == 512:
        return '512x512x2252'
    raise ValueError("Could not find %sx%s" % (caseSizeX, caseSizeY))
'''

def extractKey(key):
    zeroSplit = key.split('/')
    projectName = zeroSplit[0]
    caseName = zeroSplit[1]
    data = zeroSplit[2]

    firstSplit = data.split('x')
    Nx = int(firstSplit[0])
    Ny = int(firstSplit[1])
    secondSplit = firstSplit[2].split(':')

    Ni = int(secondSplit[0])
    R = int(secondSplit[1])
    Nt = int(secondSplit[2])
    Ns = int(secondSplit[3])

    return {"projectName": projectName, "caseName": caseName, "Nx":Nx, "Ny":Ny, "Ni":Ni, "R":R, "Nt":Nt, "Ns":Ns}

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
    key = "%s/%s/%sx%sx%s:%s:%s:%s" % (args.project_name, args.case, Nx, Ny, Ni, R, Nt, Ns)
    #print "[DATA] - %s: %s run(s) ressources = %s" % (key, len(nIterationsList), R), " case: %sx%s" % (Nx, Ny)

    return key,  nPhysicalCells * nSDD * Ni


def parseData(filepath, data, filterDict):
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

            # Filtered by machine
            machine = data_line[attrnames.index('machineName')]
            if args.machine and machine != args.machine:
                print("machine filtered: %s != %s" %(args.project_name, machine))
                continue

            # Paramètres d'entrées, point de fonctionnement.
            # nSDD_X, nSDD_Y, nCoresPerSDD
            nSDD_X = int(data_line[attrnames.index('nSDD_X')])
            nSDD_Y = int(data_line[attrnames.index('nSDD_Y')])
            nCoresPerSDD = int(data_line[attrnames.index('nCoresPerSDD')])
            point = tuple([nSDD_X, nSDD_Y, nCoresPerSDD])

            if 'R' in filterDict.keys() and filterDict['R'] != nSDD_X * nSDD_Y * nCoresPerSDD:
                continue

            nSizeX = int(data_line[attrnames.index('nSizeX')])
            if 'nSizeX' in filterDict.keys() and filterDict['nSizeX'] != nSizeX:
                continue

            nSizeY = int(data_line[attrnames.index('nSizeY')])
            if 'nSizeY' in filterDict.keys() and filterDict['nSizeY'] != nSizeY:
                continue

            minComputeSumList = data_line[attrnames.index('minComputeSum')]
            maxComputeSumList = data_line[attrnames.index('maxComputeSum')]
            maxIterationSumList = data_line[attrnames.index('maxIterationSum')]
            loopTimeList = data_line[attrnames.index('loopTime')]
            nNeighbourSDD = data_line[attrnames.index('nNeighbourSDD')]
            nPhysicalCells = int(data_line[attrnames.index('nPhysicalCells')])

            runNumber = len(maxIterationSumList)

            if runNumber != len(loopTimeList) or runNumber != len(minComputeSumList) or runNumber != len(maxComputeSumList):
                print("Erreur dans le fichier de données")
                sys.exit(1)

            if key not in data.keys():
                data[key] = []

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

        print("\t - parsed %s run added: %s" % (filepath, runAdded))
        f.close()

def readData(projectName, caseName, data, filterDict):
    dirpath = os.path.join('data', projectName, str(caseName))
    for filename in os.listdir(dirpath):
        if not filename.endswith(".csv"):
            continue
        #print "\t - parsing data from %s/%s:" % (caseName, filename)
        filepath = os.path.join(dirpath, filename)
        parseData(filepath, data, filterDict)

def getData(filterDict = {}):
    data = {}
    for projectDir in os.listdir('data'):
        if projectDir != args.project_name:
            continue

        for caseDir in os.listdir(os.path.join('data', projectDir)):
            if not caseDir.startswith(args.case):
                continue

            print "Start reading file list from %s/%s directory:" % (projectDir, caseDir)
            readData(projectDir, caseDir, data, filterDict)
    return data
