#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
"""

import __future__
import operator
import numpy as np
import matplotlib.pyplot as plt
import parser
import sys

caseSize = (8192, 8192)
resource = 256

filterDict = {'nSizeX' : caseSize[0], 'nSizeY' : caseSize[1], 'R' : resource}
data = parser.getData(filterDict)

if not len(data):
    print("Aucune données sur le cas %sx%s" % (caseSize[0], caseSize[1]))
    sys.exit(1)


print "physicalCells, nIterations, nSDD, nThreads, mean time"
globalList = list()
for k, d in data.items():
    print k
    keyDict = parser.extractKey(k)
    unnormalizer = caseSize[0] * caseSize[1] * keyDict['Ni']
    minPoint = d[0]['point']
    minTime = d[0]['loopTime']
    for run in d:
        print "\t", run['point'], ': %s (%s)' % (run['loopTime'], run['loopTime'] * unnormalizer )
        globalList.append((run['loopTime'], run['point'], k, run['loopTime'] * unnormalizer, run['nCommonSDS']))
    minTuple = sorted(d, key=operator.itemgetter('loopTime'))[0]
    print "min time: ", minTuple['loopTime'], "on point: ", minTuple['point']


globalList = sorted(globalList, key=operator.itemgetter(0))
if not globalList:
    print("No results.")
    sys.exit(1)

globalListSDS = [e for e in globalList if e[1][2] == np.min([64, resource])]
if globalListSDS:
    print "\nBest results for SDS: %s" % len(globalListSDS)
    print "\t%s on point %s, commonSize %s, for key: %s" % (globalListSDS[0][0], globalListSDS[0][1], globalListSDS[0][4], globalListSDS[0][2])
    #for i in range(1, np.min([5, len(globalListSDS)])):
    for i in range(1, len(globalListSDS)):
        print "\t%s on point %s, commonSize %s, for key: %s and ratio : minimal time x %s" % (globalListSDS[i][0], globalListSDS[i][1], globalListSDS[i][4], globalListSDS[i][2], globalListSDS[i][0] / globalListSDS[0][0])

#    if len(globalListSDS) >= 10:
#        print "\t..."
#        for i in range(np.max([0, len(globalListSDS) - 5]), len(globalListSDS)):
#            print "\t%s on point %s, commonSize %s, for key: %s and ratio : minimal time x %s" % (globalListSDS[i][0], globalListSDS[i][1], globalListSDS[i][4], globalListSDS[i][2], globalListSDS[i][0] / globalListSDS[0][0])

globalListSDD = [e for e in globalList if e[1][2] == 1]
if globalListSDD:
    print "\nBest results for SDD: %s" % len(globalListSDD)
    print "\t%s on point %s, commonSize %s, for key: %s" % (globalListSDD[0][0], globalListSDD[0][1], globalListSDD[0][4], globalListSDD[0][2])
    for i in range(1, np.min([5, len(globalListSDD)])):
        print "\t%s on point %s, commonSize %s, for key: %s and ratio : minimal time x %s" % (globalListSDD[i][0], globalListSDD[i][1], globalListSDD[i][4], globalListSDD[i][2], globalListSDD[i][0] / globalListSDD[0][0])

    if len(globalListSDD) >= 10:
        print "\t..."
        for i in range(np.max([0, len(globalListSDD) - 5]), len(globalListSDD)):
            print "\t%s on point %s, commonSize %s, for key: %s and ratio : minimal time x %s" % (globalListSDD[i][0], globalListSDD[i][1], globalListSDD[i][4], globalListSDD[i][2], globalListSDD[i][0] / globalListSDD[0][0])

print "\nAll results sorted: %s" % len(globalList)
print "\t%s on point %s, commonSize %s, for key: %s" % (globalList[0][0], globalList[0][1], globalList[0][4], globalList[0][2])
for i in range(1, np.min([10, len(globalList)])):
    print "\t%s on point %s, commonSize %s, for key: %s and ratio : minimal time x %s" % (globalList[i][0], globalList[i][1], globalList[i][4], globalList[i][2], globalList[i][0] / globalList[0][0])

if len(globalList) >= 25:
    print "\t..."
    for i in range(np.max([0, len(globalList) - 15]), len(globalList)):
        print "\t%s on point %s, commonSize %s, for key: %s and ratio : minimal time x %s" % (globalList[i][0], globalList[i][1], globalList[i][4], globalList[i][2], globalList[i][0] / globalList[0][0])
