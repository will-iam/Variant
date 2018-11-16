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
ratioThreadsCores = [1.0]
SDSratioList = [1.0] #[1.0, 4.0]
SDScommonDivider = [0.0]
SDDSizeList = range(minSdd, maxSdd)
engineOptionDict['precision'] = 'float'
#engineOptionDict['compiler'] = 'intel'

#xSizeList = [512]
#xSizeList = [1024]
#xSizeList = [64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]
#xSizeList = [131072, 262144, 524288, 1048576, 2097152, 4194304, 6291456, 8388608]
#sizeList = [(64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)]
#sizeList = [(64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024), (2048, 2048), (4096, 4096), (8192, 8192)]
#sizeList = [(64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024), (2048, 2048)]
#sizeList = [(1024, 1024), (2048, 2048), (4096, 4096), (8192, 8192)]
#sizeList = [(4096, 4096), (8192, 8192)]
#sizeList = [(64, 64), (128, 128), (256, 256)]
#sizeList = [(512, 512), (1024, 1024), (2048, 2048)]
#sizeList = [(64, 1), (128, 1), (256, 1), (512, 1), (1024, 1), (2048, 1), (4096, 1), (8192, 1), (16384, 1)]
#sizeList = [(32768, 1), (65536, 1), (131072, 1)]
#sizeList = [(512, 1), (1024, 1), (2048, 1), (4096, 1), (8192, 1), (16384, 1), (32768, 1)]
#sizeList = [(65536, 1), (131072, 1), (262144, 1)]
sizeList = [(1048576, 1)]
#sizeList = [(1048576, 1), (2097152, 1), (4194304, 1)]
#sizeList = [(6291456, 1)]

testBattery = dict()
for size in sizeList:
    xSize = size[0]
    ySize = size[1]

    cn = "%s%sx%s" % (case_name, str(xSize), str(ySize)) 

    test = dict()

    if case_name == 'nSod':
        test['solver'] = 'sod'
    if case_name == 'nSedov':
        test['solver'] = 'sedov'

#    for p in range(minSdd, maxSdd):
    for p in range(maxSdd - 1, maxSdd):
        for SDSratio in SDSratioList:
            nSDD_X = 2**(p)
            test['nSDD'] = (nSDD_X, 1)
            nSDD = test['nSDD'][0] * test['nSDD'][1]
            test['nCoresPerSDD'] = float(nTotalCores / nSDD)
            test['nThreads'] = np.max([1, int(test['nCoresPerSDD'] * ratioThreadsCores[0])])
            test['nSDS'] = int(test['nThreads'] * SDSratio)
            test['nCommonSDS'] = int(test['nSDS'] * SDScommonDivider[0])
            if test['nSDS'] > (xSize * ySize / nSDD):
                raise ValueError("Not enough cell in your case: %s > %s" % (test['nSDS'], xSize * ySize / nSDD))
            testBattery.setdefault(cn, list()).append(copy.copy(test))

battery = compileTestBattery([testBattery], SDSgeom, nruns)
runTestBattery(engineOptionDict, battery)
