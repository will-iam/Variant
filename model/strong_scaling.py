#!/usr/bin/python
# -*- coding:utf-8 -*-

import parser
import sys
import matplotlib.pyplot as plt
import numpy as np
import operator
from collections import *

# make point
caseSize = (2048, 2048)
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

        R = keyDict['R']
        Nt = keyDict['Nt']

        for run in value:
            nSDD = run['point'][0] * run['point'][1]
            t = run['loopTime'] * keyDict['Ny'] * keyDict['Nx'] * R
            if nSDD == 1:
                if R not in sdsStrongDict.keys():
                    sdsStrongDict[R] = list()
                sdsStrongDict[R].append(t)
                print 'SDS ressource: %s, loopTime: %s, Nt: %s, %sx%s' % (R, t, Nt, keyDict['Ny'], keyDict['Nx'])
            if nSDD == R and Nt == 1.0:
                if R not in sddStrongDict.keys():
                    sddStrongDict[R] = list()
                sddStrongDict[R].append(t)
                #print 'SDD ressource: %s, loopTime: %s' % (R, t)


# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
#ax = fig.add_subplot(111)
ax = fig.add_subplot(211)
ax.set_xscale('log', basex=2)
ax.set_yscale('log')

firstValueSDD = [np.min(v) for k, v in sorted(sddStrongDict.items())][0]
firstValueSDS = [np.min(v) for k, v in sorted(sdsStrongDict.items())][0]

ax.plot(sorted(sdsStrongDict), [np.min(v) / k for k, v in sorted(sdsStrongDict.items(), key=operator.itemgetter(0))], 'g+-', label="SDS scaling")
ax.plot(sorted(sddStrongDict), [np.min(v) / k for k, v in sorted(sddStrongDict.items())], 'b+-', label="SDD scaling w/o HT")
ax.plot(sorted(sdsStrongDict), [firstValueSDS / k for k in sorted(sdsStrongDict.keys())], 'g--', label="SDS ideal")
ax.plot(sorted(sddStrongDict), [firstValueSDD / k for k in sorted(sddStrongDict.keys())], 'b--', label="SDD ideal")

for k in sdsStrongDict:
    ax.plot(np.full(len(sdsStrongDict[k]), k), [i / k for i in sdsStrongDict[k]], 'g+')
for k in sddStrongDict:
    ax.plot(np.full(len(sddStrongDict[k]), k), [i / k for i in sddStrongDict[k]], 'b+')


plt.title('Strong Scaling of %sx%s on 64 cores' % (caseSize[0], caseSize[1]))
plt.xlabel('Core(s)')
plt.ylabel('(Log scaled) Loop Time / cell')
plt.legend()

bx = fig.add_subplot(212)
bx.set_xscale('log', basex=2)
bx.plot(sorted(sdsStrongDict), [np.min(v) for k, v in sorted(sdsStrongDict.items(), key=operator.itemgetter(0))], 'g+-', label="SDS scaling")
bx.plot(sorted(sddStrongDict), [np.min(v) for k, v in sorted(sddStrongDict.items())], 'b+-', label="SDD scaling w/o HT")
bx.plot(sorted(sdsStrongDict), [firstValueSDS for k in sorted(sdsStrongDict.keys())], 'g--', label="SDS ideal")
bx.plot(sorted(sddStrongDict), [firstValueSDD for k in sorted(sddStrongDict.keys())], 'b--', label="SDD ideal")

for k in sdsStrongDict:
    bx.plot(np.full(len(sdsStrongDict[k]), k), sdsStrongDict[k], 'g+')
for k in sddStrongDict:
    bx.plot(np.full(len(sddStrongDict[k]), k), sddStrongDict[k], 'b+')


plt.title('Strong Scaling of %sx%s  on 64 cores' % (caseSize[0], caseSize[1]))
plt.xlabel('Core(s)')
plt.ylabel('(Scaled) Loop Time x resource / cell')
plt.legend()

plt.show()


