#!/usr/bin/python3
# -*- coding:utf-8 -*-

import __future__
import parser
import sys
import matplotlib.pyplot as plt
#plt.style.use('ggplot')
import numpy as np
import operator
from collections import *

caseSize = (8192, 8192)
if parser.args.res:
    maxAvailableNode = parser.args.res
else:
    maxAvailableNode = 8

sizeDataDict = []
for p in range(0, int(np.log2(maxAvailableNode)) + 1):
    filterDict = {'nSizeX' : caseSize[0], 'nSizeY' : caseSize[1], 'R' : 64 * 2**p}
    print filterDict
    data = parser.getData(filterDict)
    if len(data):
        sizeDataDict.append(data)


if len(sizeDataDict) == 0:
    print("No data found.")
    sys.exit(1)


loopTimeDict = dict()
for data in sizeDataDict:
    for key, value in data.items():
        keyDict = parser.extractKey(key)

        Nt = keyDict['Nt']
        R = keyDict['R']


        if keyDict['Ny'] != caseSize[0] or keyDict['Nx'] != caseSize[1]:
            print("Error in collected data")
            sys.exit(1)

        for run in value:
            nSDD = run['point'][0] * run['point'][1]

            # On several nodes, select only pure SDD, which is the best result.
            if R > 64 and nSDD < R:
                continue

            # Don't remove HyperThreading.
            # We assume that hyperthreading with SDD leads to same results as with SDS.
            #if R > 64 and nSDD == R and Nt > 1.0:
            #    continue

            # On a single node, select only pure SDS
            if R == 64 and nSDD > 1:
                continue

            loopT = run['loopTime'] * caseSize[0] * caseSize[1] * keyDict['Ni'] / 1000.
            if R not in loopTimeDict.keys():
                loopTimeDict[R] = list()
            loopTimeDict[R].append(loopT)

# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
#ax = fig.add_subplot(211)
#ax.set_xscale('log', basex=2)
#ax.set_yscale('log')

maxSimulationNumber = 42
xArray = range(1, maxSimulationNumber + 1)

'''
#Perfect Scale

loopTimeDict[128] = [k / 2. for k in loopTimeDict[64]]
loopTimeDict[256] = [k / 4. for k in loopTimeDict[64]]
loopTimeDict[512] = [k / 8. for k in loopTimeDict[64]]
'''

for r in sorted(loopTimeDict):
    nodeNeeded = r // 64
    minT = np.min(loopTimeDict[r])
    print("Min Time %s node(s) = %s" % (nodeNeeded, minT))
    totalTimeArray = np.zeros(maxSimulationNumber)
    for i in xArray:
        totalTimeArray[i-1] = minT * (1 + (i * nodeNeeded - 1) // maxAvailableNode)
    ax.plot(xArray, totalTimeArray, '-', label="Batch Size %s" % (r // 64))
    parser.outputCurve("ergodicity_scaling-%s.dat" % (r//64), xArray, totalTimeArray)

'''
minSize = int(np.sqrt(np.min(syncTimeDict.keys())))
maxSize = int(np.sqrt(np.max(syncTimeDict.keys())))
nodeNumber = (caseSize[0] * caseSize[1] / (maxSize * maxSize))
'''

plt.title('%sx%s batch time with %s node(s) available at the same time.' % (caseSize[0], caseSize[1], maxAvailableNode))

plt.xlabel('Total number of simulation to run')
plt.ylabel('Loop Time')
plt.legend()

'''
bx = fig.add_subplot(212)
bx.set_xscale('log', basex=2)
bx.plot(sorted(sdsWeakDict), [np.min(v) for k, v in sorted(sdsWeakDict.items(), key=operator.itemgetter(0))], 'g+-', label="SDS scaling")
bx.plot(sorted(sddWeakDict), [np.min(v) for k, v in sorted(sddWeakDict.items())], 'b+-', label="SDD scaling")
#bx.plot(sorted(hybridWeakDict), [np.min(v) for k, v in sorted(hybridWeakDict.items())], 'y+-', label="Hybrid scaling")
bx.plot(sorted(sddWeakDict), [firstValueSDD for k in sorted(sddWeakDict.keys())], 'b--', label="SDD ideal")
bx.plot(sorted(sdsWeakDict), [firstValueSDS for k in sorted(sdsWeakDict.keys())], 'g--', label="SDS ideal")

for k in sdsWeakDict:
    bx.plot(np.full(len(sdsWeakDict[k]), k), sdsWeakDict[k], 'g+')
for k in sddWeakDict:
    bx.plot(np.full(len(sddWeakDict[k]), k), sddWeakDict[k], 'b+')


plt.title('Weak Scaling from %sx%s to %sx%s' % (initSize, initSize, initSize * 2**((maxPower-1) / 2), initSize * 2**((maxPower-1) / 2)) )
plt.xlabel('Core(s)')
plt.ylabel('Loop Time / iteration')
plt.legend()
'''

plt.show()
