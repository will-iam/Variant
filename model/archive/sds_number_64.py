#!/usr/bin/python
# -*- coding:utf-8 -*-

import parser
import sys
import matplotlib.pyplot as plt
import numpy as np
from collections import *

# Get all data
#caseKey = '128x128x556:64'
caseKey = '512x512x2252:64'
data = parser.getData(caseKey)

ht_sds_time = {}
for item in data.items():
    keyDict = parser.extractKey(item[0])
    R = keyDict['R']
    if R != 64:
        continue

    Nt = keyDict['Nt']


    if Nt not in ht_sds_time.keys():
        ht_sds_time[Nt] = {}

    Ns = keyDict['Ns']
    if Ns not in ht_sds_time[Nt].keys():
        ht_sds_time[Nt][Ns] = []

    for run in item[1]:
        t = run['loopTime']
        ht_sds_time[Nt][Ns].append(t)
        print 'ressource: %s, nThreads: %s, nSDS: %s, loopTime: %s' % (keyDict['R'], Nt, Ns, t)

#sys.exit(1)

fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
#ax.set_xscale('log', basex=2)
#ax.set_yscale('log')

for Nt, sds_time in ht_sds_time.items():
    ordered_sds_time = OrderedDict([(k, np.mean(sds_time[k])) for k in sorted(sds_time)])
    minTime = np.min(ordered_sds_time.values())
    maxTime = np.max(ordered_sds_time.values())
    print "Nt: %s, minTime: %s, maxTime: %s, ratio: %s" % (Nt, minTime, maxTime, maxTime / minTime)
    ax.plot(ordered_sds_time.keys(), ordered_sds_time.values(), label="%s thread(s) per core" % Nt)
    ax.boxplot(sds_time.values(), positions=sds_time.keys())

plt.title(caseKey + ' on 64 cores')
plt.xlabel('SDS number per thread')
plt.ylabel('Time')
plt.legend()
plt.show()

sys.exit(1)




