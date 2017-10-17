#!/usr/bin/python
# -*- coding:utf-8 -*-

import parser
import sys
import matplotlib.pyplot as plt
import numpy as np
from collections import *

# make point
pointList = []
initSize = 128
caseSizeX = initSize / 2
caseSizeY = initSize
for p in [0, 1, 2, 3, 4, 5, 6]:
	# Defining case directory
    if p % 2 == 1:
        caseSizeY = caseSizeY * 2
    else:
        caseSizeX = caseSizeX * 2
    pointList.append((caseSizeX, caseSizeY, 2**p))

pointDataDict = {}
for point in pointList:
    data = {}
    caseKey = makeCaseKey(point[0], point[1]) + ':' + str(point[2])
    try:
        data = parser.getData(caseKey)
    except:
        pass
    if len(data):
        pointDataDict[point] = data

sdsWeakDict = {}
sddWeakDict = {}
for point, data in pointDataDict:
    sddWeakDict[point] = []
    sdsWeakDict[point] = []
    for item in data.items():
        keyDict = parser.extractKey(item[0])
        if keyDict['Nt'] != 1:
            continue

        for run in item[1]:
            if run['nSDD'] == 1:
                t = run['loopTime']
                sdsWeakDict[point].append(t)
                print 'ressource: %s, nThreads: %s, loopTime: %s' % (keyDict['R'], Nt, t)
            if run['nSDD'] == keyDict['R']:
                t = run['loopTime']
                sddWeakDict[point].append(t)
                print 'ressource: %s, nThreads: %s, loopTime: %s' % (keyDict['R'], Nt, t)

# And now, we must plot that
sys.exit(1)

fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
#ax.set_xscale('log', basex=2)
#ax.set_yscale('log')

for Nt, sds_time in ht_sds_time.items():
    ordered_sds_time = OrderedDict([(k, np.mean(sds_time[k])) for k in sorted(sds_time)])
    minTime = np.min(ordered_sds_time.values())
    maxTime = np.max(ordered_sds_time.values())
    print "Nt: %s, minTime: %s, maxTime: %s, ratio: %s" % (Nt, minTime, maxTime, maxTime / minTime)
    ax.plot(ordered_sds_time.keys(), ordered_sds_time.values(), label="%s thread(s) per core" % Nt)
    ax.boxplot(sds_time.values(), positions=sds_time.keys())

plt.title(caseKey + ' on 64 cores')
plt.xlabel('SDS number per thread')
plt.ylabel('Time')
plt.legend()
plt.show()

sys.exit(1)
