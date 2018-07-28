#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
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
res = 64
filterDict = {'nSizeX' : caseSize[0], 'nSizeY' : caseSize[1], 'R' : res}
data = parser.getData(filterDict)
if len(data):
    sizeDataDict.append(data)

if len(sizeDataDict) == 0:
    print("No data found.")
    sys.exit(1)

commonWithoutHTDict = dict()
commonWithHTDict = dict()

for data in sizeDataDict:
    for key, value in data.items():
        keyDict = parser.extractKey(key)
        Nt = keyDict['Nt']
        Ns = keyDict['Ns']
        for run in value:

            if run['point'][2] != res:
                continue

            if Nt >= 4.0:
                continue

            nCommonSDS = float(run['nCommonSDS']) / (Ns * Nt * run['point'][2])
            t = run['loopTime']

            if nCommonSDS < 8.0 and Nt > 1.0 and t > 20.e-6:
                print nCommonSDS, '->', run['nCommonSDS'], keyDict['Nt'], keyDict['Ns'], run['point'][2], t, (keyDict['Ns'] * keyDict['Nt'] * run['point'][2])
 
            if Nt == 1.0:
                commonWithoutHTDict.setdefault(nCommonSDS, list()).append(t)
            else:
                commonWithHTDict.setdefault(nCommonSDS, list()).append(t)

            
minPoint = commonWithoutHTDict.keys()[0]
minValue = np.min(commonWithoutHTDict.values()[0])
for item in commonWithoutHTDict.items():
    if np.min(item[1]) < minValue:
        minValue = np.min(item[1])
        minPoint = item[0]

print("min time value w/o HT = %s on point: %s" % (minValue, minPoint))

minPoint = commonWithHTDict.keys()[0]
minValue = np.min(commonWithHTDict.values()[0])
for item in commonWithHTDict.items():
    if np.min(item[1]) < minValue:
        minValue = np.min(item[1])
        minPoint = item[0]

print("min time value of with HT points = %s on point: %s" % (minValue, minPoint))

# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
#ax.set_xscale('log', basex=2)
#ax.set_yscale('log')

ax.plot(sorted(commonWithoutHTDict), [np.min(v) for k, v in sorted(commonWithoutHTDict.items(), key=operator.itemgetter(0))], 'gx--', label="Min. time per % (without HT)")
ax.plot(sorted(commonWithHTDict), [np.min(v) for k, v in sorted(commonWithHTDict.items(), key=operator.itemgetter(0))], 'go-', label="Min. time per %")

for k in commonWithoutHTDict:
    ax.plot(np.ones(len(commonWithoutHTDict[k]))*k, commonWithoutHTDict[k], 'gx')

for k in commonWithHTDict:
    ax.plot(np.ones(len(commonWithHTDict[k]))*k, commonWithHTDict[k], 'go')


parser.outputCurve("plot/common_scaling_wo_HT-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(commonWithoutHTDict), [np.min(v) for k, v in sorted(commonWithoutHTDict.items(), key=operator.itemgetter(0))])
parser.outputCurve("plot/common_scaling_HT-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(commonWithHTDict), [np.min(v) for k, v in sorted(commonWithHTDict.items(), key=operator.itemgetter(0))])

parser.outputPoint("plot/common_scaling_wo_HT_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), commonWithoutHTDict)
parser.outputPoint("plot/common_scaling_HT_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), commonWithHTDict)

plt.title('SDS Common Scaling of %s x %s on %s cores' % (caseSize[0], caseSize[1], res))
plt.xlabel('SDS Common Percentage')
plt.ylabel('Loop Time / (cell x Iteration)')
plt.legend()



plt.show()


