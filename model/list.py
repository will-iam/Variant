#!/usr/bin/python
# -*- coding:utf-8 -*-

import operator
import numpy as np
import matplotlib.pyplot as plt
import parser

caseSize = 512
caseKey = parser.makeCaseKey(caseSize) + ':256'
data = parser.getData(caseKey)
if not len(data):
    print("Aucune données sur le cas %s" % caseKey)
    sys.exit(1)


print "physicalCells, nIterations, nSDD, nThreads, mean time"
globalMinTime = 1e300
globalMinPoint = (0,0,0)
globalMinKey = '-----'
for k, d in data.items():
    print k
    minPoint = d[0]['point']
    minTime = d[0]['loopTime']
    for run in d:
        if run['loopTime'] < minTime:
            minTime = run['loopTime']
            minPoint = run['point']
        print "\t", run['point'], ': %s' % run['loopTime']
    minTuple = sorted(d, key=operator.itemgetter('loopTime'))[0]
    print "min time: ", minTuple['loopTime'], "on point: ", minTuple['point']
    if minTuple['loopTime'] < globalMinTime:
        globalMinTime = minTime
        globalMinPoint = minPoint
        globalMinKey = k
print "Best time is: %s on point %s for key: %s" % (globalMinTime, globalMinPoint, globalMinKey)

print "\nratio with min"
for k, d in data.items():
    print k
    for run in d:
        print "\t", run['point'], ': min time x %s' % (run['loopTime'] / float(globalMinTime))
    


