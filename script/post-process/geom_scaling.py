#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Plot to compare different SDS geometry: random or line.
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
sizeDataDict = []

for p in range(0, 7):
    filterDict = {'nSizeX' : caseSize[0], 'nSizeY' : caseSize[1], 'R' : 2**p}
    data = parser.getData(filterDict)
    if len(data):
        sizeDataDict.append(data)

if len(sizeDataDict) == 0:
    print("No data found.")
    sys.exit(1)

sdsWithoutHTRandomDict = {}
sdsWithoutHTLineDict = {}

sdsRandomDict = {}
sdsLineDict = {}

for data in sizeDataDict:
    for key, value in data.items():
        keyDict = parser.extractKey(key)

        R = keyDict['R']
        Nt = keyDict['Nt']

        for run in value:
            nSDD = run['point'][0] * run['point'][1]
    
            if nSDD != R:
                continue

            #t = run['loopTime'] * keyDict['Ny'] * keyDict['Nx'] * R
            t = run['loopTime']
            if run['sdsGeom'] == 'line':
                if Nt == 1.0:
                    sdsWithoutHTLineDict.setdefault(R, list()).append(t)
                sdsLineDict.setdefault(R, list()).append(t)
            else:
                if Nt == 1.0:
                    sdsWithoutHTRandomDict.setdefault(R, list()).append(t)
                sdsRandomDict.setdefault(R, list()).append(t)


# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
#ax = fig.add_subplot(211)
if not parser.args.nolog:
    ax.set_xscale('log', basex=2)
    ax.set_yscale('log')

if len(sdsWithoutHTLineDict) > 0:
    firstValueLine = [np.min(v) for k, v in sorted(sdsWithoutHTLineDict.items())][0]
    #ax.plot(sorted(sdsLineDict), [np.min(v) for k, v in sorted(sdsLineDict.items(), key=operator.itemgetter(0))], 'go-', label="Line geom. scaling")
    ax.plot(sorted(sdsWithoutHTLineDict), [np.min(v) for k, v in sorted(sdsWithoutHTLineDict.items(), key=operator.itemgetter(0))], 'g+-', label="Line geom. scaling w/o HT")
    ax.plot(sorted(sdsLineDict), [firstValueLine / k for k in sorted(sdsLineDict.keys())], 'g--', label="Line geom. ideal")
    for k in sdsLineDict:
        ax.plot(np.ones(len(sdsLineDict[k])) * k, [i for i in sdsLineDict[k]], 'g+')

if len(sdsWithoutHTRandomDict) > 0:
    firstValueRandom = [np.min(v) for k, v in sorted(sdsWithoutHTRandomDict.items())][0]
    #ax.plot(sorted(sdsRandomDict), [np.min(v) for k, v in sorted(sdsRandomDict.items(), key=operator.itemgetter(0))], 'yo-', label="Random geom. scaling")
    ax.plot(sorted(sdsWithoutHTRandomDict), [np.min(v) for k, v in sorted(sdsWithoutHTRandomDict.items(), key=operator.itemgetter(0))], 'y+-', label="Random geom. scaling w/o HT")
    ax.plot(sorted(sdsRandomDict), [firstValueRandom / k for k in sorted(sdsRandomDict.keys())], 'y--', label="Random geom. ideal")
    for k in sdsRandomDict:
        ax.plot(np.ones(len(sdsRandomDict[k])) * k, [i for i in sdsRandomDict[k]], 'y+')

parser.outputCurve("plot/geom_scaling_line-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sdsWithoutHTLineDict), [np.min(v) for k, v in sorted(sdsWithoutHTLineDict.items(), key=operator.itemgetter(0))])
parser.outputCurve("plot/geom_scaling_line_ideal-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sdsWithoutHTLineDict), [firstValueLine / k for k in sorted(sdsLineDict.keys())])

parser.outputCurve("plot/geom_scaling_random-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sdsWithoutHTRandomDict), [np.min(v) for k, v in sorted(sdsWithoutHTRandomDict.items(), key=operator.itemgetter(0))])
parser.outputCurve("plot/geom_scaling_random_ideal-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sdsWithoutHTRandomDict), [firstValueRandom / k for k in sorted(sdsWithoutHTRandomDict.keys())])

parser.outputPoint("plot/geom_scaling_line_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), sdsWithoutHTLineDict)
parser.outputPoint("plot/geom_scaling_random_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), sdsWithoutHTRandomDict)

plt.title('SDS Geometry Scaling of %sx%s' % (caseSize[0], caseSize[1]))
plt.xlabel('Core(s)')
plt.ylabel('(Log scaled) Loop Time')
plt.legend()
plt.show()

