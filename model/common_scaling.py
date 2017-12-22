#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import parser
import sys
import matplotlib.pyplot as plt
import numpy as np
import operator
from collections import *

# make point
caseSize = (4096, 4096)
sizeDataDict = []
resource = 64

filterDict = {'nSizeX' : caseSize[0], 'nSizeY' : caseSize[1], 'R' : resource}
data = parser.getData(filterDict)
if len(data):
    sizeDataDict.append(data)

if len(sizeDataDict) == 0:
    print("No data found.")
    sys.exit(1)

sdsRatioDict = dict()
for data in sizeDataDict:
    for key, value in data.items():
        keyDict = parser.extractKey(key)
        for run in value:
            if run['point'][2] == 1:
                continue

            nCommonSDS = float(run['nCommonSDS'])/ (keyDict['Ns'] * keyDict['Nt'] * run['point'][2])
            t = run['loopTime']

            if t < 4.81e-06:
                print nCommonSDS, '->', keyDict['Nt'], keyDict['Ns'], run['point'][2], t, (keyDict['Ns'] * keyDict['Nt'] * run['point'][2])
 
            if nCommonSDS not in sdsRatioDict.keys():
                sdsRatioDict[nCommonSDS] = list()
            sdsRatioDict[nCommonSDS].append(t)


if sdsRatioDict == dict():
    print("No data found.")
    sys.exit(1)

minPoint = sdsRatioDict.keys()[0]
minValue = np.min(sdsRatioDict.values()[0])
for item in sdsRatioDict.items():
    if np.min(item[1]) < minValue:
        minValue = np.min(item[1])
        minPoint = item[0]

print("min time value = %s on point: %s" % (minValue, minPoint))

# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
#ax.set_xscale('log', basex=2)
#ax.set_yscale('log')


ax.plot(sorted(sdsRatioDict), [np.min(v) for k, v in sorted(sdsRatioDict.items(), key=operator.itemgetter(0))], 'go-', label="no random")
for k in sdsRatioDict:
    ax.plot(np.full(len(sdsRatioDict[k]), k), sdsRatioDict[k], 'g+')


plt.title('SDS Ratio Scaling of %s x %s' % (caseSize[0], caseSize[1]))
plt.xlabel('SDS Common Size')
plt.ylabel('Loop Time / (cell x Iteration)')
plt.legend()



plt.show()


