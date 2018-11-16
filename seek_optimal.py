##!/usr/bin/python3
# -*- coding:utf-8 -*-

import __future__
import sys
import itertools
from decimal import *
from seek_common import *
import script.compiler as compiler


testList = list()

nruns = 1
SDSgeom = 'line'
ratioThreadsCores = [1.00]
SDSratioList = [4.0]
SDScommonDivider = [0.0]
SDDSizeList = range(minSdd, maxSdd)

caseSize = (2048, 2048)
if nTotalCores == 128:
    caseSize = (4096, 4096)
if nTotalCores == 256:
    caseSize = (8192, 8192)
if nTotalCores == 512:
    caseSize = (16384, 16384)

#if args.jobname == "Variant-Job-XYZ6":
    #Special argument depending on the job.

#testList.append(explore((256, 256), ratioThreadsCores, SDDSizeList, SDSratioList, SDScommonDivider))
#testList.append(weakSDD(128, ratioThreadsCores, SDSratioList))
#testList.append(weakSDS(128, ratioThreadsCores, SDSratioList, SDScommonDivider))
testList.append(strongSDD((256, 256), ratioThreadsCores, SDDSizeList, SDSratioList))
#testList.append(strongSDS((128, 128), ratioThreadsCores, SDSratioList, SDScommonDivider))
#testList.append(exploreCaseSize(512, ratioThreadsCores, SDDSizeList, SDSratioList, SDScommonDivider))

battery = compileTestBattery(testList, SDSgeom, nruns)
runTestBattery(engineOptionDict, battery)
