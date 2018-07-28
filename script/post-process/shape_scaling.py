#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
Plot to compare different shape of the SDD split: (X, Y) with a single thread and a single core in each.
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

for resource in range(0, 7):
    filterDict = {'nSizeX' : caseSize[0], 'nSizeY' : caseSize[1], 'R' : 2**resource}
    data = parser.getData(filterDict)
    if len(data):
        sizeDataDict.append(data)

if len(sizeDataDict) == 0:
    print("No data found.")
    sys.exit(1)

sddStrongDict = {}
sddWithoutHTStrongDict = {}

scatterWithoutHT = []

for data in sizeDataDict:
    for key, value in data.items():
        keyDict = parser.extractKey(key)

        R = keyDict['R']
        Nt = keyDict['Nt']

        for run in value:
            if run['sdsGeom'] != 'line':
                continue
            nSDD = run['point'][0] * run['point'][1]
            t = run['loopTime'] * keyDict['Ny'] * keyDict['Nx'] * R
            if nSDD == R:
                if Nt == 1.0:
                    if R not in sddWithoutHTStrongDict.keys():
                        sddWithoutHTStrongDict[R] = list()
                    sddWithoutHTStrongDict[R].append(t)
                    scatterWithoutHT.append((run['point'][0], run['point'][1], t))

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
#ax.plot(sorted(sddStrongDict), [firstValueSDD / k for k in sorted(sddStrongDict.keys())], 'b--', label="SDD ideal")
#ax.plot(sorted(sddStrongDict), [np.min(v) / k for k, v in sorted(sddStrongDict.items())], 'bo-', label="SDD scaling")

ax.plot(sorted(sddWithoutHTStrongDict), [np.min(v) / k for k, v in sorted(sddWithoutHTStrongDict.items())], 'b-', label="best SDD scaling w/o HT")
ax.plot(sorted(sddWithoutHTStrongDict), [np.max(v) / k for k, v in sorted(sddWithoutHTStrongDict.items())], 'r-', label="worst SDD scaling w/o HT")


parser.outputCurve("plot/shape_scaling_looptime_min-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sddWithoutHTStrongDict), [np.min(v) / k for k, v in sorted(sddWithoutHTStrongDict.items())])
parser.outputCurve("plot/shape_scaling_looptime_max-%sx%s.dat" % (caseSize[0], caseSize[1]), sorted(sddWithoutHTStrongDict), [np.max(v) / k for k, v in sorted(sddWithoutHTStrongDict.items())])

# Transform into np array.
data = np.array(scatterWithoutHT)
labels = ['(%s x %s)' % (int(p[0]), int(p[1])) for p in data]
ax.scatter(data[:, 0] * data[:, 1], data[:, 2] / (data[:, 0] * data[:, 1]), marker='D', c='b', cmap=plt.get_cmap('Spectral'))

output_min = []
output_max = []
for label, x, y, in zip(labels, data[:, 0] * data[:, 1], data[:, 2] / (data[:, 0] * data[:, 1])):
    if y <= np.min(sddWithoutHTStrongDict[x]) / x:
        output_min.append((x, y, label))
        plt.annotate(label, xy=(x,y)
            ,xytext=(-20, -20)
            ,textcoords='offset pixels'
            ,ha='right'
            ,va='bottom'
            ,bbox=dict(boxstyle='round, pad=0.5', fc='green', alpha=0.5)
            ,arrowprops=dict(arrowstyle = 'wedge', connectionstyle='arc3,rad=0')
            )

    if y >= np.max(sddWithoutHTStrongDict[x]) / x:
        output_max.append((x, y, label))
        plt.annotate(label, xy=(x,y)
            ,xytext=(30, 20)
            ,textcoords='offset points'
            ,ha='right'
            ,va='bottom'
            ,bbox=dict(boxstyle='round, pad=0.5', fc='red', alpha=0.5)
            ,arrowprops=dict(arrowstyle = 'wedge', connectionstyle='arc3,rad=0')
            )



with open("plot/shape_scaling_looptime_label_min-%sx%s.dat" % (caseSize[0], caseSize[1]), 'w+') as f:
    for p in output_min:
        f.write(str(p[0]) + "\t" + "{:16.16g}".format(p[1]) + "\t" + p[2].replace(" ", "") + "\n")

with open("plot/shape_scaling_looptime_label_max-%sx%s.dat" % (caseSize[0], caseSize[1]), 'w+') as f:
    for p in output_max:
        f.write(str(p[0]) + "\t" + "{:16.16g}".format(p[1]) + "\t" + p[2].replace(" ", "") + "\n")


plt.title('Shape Scaling of %sx%s' % (caseSize[0], caseSize[1]))
plt.xlabel('Core(s)')
plt.ylabel('(Log scaled) Loop Time')
plt.legend()
plt.show()


