#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import __future__
import sys
import itertools
from seek_common import *


nruns = 1
SDSgeom = 'line'
ratioThreadsCores = [1.0]
SDSratioList = [1.0] #[1.0, 4.0]
SDScommonDivider = [0.0]
SDDSizeList = range(minSdd, maxSdd)
engineOptionDict['compiler'] = 'gnu'

roundingList = ['nearest', 'toward_zero', 'upward', 'downward']
roundingList = ['nearest']
precisionList = [
            #'weak8', 'weak9', 'weak10', // failed on nSod64x1
            #'weak11', // failed on nSod256x1
            #'weak12', // failed on nSod512x1
            #'weak13', // failed on nSod2048
            #'weak14', // failed on nSod4096
            #'weak15', // failed on nSod16384
            #'weak16', // failed on nSod32768
            #'weak17',
            #'weak18', 'weak19',
            'weak20', 'weak21', 'weak22', 'weak23', 'weak24', 'weak25',
            'weak26', 'weak27', 'weak28', 'weak29', 'weak30', 'weak31',
            'weak32', 'float', 'double', 'long_double', 'quad'
            ]

precisionList=['double']

#sizeList = [(64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)]
#sizeList = [(256, 256), (512, 512), (1024, 1024), (2048, 2048), (4096, 4096), (8192, 8192)]
#sizeList = [(64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024), (2048, 2048)]
#sizeList = [(1024, 1024), (2048, 2048), (4096, 4096), (8192, 8192)]
#sizeList = [(4096, 4096), (8192, 8192)]
#sizeList = [(64, 64), (128, 128), (256, 256)]
#sizeList = [(1, 64)]
sizeList = [(1,4096), (64,1), (128,1), (256,1), (512,1), (1024,1), (2048,1), (4096,1), (8192,1), (16384, 1), (32768, 1), (65536, 1), (131072, 1)]
sizeList = [(512, 1)]
#sizeList = [(4096,1), (8192,1), (16384, 1), (32768, 1)]
#sizeList = [(128,128)]
#sizeList = [(1024,1024)]
#sizeList = [(256, 1)]
#sizeList = [(16384, 1)]
#sizeList = [(4096, 1)]
#sizeList = [(512, 512), (1024, 1024)]
#sizeList = [(64, 1), (128, 1), (256, 1), (512, 1), (1024, 1), (2048, 1), (4096, 1)]
#sizeList = [(64, 1), (128, 1), (256, 1), (512, 1), (1024, 1), (2048, 1), (4096, 1), (8192, 1), (16384, 1)]
#sizeList = [(65536, 1), (131072, 1)]
#sizeList = [(512, 1), (1024, 1), (2048, 1), (4096, 1), (8192, 1), (16384, 1), (32768, 1)]
#sizeList = [(65536, 1), (131072, 1), (262144, 1)]
#sizeList = [(4096, 1)]
#sizeList = [(1048576, 1), (2097152, 1), (4194304, 1)]
#sizeList = [(6291456, 1)]

testBattery = dict()
for precision in reversed(precisionList):
    test = dict()
    test['precision'] = precision
    for rounding in roundingList:
        test['rounding'] = rounding
        for size in sizeList:
            xSize = size[0]
            ySize = size[1]
            cn = "%s%sx%s" % (case_name, str(xSize), str(ySize))

            if case_name == 'nSod':
                test['solver'] = 'sod'
            if case_name == 'nSedov':
                test['solver'] = 'sedov'
            if case_name == 'nNoh':
                test['solver'] = 'noh'

        #    for p in range(minSdd, maxSdd):
        #    for p in range(maxSdd - 1, maxSdd):
            for p in range(minSdd - 1, minSdd):
        #    for p in range(minSdd, minSdd + 1):
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
