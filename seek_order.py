##!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
import sys
import itertools
from decimal import *
from seek_common import *
import script.compiler as compiler


nruns = 1
SDSgeom = 'line'
ratioThreadsCores = [2.00]
SDSratioList = [4.0]
SDScommonDivider = [0.0]
SDDSizeList = range(minSdd, maxSdd)
caseSize = (64, 1)

testBattery = dict()
for p in range(9, 12):
    xSize = caseSize[0] * 2**p
    cn = case_name + str(xSize)
    test = dict()
    test['nSDD'] = (maxSdd, 1)
    test['nCoresPerSDD'] = float(nTotalCores) / maxSdd
    test['nThreads'] = np.max([1, int(test['nCoresPerSDD'] * ratioThreadsCores[0])])
    test['nSDS'] = int(test['nThreads'] * SDSratioList[0])
    test['nCommonSDS'] = int(test['nSDS'] * SDScommonDivider[0])
    if test['nSDS'] > caseSize[0] * caseSize[1]:
        raise ValueError("Not enough cell in your case.")
    testBattery[cn] = [copy.copy(test)]

battery = compileTestBattery([testBattery], SDSgeom, nruns)
runTestBattery(engineOptionDict, battery)
