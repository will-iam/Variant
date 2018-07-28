#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Plot the scaling of the sds ratio (per thread) parameter.
"""

import parser
import sys
import matplotlib.pyplot as plt
#plt.style.use('ggplot')
import numpy as np
import operator
from collections import *

# make point
caseSize = (2048, 2048)
if parser.args.x and parser.args.y:
    caseSize = (parser.args.x, parser.args.y)

sizeDataDict = []
filterDict = {'nSizeX' : caseSize[0], 'nSizeY' : caseSize[1], 'R' : 64}
data = parser.getData(filterDict)
if len(data):
    sizeDataDict.append(data)

if len(sizeDataDict) == 0:
    print("No data found.")
    sys.exit(1)

sdsRatioDict = dict()
sdsRatioWithoutHTDict = dict()
for data in sizeDataDict:
    for key, value in data.items():
        keyDict = parser.extractKey(key)
        Ns = keyDict['Ns']
        Nt = keyDict['Nt']
        for run in value:
            nSDD = run['point'][0] * run['point'][1]
            if nSDD != 1:
                continue

            t = run['loopTime']
            #print Ns, '->', keyDict['Nt'], run['nCommonSDS'], t

            if Nt == 1.0:
                sdsRatioWithoutHTDict.setdefault(Ns, list()).append(t)
            else:
                sdsRatioDict.setdefault(Ns, list()).append(t)

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

minPoint = sdsRatioWithoutHTDict.keys()[0]
minValue = np.min(sdsRatioWithoutHTDict.values()[0])
for item in sdsRatioWithoutHTDict.items():
    if np.min(item[1]) < minValue:
        minValue = np.min(item[1])
        minPoint = item[0]
print("min time value without HT = %s on point: %s" % (minValue, minPoint))


# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)

ax.plot(sorted(sdsRatioWithoutHTDict), [np.min(v) for k, v in sorted(sdsRatioWithoutHTDict.items(), key=operator.itemgetter(0))], 'gx--', label="Min. time per ratio (without HT)")
ax.plot(sorted(sdsRatioDict), [np.min(v) for k, v in sorted(sdsRatioDict.items(), key=operator.itemgetter(0))], 'go-', label="Min. time per ratio")
for k in sdsRatioDict:
    ax.plot(np.ones(len(sdsRatioDict[k]))*k, sdsRatioDict[k], 'g+')
for k in sdsRatioWithoutHTDict:
    ax.plot(np.ones(len(sdsRatioWithoutHTDict[k]))*k, sdsRatioWithoutHTDict[k], 'gx')

plt.title('SDS Ratio Scaling of %s x %s' % (caseSize[0], caseSize[1]))
plt.xlabel('SDS ratio(s)')
plt.ylabel('Loop Time / (cell x Iteration)')
plt.legend()


parser.outputCurve("plot/sds_scaling_wo_HT-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sdsRatioWithoutHTDict), [np.min(v) for k, v in sorted(sdsRatioWithoutHTDict.items(), key=operator.itemgetter(0))])
parser.outputCurve("plot/sds_scaling_HT-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sdsRatioDict), [np.min(v) for k, v in sorted(sdsRatioDict.items(), key=operator.itemgetter(0))])

parser.outputPoint("plot/sds_scaling_wo_HT_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), sdsRatioWithoutHTDict)
parser.outputPoint("plot/sds_scaling_HT_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), sdsRatioDict)


plt.show()


