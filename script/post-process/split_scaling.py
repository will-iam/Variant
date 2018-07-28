#!/usr/bin/python
# -*- coding:utf-8 -*-

import parser
import sys
import matplotlib.pyplot as plt
#plt.style.use('ggplot')
import numpy as np
import operator
from collections import *

caseSize = (8192, 8192)
if parser.args.res:
    resource = parser.args.res
else:
    resource = 256

if parser.args.x and parser.args.y:
    caseSize = (parser.args.x, parser.args.y)

filterDict = {'nSizeX' : caseSize[0], 'nSizeY' : caseSize[1], 'R' : resource}
data = parser.getData(filterDict)

if not len(data):
    print("Aucune données sur le cas %sx%s" % (caseSize[0], caseSize[1]))
    sys.exit(1)

syncTimeDict = dict()
loopTimeDict = dict()
loopTimeWoHTDict = dict()
minComputeSumTimeDict = dict()
maxComputeSumTimeDict = dict()

minSubdomain = caseSize
maxSubdomain = (0, 0)

for key, value in data.items():
    keyDict = parser.extractKey(key)

    Nt = keyDict['Nt']

    if keyDict['Nx'] != caseSize[0] or keyDict['Ny'] != caseSize[1]:
        print(keyDict['Nx'], keyDict['Ny'])
        print("Error in collected data: %s" % keyDict)
        sys.exit(1)

    for run in value:
        nSDD = run['point'][0] * run['point'][1]

        loopT = run['loopTime'] * caseSize[0] * caseSize[1]
        minT = run['minComputeSum'] * caseSize[0] * caseSize[1]
        maxT = run['maxComputeSum'] * caseSize[0] * caseSize[1]
        syncT = (run['maxIterationSum'] - run['maxComputeSum']) * caseSize[0] * caseSize[1]
        subDomainSize = caseSize[0] * caseSize[1] // nSDD

        if np.log2(subDomainSize) == 20:
            print("subDomainSize: %s, Loop: %s, maxT: %s; maxT x Ni: %s, nSDD: %s, %sx%s, Ns: %s, Nt: %s" % (np.log2(subDomainSize), run['loopTime'], maxT, maxT * keyDict['Ni'], nSDD, caseSize[0],  caseSize[1], keyDict['Ns'], keyDict['Nt']))

        #if nSDD > resource:
        #    continue

        #if Nt > 1.0:
        #    continue

        if subDomainSize < minSubdomain[0] * minSubdomain[1]:
            minSubdomain = (caseSize[0] / run['point'][0], caseSize[1] / run['point'][1])

        if subDomainSize > maxSubdomain[0] * maxSubdomain[1]:
            maxSubdomain = (caseSize[0] / run['point'][0], caseSize[1] / run['point'][1])

        if subDomainSize not in loopTimeDict.keys():
            loopTimeDict[subDomainSize] = list()

        loopTimeDict[subDomainSize].append(loopT)

        if np.min(loopTimeDict[subDomainSize]) == loopT:
            syncTimeDict[subDomainSize] = syncT
            minComputeSumTimeDict[subDomainSize] = minT
            maxComputeSumTimeDict[subDomainSize] = maxT

        if Nt == 1.0:
            if subDomainSize not in loopTimeWoHTDict.keys():
                loopTimeWoHTDict[subDomainSize] = list()
            loopTimeWoHTDict[subDomainSize].append(loopT)

#sys.exit(1)

if len(syncTimeDict) == 0:
    print("No data")
    sys.exit(1)

# And now, we must plot that

fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
#ax = fig.add_subplot(211)
ax.set_xscale('log', basex=2)
#ax.set_yscale('log')

firstValueMaxComputeTime = np.min(maxComputeSumTimeDict.values())
ax.plot(sorted(loopTimeDict), [np.min(v) for k, v in sorted(loopTimeDict.items())], 'b+-', label="Loop Time")
#ax.plot(sorted(loopTimeWoHTDict), [np.min(v)  for k, v in sorted(loopTimeWoHTDict.items())], 'b--', label="Loop Time w/o HT")

ax.plot(sorted(syncTimeDict), [v for k, v in sorted(syncTimeDict.items())], 'g+-', label="Sync Time")
ax.plot(sorted(maxComputeSumTimeDict), [v  for k, v in sorted(maxComputeSumTimeDict.items())], 'y+-', label="Compute Time")
ax.plot(sorted(maxComputeSumTimeDict), [firstValueMaxComputeTime for k in sorted(maxComputeSumTimeDict.keys())], 'y--', label="Compute Time ideal")

#for k in loopTimeWoHTDict:
#    ax.plot(np.ones(len(loopTimeWoHTDict[k])) * k, loopTimeWoHTDict[k], 'b*')

for k in loopTimeDict:
    ax.plot(np.ones(len(loopTimeDict[k])) * k, loopTimeDict[k], 'b+')


nodeNumber = (caseSize[0] * caseSize[1] / (maxSubdomain[0] * maxSubdomain[1]))
plt.title('Times from %sx%s to %sx%s subdomain sizes on %sx%s on %s node(s)' % (minSubdomain[0], minSubdomain[1], maxSubdomain[0], maxSubdomain[1], caseSize[0], caseSize[1], nodeNumber))
plt.xlabel('Number of cells in subdomain')
plt.ylabel('Time / iteration')
plt.legend()


# Output
parser.outputCurve("plot/split_scaling_looptime-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(loopTimeDict), [np.min(v) for k, v in sorted(loopTimeDict.items())])
parser.outputCurve("plot/split_scaling_synctime-%sx%s.dat"% (caseSize[0], caseSize[1]), sorted(syncTimeDict), [v for k, v in sorted(syncTimeDict.items())])
parser.outputCurve("plot/split_scaling_comptime-%sx%s.dat"% (caseSize[0], caseSize[1]), sorted(maxComputeSumTimeDict), [v  for k, v in sorted(maxComputeSumTimeDict.items())])
parser.outputCurve("plot/split_scaling_ideal_comptime-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(maxComputeSumTimeDict), [firstValueMaxComputeTime for k in sorted(maxComputeSumTimeDict.keys())])
parser.outputPoint("plot/split_scaling_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), loopTimeDict)


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

sys.exit(1)
