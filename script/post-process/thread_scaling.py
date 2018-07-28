#!/usr/bin/python
# -*- coding:utf-8 -*-

import parser
import sys
import matplotlib.pyplot as plt
#plt.style.use('ggplot')
import numpy as np
import operator
from collections import *

# make point
caseSize = (2048, 2048)
res = 64

if parser.args.x and parser.args.y:
    caseSize = (parser.args.x, parser.args.y)

if parser.args.res:
    res = parser.args.res

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
        Ns = keyDict['Ns']
        for run in value:
            nSDD = run['point'][0] * run['point'][1]
            if nSDD != 1:
                continue

#            if Nt >= 4.0:
#                continue

            t = run['loopTime'] 
            if Nt not in threadRatioDict.keys():
                threadRatioDict[Nt] = list()
            threadRatioDict[Nt].append(t)


            nCommonSDS = float(run['nCommonSDS']) / (Ns * Nt * run['point'][2])
            if Nt > 4.18 and Nt < 4.6 and t < 2.e-5:
                print 'Resource: %s, nSDD: %s, Thread Number: %s, SDS Number: %s, Common %s %%, loopTime: %s' % (res, nSDD, Nt, Ns, nCommonSDS, t)

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

ax.plot(sorted(threadRatioDict), [np.min(v) for k, v in sorted(threadRatioDict.items(), key=operator.itemgetter(0))], 'go-', label="HT Scaling")
for k in threadRatioDict:
    ax.plot(np.ones(len(threadRatioDict[k]))*k, threadRatioDict[k], 'g+')


plt.title('Hyperthread Scaling of %s x %s on %s core(s)' % (caseSize[0], caseSize[1], res))
plt.xlabel('Thread ratio')
plt.ylabel('Loop Time / (cell x Iteration)')
plt.legend()


parser.outputCurve("plot/thread_scaling-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(threadRatioDict), [np.min(v) for k, v in sorted(threadRatioDict.items())])
parser.outputPoint("plot/thread_scaling_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), threadRatioDict)

plt.show()


