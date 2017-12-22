#!/usr/bin/python
# -*- coding:utf-8 -*-

import parser
import sys
import matplotlib.pyplot as plt
import numpy as np
import operator
from collections import *

# make point
initSize = 512
maxPower = 7
caseSizeX = initSize / 2
caseSizeY = initSize
sizeDataDict = []
for p in range(0, maxPower):
	# Defining case directory
    if p % 2 == 1:
        caseSizeY = caseSizeY * 2
    else:
        caseSizeX = caseSizeX * 2
    filterDict = {'nSizeX' : caseSizeX, 'nSizeY' : caseSizeY, 'R' : 2**p}
    print filterDict
    data = parser.getData(filterDict)
    if len(data):
        sizeDataDict.append(data)

if len(sizeDataDict) == 0:
    print("No data found.")
    sys.exit(1)

sdsWeakDict = dict()
sddWeakDict = dict()
hybridWeakDict = dict()
normalizeDict = dict()
for data in sizeDataDict:
    for key, value in data.items():
        keyDict = parser.extractKey(key)
        R = keyDict['R']
        Nt = keyDict['Nt']

        #if keyDict['Nt'] > 1.0:
        #    continue

        #if keyDict['Nt'] > 1.0 and R == 1:
        #    continue

        normalizeDict[R] = keyDict['Ny'] * keyDict['Nx']
        for run in value:
            nSDD = run['point'][0] * run['point'][1]
            t = run['loopTime'] * normalizeDict[R]
            if nSDD == 1:
                if R not in sdsWeakDict.keys():
                    sdsWeakDict[R] = list()
                sdsWeakDict[R].append(t)
                #print 'SDS ressource: %s, loopTime: %s' % (R, t)
            if nSDD == R and Nt == 1.0:
                if R not in sddWeakDict.keys():
                    sddWeakDict[R] = list()
                sddWeakDict[R].append(t)
                #print 'SDD ressource: %s, loopTime: %s' % (R, t)
            if nSDD != R and nSDD != 1:
                if R not in hybridWeakDict.keys():
                    hybridWeakDict[R] = list()
                hybridWeakDict[R].append(t)
                #print 'SDD ressource: %s, loopTime: %s' % (R, t)


# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
#ax = fig.add_subplot(111)
ax = fig.add_subplot(211)
ax.set_xscale('log', basex=2)
#ax.set_yscale('log')

firstValueSDD = [np.min(v) for k, v in sorted(sddWeakDict.items())][0]
firstValueSDS = [np.min(v) for k, v in sorted(sdsWeakDict.items())][0]

ax.plot(sorted(sdsWeakDict), [np.min(v) / normalizeDict[k] for k, v in sorted(sdsWeakDict.items(), key=operator.itemgetter(0))], 'g+-', label="SDS scaling")
ax.plot(sorted(sddWeakDict), [np.min(v) / normalizeDict[k] for k, v in sorted(sddWeakDict.items())], 'b+-', label="SDD scaling")
#ax.plot(sorted(hybridWeakDict), [np.min(v) / normalizeDict[k] for k, v in sorted(hybridWeakDict.items())], 'y+-', label="Hybrid scaling")
ax.plot(sorted(sddWeakDict), [firstValueSDD / normalizeDict[k] for k in sorted(sddWeakDict.keys())], 'b--', label="SDD ideal")
ax.plot(sorted(sdsWeakDict), [firstValueSDS / normalizeDict[k] for k in sorted(sdsWeakDict.keys())], 'g--', label="SDS ideal")

for k in sdsWeakDict:
    ax.plot(np.full(len(sdsWeakDict[k]), k), [i / normalizeDict[k] for i in sdsWeakDict[k]], 'g+')
for k in sddWeakDict:
    ax.plot(np.full(len(sddWeakDict[k]), k), [i / normalizeDict[k] for i in sddWeakDict[k]], 'b+')


plt.title('Weak Scaling from %sx%s to %sx%s' % (initSize, initSize, initSize * 2**((maxPower-1) / 2), initSize * 2**((maxPower-1) / 2)) )
plt.xlabel('Core(s)')
plt.ylabel('(Log) Loop Time / (cell x iteration)')
plt.legend()

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

plt.show()

sys.exit(1)
