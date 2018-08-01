#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
import parser
import sys
import matplotlib.pyplot as plt
#plt.style.use('ggplot')
import numpy as np
import operator
from collections import *

"""
Mesure de l'écart-type sur même runs ie sur même machine avec les mêmes options à la suite.
"""

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


runWithoutHTDict = dict()
runWithHTDict = dict()

for data in sizeDataDict:
    for key, value in data.items():
        # Pas d'écart type sur un run.
        if len(value) < 2:
            continue

        keyDict = parser.extractKey(key)

        for run in value:
            # std_deviation / Size_X * Size_Y * Resource * TotalLoopTime
            p = 100.0 * run["stdLoopTime"] / run["meanLoopTime"]

            print run["runNumber"], run["meanLoopTime"], run["stdLoopTime"], p
            if keyDict['Nt'] == 1.0:
                runWithoutHTDict.setdefault(run["runNumber"], list()).append(p)
            else:
                runWithHTDict.setdefault(run["runNumber"], list()).append(p)

# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
#ax.set_xscale('log', basex=2)
#ax.set_yscale('log')

ax.plot(sorted(runWithoutHTDict), [np.max(v) for k, v in sorted(runWithoutHTDict.items(), key=operator.itemgetter(0))], 'gx--', label="Mean time per % (without HT)")
ax.plot(sorted(runWithHTDict), [np.max(v) for k, v in sorted(runWithHTDict.items(), key=operator.itemgetter(0))], 'go-', label="Mean time per %")

for k in runWithoutHTDict:
    ax.plot(np.ones(len(runWithoutHTDict[k]))*k, runWithoutHTDict[k], 'gx')

for k in runWithHTDict:
    ax.plot(np.ones(len(runWithHTDict[k]))*k, runWithHTDict[k], 'go')

plt.title('Run Scaling of %s x %s on %s cores' % (caseSize[0], caseSize[1], res))
plt.xlabel('Run number')
plt.ylabel('std-deviation(%) / (Cell x Iteration)')
plt.legend()


parser.outputCurve("plot/run_scaling_wo_HT-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(runWithoutHTDict), [np.max(v) for k, v in sorted(runWithoutHTDict.items(), key=operator.itemgetter(0))])
parser.outputCurve("plot/run_scaling_HT-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(runWithHTDict), [np.max(v) for k, v in sorted(runWithHTDict.items(), key=operator.itemgetter(0))])

parser.outputPoint("plot/run_scaling_wo_HT_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), runWithoutHTDict)
parser.outputPoint("plot/run_scaling_HT_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), runWithHTDict)

plt.show()


