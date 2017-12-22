#!/usr/bin/python
# -*- coding:utf-8 -*-

import parser
import sys
import matplotlib.pyplot as plt
import numpy as np
import operator
from collections import *

# make point
caseSize = (4096, 4096)
sizeDataDict = []


filterDict = {'nSizeX' : caseSize[0], 'nSizeY' : caseSize[1], 'R' : 64}
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
        Ns = keyDict['Ns']
        
        for run in value:
            nSDD = run['point'][0] * run['point'][1]
            if nSDD != 1:
                continue

            t = run['loopTime']

            if t < 4.92e-6:        
                print Ns, '->', keyDict['Nt'], run['nCommonSDS'], t

             
            if Ns not in sdsRatioDict.keys():
                sdsRatioDict[Ns] = list()
            sdsRatioDict[Ns].append(t)

if sdsRatioDict == dict():
    print("No data found for %s" % filterDict)
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


ax.plot(sorted(sdsRatioDict), [np.min(v) for k, v in sorted(sdsRatioDict.items(), key=operator.itemgetter(0))], 'go-', label=parser.args.case)
for k in sdsRatioDict:
    ax.plot(np.full(len(sdsRatioDict[k]), k), sdsRatioDict[k], 'g+')


plt.title('SDS Ratio Scaling of %s x %s' % (caseSize[0], caseSize[1]))
plt.xlabel('SDS ratio(s)')
plt.ylabel('Loop Time / (cell x Iteration)')
plt.legend()



plt.show()


