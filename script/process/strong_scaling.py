#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
"""

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
sdsWithoutHTStrongDict = {}

sddStrongDict = {}
sddWithoutHTStrongDict = {}


for data in sizeDataDict:
    for key, value in data.items():
        keyDict = parser.extractKey(key)

        R = keyDict['R']
        Nt = keyDict['Nt']

        for run in value:
            nSDD = run['point'][0] * run['point'][1]
            t = run['loopTime'] * keyDict['Ny'] * keyDict['Nx'] * R
            if nSDD == 1:
                if Nt == 1.0:
                    if R not in sdsWithoutHTStrongDict.keys():
                        sdsWithoutHTStrongDict[R] = list()
                    sdsWithoutHTStrongDict[R].append(t)
                    #print 'SDS without HT ressource: %s, loopTime: %s, Nt: %s, %sx%s' % (R, t, Nt, keyDict['Ny'], keyDict['Nx'])

                if R not in sdsStrongDict.keys():
                    sdsStrongDict[R] = list()
                sdsStrongDict[R].append(t)
                #print 'SDS ressource: %s, loopTime: %s, Nt: %s, %sx%s' % (R, t, Nt, keyDict['Ny'], keyDict['Nx'])

            if nSDD == R:
                if Nt == 1.0:
                    if R not in sddWithoutHTStrongDict.keys():
                        sddWithoutHTStrongDict[R] = list()
                    sddWithoutHTStrongDict[R].append(t)

                if R not in sddStrongDict.keys():
                    sddStrongDict[R] = list()
                sddStrongDict[R].append(t)



# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
#ax = fig.add_subplot(211)
if not parser.args.nolog:
    ax.set_xscale('log', basex=2)
    ax.set_yscale('log')

if len(sddWithoutHTStrongDict) > 0:
    firstValueSDD = [np.min(v) for k, v in sorted(sddWithoutHTStrongDict.items())][0]
else:
    firstValueSDD = 0.

firstValueSDS = [np.min(v) for k, v in sorted(sdsWithoutHTStrongDict.items())][0]

ax.plot(sorted(sdsStrongDict), [np.min(v) / k for k, v in sorted(sdsStrongDict.items(), key=operator.itemgetter(0))], 'go-', label="SDS scaling")
ax.plot(sorted(sdsWithoutHTStrongDict), [np.min(v) / k for k, v in sorted(sdsWithoutHTStrongDict.items(), key=operator.itemgetter(0))], 'g+-', label="SDS scaling w/o HT")

ax.plot(sorted(sddStrongDict), [np.min(v) / k for k, v in sorted(sddStrongDict.items())], 'bo-', label="SDD scaling")
ax.plot(sorted(sddWithoutHTStrongDict), [np.min(v) / k for k, v in sorted(sddWithoutHTStrongDict.items())], 'b+-', label="SDD scaling w/o HT")

ax.plot(sorted(sdsStrongDict), [firstValueSDS / k for k in sorted(sdsStrongDict.keys())], 'g--', label="SDS ideal")
ax.plot(sorted(sddStrongDict), [firstValueSDD / k for k in sorted(sddStrongDict.keys())], 'b--', label="SDD ideal")

for k in sdsStrongDict:
    ax.plot(np.ones(len(sdsStrongDict[k])) * k, [i / k for i in sdsStrongDict[k]], 'g+')
for k in sddStrongDict:
    ax.plot(np.ones(len(sddStrongDict[k])) * k, [i / k for i in sddStrongDict[k]], 'b+')



parser.outputCurve("plot/strong_scaling_sds_HT-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sdsStrongDict), [np.min(v) / k for k, v in sorted(sdsStrongDict.items(), key=operator.itemgetter(0))])
parser.outputCurve("plot/strong_scaling_sds_wo_HT-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sdsWithoutHTStrongDict), [np.min(v) / k for k, v in sorted(sdsWithoutHTStrongDict.items(), key=operator.itemgetter(0))])
parser.outputCurve("plot/strong_scaling_sdd_HT-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sddStrongDict), [np.min(v) / k for k, v in sorted(sddStrongDict.items(), key=operator.itemgetter(0))])
parser.outputCurve("plot/strong_scaling_sdd_wo_HT-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sddWithoutHTStrongDict), [np.min(v) / k for k, v in sorted(sddWithoutHTStrongDict.items(), key=operator.itemgetter(0))])

parser.outputCurve("plot/strong_scaling_sds_ideal-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sdsStrongDict), [firstValueSDS / k for k in sorted(sdsStrongDict.keys())])
parser.outputCurve("plot/strong_scaling_sdd_ideal-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sddStrongDict), [firstValueSDD / k for k in sorted(sddStrongDict.keys())])


parser.outputPoint("plot/strong_scaling_sds_HT_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), sdsStrongDict)
parser.outputPoint("plot/strong_scaling_sdd_HT_dot-%sx%s.dat" % (caseSize[0], caseSize[1]), sddStrongDict)


plt.title('Strong Scaling of %sx%s on 64 cores' % (caseSize[0], caseSize[1]))
plt.xlabel('Core(s)')
plt.ylabel('(Log scaled) Loop Time')
plt.legend()
plt.show()
sys.exit(0)

bx = fig.add_subplot(212)
bx.set_xscale('log', basex=2)
bx.plot(sorted(sdsStrongDict), [np.min(v) for k, v in sorted(sdsStrongDict.items(), key=operator.itemgetter(0))], 'g+-', label="SDS scaling")
bx.plot(sorted(sddWithoutHTStrongDict), [np.min(v) for k, v in sorted(sddWithoutHTStrongDict.items())], 'b+-', label="SDD scaling w/o HT")
bx.plot(sorted(sdsStrongDict), [firstValueSDS for k in sorted(sdsStrongDict.keys())], 'g--', label="SDS ideal")
bx.plot(sorted(sddWithoutHTStrongDict), [firstValueSDD for k in sorted(sddWithoutHTStrongDict.keys())], 'b--', label="SDD ideal")

for k in sdsStrongDict:
    bx.plot(np.full(len(sdsStrongDict[k]), k), sdsStrongDict[k], 'g+')
for k in sddWithoutHTStrongDict:
    bx.plot(np.full(len(sddWithoutHTStrongDict[k]), k), sddWithoutHTStrongDict[k], 'b+')


plt.title('Strong Scaling of %sx%s  on 64 cores' % (caseSize[0], caseSize[1]))
plt.xlabel('Core(s)')
plt.ylabel('(Scaled) Loop Time x resource')
plt.legend()

plt.show()
