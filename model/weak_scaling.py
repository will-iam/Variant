#!/usr/bin/python
# -*- coding:utf-8 -*-

import parser
import sys
import matplotlib.pyplot as plt
import numpy as np
import operator
from collections import *

# make point
sizeList = []
initSize = 64
caseSizeX = initSize / 2
caseSizeY = initSize
for p in [0, 1, 2, 3, 4, 5, 6]:
	# Defining case directory
    if p % 2 == 1:
        caseSizeY = caseSizeY * 2
    else:
        caseSizeX = caseSizeX * 2
    point = (caseSizeX, caseSizeY, 2**p)
    print point
    sizeList.append(point)


sizeDataDict = {}
for size in sizeList:
    data = {}
    caseKey = parser.makeCaseKey(size[0], size[1]) + ':' + str(size[2])
    data = parser.getData(caseKey)
    if len(data):
        sizeDataDict[size] = data

sdsWeakDict = {}
sddWeakDict = {}
for size, data in sizeDataDict.items():
    for key, value in data.items():
        keyDict = parser.extractKey(key)
        if keyDict['Nt'] != 1:
            continue

        R = keyDict['R']

        for run in value:
            nSDD = run['point'][0] * run['point'][1]
            t = run['loopTime']
            if nSDD == 1:
                if R not in sdsWeakDict.keys():
                    sdsWeakDict[R] = list()
                sdsWeakDict[R].append(t)
                print 'SDS ressource: %s, loopTime: %s' % (R, t)
            if nSDD == R:
                if R not in sddWeakDict.keys():
                    sddWeakDict[R] = list()
                sddWeakDict[R].append(t)
                print 'SDD ressource: %s, loopTime: %s' % (R, t)


# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
ax.set_xscale('log', basex=2)
ax.set_yscale('log')

firstValue = [np.mean(v) for k, v in sorted(sddWeakDict.items())][0]

#ax.boxplot([v for k,v in sorted(sddWeakDict.items())], positions=sorted(sddWeakDict.keys()))
#ax.boxplot([v for k,v in sorted(sdsWeakDict.items())], positions=sorted(sdsWeakDict.keys()))

#sorted(sdsWeakDict.items(), key=operator.itemgetter(0))
ax.plot(sorted(sdsWeakDict), [np.mean(v) for k, v in sorted(sdsWeakDict.items(), key=operator.itemgetter(0))], 'g+-', label="SDS scaling")
ax.plot(sorted(sddWeakDict), [np.mean(v) for k, v in sorted(sddWeakDict.items())], 'b+-', label="SDD scaling")
ax.plot(sorted(sdsWeakDict), [firstValue / k for k in sorted(sdsWeakDict.keys())], 'k--', label="ideal")

for k in sdsWeakDict:
    ax.plot(np.full(len(sdsWeakDict[k]), k), sdsWeakDict[k], 'g+')
for k in sddWeakDict:
    ax.plot(np.full(len(sddWeakDict[k]), k), sddWeakDict[k], 'b+')
    #ax.plot(sorted(sddWeakDict), [np.mean(v) for k, v in sorted(sddWeakDict.items())], 'b+', label="SDD scaling")


plt.title('Weak Scaling')
plt.xlabel('Core(s)')
plt.ylabel('(Scaled) Loop Time')
plt.legend()
plt.show()

sys.exit(1)
