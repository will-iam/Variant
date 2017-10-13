#!/usr/bin/python
# -*- coding:utf-8 -*-

import parser
import sys
import matplotlib.pyplot as plt
import numpy as np
from pprint import *
from collections import *

# Get all data
caseKey = '128x128'
#caseKey = '256x256'
#caseKey = '512x512'

data = parser.getData(caseKey)

sds_resource_time = {}
refTimeList = []
totalPoint = 0
for item in data.items():
    keyDict = parser.extractKey(item[0])
    Nt = keyDict['Nt']
    
    if Nt != 1:
        continue

    resource = keyDict['R']
    Ns = keyDict['Ns']

    if Ns not in sds_resource_time.keys():
        sds_resource_time[Ns] = {}

    if resource not in sds_resource_time[Ns]:
        sds_resource_time[Ns][resource] = []

    for run in item[1]:
        totalPoint += 1
        t = run['loopTime']
        sds_resource_time[Ns][resource].append(t)
        if resource == 1:
            refTimeList.append(t)        
        #print '[%s] ressource: %s, nThreads: %s, nSDS: %s, loopTime: %s' % (totalPoint, resource, Nt, Ns, t)

# Trie et Moyenne les résultats
sorted_sds_resource_time = OrderedDict()
for sds, resource_time in sorted(sds_resource_time.items()):
    sorted_sds_resource_time[sds] = OrderedDict()
    for res, time in sorted(resource_time.items()):
        sorted_sds_resource_time[sds][res] = np.mean(time)

fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
ax.set_xscale('log', basex=2)
ax.set_yscale('log')
for sds in sorted_sds_resource_time:
    if sds < 16:            
        ax.plot(sorted_sds_resource_time[sds].keys(), sorted_sds_resource_time[sds].values(), label="%s SDS per thread" % sds)
        ax.boxplot(sds_resource_time[sds].values(), positions=sds_resource_time[sds].keys())

# Build reference:
refTime = np.min(refTimeList)
ideal = OrderedDict([(i, refTime/i) for i in range(1, 65)])
ax.plot(ideal.keys(), ideal.values(), 'k--', label="ideal", linewidth=0.5)

plt.title(caseKey + ' SDS strong scalability')
plt.xlabel('Core used')
plt.ylabel('Time')
plt.legend(loc='upper left')
plt.show()



