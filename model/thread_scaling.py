#!/usr/bin/python
# -*- coding:utf-8 -*-

import parser
import sys
import matplotlib.pyplot as plt
import numpy as np
import operator
from collections import *

# make point
caseSize = (1024, 2048)
res = 8
sizeDataDict = []


filterDict = {'nSizeX' : caseSize[0], 'nSizeY' : caseSize[1], 'R' : res}
data = parser.getData(filterDict)
if len(data):
    sizeDataDict.append(data)

if len(sizeDataDict) == 0:
    print("No data found.")
    sys.exit(1)

threadRatioDict = {}
for data in sizeDataDict:
    for key, value in data.items():
        keyDict = parser.extractKey(key)
        
        Nt = keyDict['Nt']
        
        for run in value:
            nSDD = run['point'][0] * run['point'][1]
            if nSDD != 1:
                continue

            t = run['loopTime'] 
            if Nt not in threadRatioDict.keys():
                threadRatioDict[Nt] = list()
            threadRatioDict[Nt].append(t)
            #print 'Resource: %s, Thread Number: %s, Thread Number: %s, loopTime: %s' % (keyDict['R'], keyDict['Nt'], ratio, t)

minPoint = threadRatioDict.keys()[0]
minValue = np.min(threadRatioDict.values()[0])
for item in threadRatioDict.items():
    if np.min(item[1]) < minValue:
        minValue = np.min(item[1])
        minPoint = item[0]

print("min time value = %s on point: %s" % (minValue, minPoint))

# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
#ax.set_xscale('log', basex=2)
#ax.set_yscale('log')


ax.plot(sorted(threadRatioDict), [np.mean(v) for k, v in sorted(threadRatioDict.items(), key=operator.itemgetter(0))], 'go-', label=parser.args.case)
for k in threadRatioDict:
    ax.plot(np.full(len(threadRatioDict[k]), k), threadRatioDict[k], 'g+')


plt.title('Thread Scaling of %s x %s on %s core(s)' % (caseSize[0], caseSize[1], res))
plt.xlabel('Thread(s)')
plt.ylabel('Loop Time / (cell x Iteration)')
plt.legend()



plt.show()


