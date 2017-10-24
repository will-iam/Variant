#!/usr/bin/python
# -*- coding:utf-8 -*-

import parser
import sys
import matplotlib.pyplot as plt
import numpy as np
import operator
from collections import *

# make point
caseSize = (256, 256)
sizeDataDict = []

for p in range(0, 7):
    filterDict = {'nSizeX' : caseSize[0], 'nSizeY' : caseSize[1], 'R' : 2**p}
    print filterDict
    data = parser.getData(filterDict)
    if len(data):
        sizeDataDict.append(data)

if len(sizeDataDict) == 0:
    print("No data found.")
    sys.exit(1)

sdsStrongDict = {}
sddStrongDict = {}
for data in sizeDataDict:
    for key, value in data.items():
        keyDict = parser.extractKey(key)
        if keyDict['Nt'] != 1:
            continue

        R = keyDict['R']

        for run in value:
            nSDD = run['point'][0] * run['point'][1]
            t = run['loopTime']
            if nSDD == 1:
                if R not in sdsStrongDict.keys():
                    sdsStrongDict[R] = list()
                sdsStrongDict[R].append(t)
                print 'SDS ressource: %s, loopTime: %s' % (R, t)
            if nSDD == R:
                if R not in sddStrongDict.keys():
                    sddStrongDict[R] = list()
                sddStrongDict[R].append(t)
                print 'SDD ressource: %s, loopTime: %s' % (R, t)


# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
ax.set_xscale('log', basex=2)
ax.set_yscale('log')

firstValue = [np.mean(v) for k, v in sorted(sddStrongDict.items())][0]

#ax.boxplot([v for k,v in sorted(sddStrongDict.items())], positions=sorted(sddStrongDict.keys()))
#ax.boxplot([v for k,v in sorted(sdsStrongDict.items())], positions=sorted(sdsStrongDict.keys()))

#sorted(sdsStrongDict.items(), key=operator.itemgetter(0))
ax.plot(sorted(sdsStrongDict), [np.mean(v) for k, v in sorted(sdsStrongDict.items(), key=operator.itemgetter(0))], 'g+-', label="SDS scaling")
ax.plot(sorted(sddStrongDict), [np.mean(v) for k, v in sorted(sddStrongDict.items())], 'b+-', label="SDD scaling")
ax.plot(sorted(sdsStrongDict), [firstValue / k for k in sorted(sdsStrongDict.keys())], 'k--', label="ideal")

for k in sdsStrongDict:
    ax.plot(np.full(len(sdsStrongDict[k]), k), sdsStrongDict[k], 'g+')
for k in sddStrongDict:
    ax.plot(np.full(len(sddStrongDict[k]), k), sddStrongDict[k], 'b+')
    #ax.plot(sorted(sddStrongDict), [np.mean(v) for k, v in sorted(sddStrongDict.items())], 'b+', label="SDD scaling")


plt.title('Strong Scaling')
plt.xlabel('Core(s)')
plt.ylabel('(Scaled) Loop Time')
plt.legend()
plt.show()

sys.exit(1)
