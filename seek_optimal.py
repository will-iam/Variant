##!/usr/bin/python
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
ratioThreadsCores = [3.92]
SDSratioList = [4.]
SDScommonDivider = [0.]
SDDSizeList = range(minSdd, maxSdd)

caseSize = (2048, 2048)
if nTotalCores == 128:
    caseSize = (4096, 4096)
if nTotalCores == 256:
    caseSize = (8192, 8192)
if nTotalCores == 512:
    caseSize = (16384, 16384)


#testList.append(strongSDS((caseSize[0], caseSize[1]), ratioThreadsCores, SDSratioList, SDScommonDivider, 6, 7))
#testList.append(strongSDD((2048, 2048), ratioThreadsCores, [4, 5], SDSratioList))

'''
common
strong SDD SDS
weak SDD SDS
explore((caseSize[0], caseSize[1]), ratioThreadsCores, SDDSizeList, SDSratioList, SDScommonDivider, True)
exploreCaseSize(512)

'''

if args.jobname == "Variant-2Nodes":
    nruns = 1
    ratioThreadsCores = [1.00]
    SDSratioList = [4.0]
    SDScommonDivider = [0.145, 0.155, 0.165]
    SDDSizeList = range(minSdd, maxSdd + 1)
    testList.append(explore((4096, 4096), ratioThreadsCores, SDDSizeList, SDSratioList, SDScommonDivider))

if args.jobname == "Variant-4Nodes":
    nruns = 1
    ratioThreadsCores = [3.91]
    SDSratioList = [4.0]
    SDScommonDivider = [0.0]
    SDDSizeList = range(minSdd, maxSdd + 1)
    testList.append(explore((caseSize[0], caseSize[1]), ratioThreadsCores, SDDSizeList, SDSratioList, SDScommonDivider))
#    ratioThreadsCores = [1.0]
#    SDScommonDivider = [0.10, 0.125, 0.15]
#    SDDSizeList = range(minSdd, maxSdd + 1)
#    testList.append(explore((caseSize[0], caseSize[1]), ratioThreadsCores, SDDSizeList, SDSratioList, SDScommonDivider))

if args.jobname == "Variant-8Nodes":
    testList.append(strongSDD((2048, 2048), ratioThreadsCores, [9], SDSratioList))

if args.jobname == "Variant-16Nodes":
    testList.append(strongSDD((2048, 2048), ratioThreadsCores, [10], SDSratioList))

if args.jobname == "Variant-Thom-0":
    nruns = 1
    ratioThreadsCores = [1.0]
    SDSratioList = [4.0]
    SDScommonDivider = [0.0]
    testList.append(strongSDS((2048, 2048), ratioThreadsCores, SDSratioList, SDScommonDivider))

if args.jobname == "Variant-Thom-1":
    nruns = 1
    ratioThreadsCores = [1.9]
    SDSratioList = [4.0]
    SDScommonDivider = [0.0]
    testList.append(strongSDS((2048, 2048), ratioThreadsCores, SDSratioList, SDScommonDivider))

if args.jobname == "Variant-SKL-0":
    nruns = 1
    ratioThreadsCores = [1.0]
    SDSratioList = [4.0]
    SDScommonDivider = [0.0]
    testList.append(strongSDS((2048, 2048), ratioThreadsCores, SDSratioList, SDScommonDivider))

if args.jobname == "Variant-SKL-1":
    nruns = 1
    ratioThreadsCores = [1.9]
    SDSratioList = [4.0]
    SDScommonDivider = [0.0]
    testList.append(strongSDS((2048, 2048), ratioThreadsCores, SDSratioList, SDScommonDivider))

if args.jobname == "Variant-Yoccoz-0":
    nruns = 1
    ratioThreadsCores = [3.91]
    SDSratioList = [4.0]
    SDScommonDivider = [0.0]
    testList.append(strongSDS((2048, 2048), ratioThreadsCores, SDSratioList, SDScommonDivider))
    #testList.append(strongSDD((4096, 2048), ratioThreadsCores, [0], SDSratioList))

if args.jobname == "Variant-Yoccoz-1":
    nruns = 1
    ratioThreadsCores = [3.91]
    SDSratioList = [4.0]
    SDScommonDivider = [0.10]
    testList.append(strongSDS((2048, 2048), ratioThreadsCores, SDSratioList, SDScommonDivider))

if args.jobname == "Variant-Thom-3":
    nruns = 4
    ratioThreadsCores = [1.0]
    SDSratioList = [2.5, 3.5, 4.5, 5.5]
    SDScommonDivider = [0.0]
    testList.append(strongSDS((4096, 4096), ratioThreadsCores, SDSratioList, SDScommonDivider))

if args.jobname == "Variant-Thom-4":
    nruns = 5
    ratioThreadsCores = [1.0]
    SDSratioList = [4.0]
    SDScommonDivider = [0.125]
    testList.append(strongSDS((4096, 4096), ratioThreadsCores, SDSratioList, SDScommonDivider))

if args.jobname == "Variant-Thom-5":
    nruns = 6
    ratioThreadsCores = [1.0]
    SDSratioList = [4.0]
    SDScommonDivider = [0.125]
    testList.append(strongSDS((4096, 4096), ratioThreadsCores, SDSratioList, SDScommonDivider))

if args.jobname == "Variant-Thom-6":
    nruns = 1
    ratioThreadsCores = [1.00]
    SDSratioList = [4.0]
    SDScommonDivider = [0.145, 0.155, 0.165]
    SDDSizeList = range(minSdd, maxSdd)
    #testList.append(exploreCaseSize(512, ratioThreadsCores, SDDSizeList, SDSratioList, SDScommonDivider))
    #testList.append(explore((512, 1024), ratioThreadsCores, SDDSizeList, SDSratioList, SDScommonDivider))
    #testList.append(explore((1024, 1024), ratioThreadsCores, SDDSizeList, SDSratioList, SDScommonDivider))
    #testList.append(explore((4096, 4096), ratioThreadsCores, SDDSizeList, SDSratioList, SDScommonDivider))
    #testList.append(strongSDS((4096, 4096), ratioThreadsCores, SDSratioList, SDScommonDivider))
    testList.append(strongSDD((4096, 4096), ratioThreadsCores, SDDSizeList, SDSratioList))

if args.jobname == "Variant-Thom-7":
    nruns = 1
    ratioThreadsCores = [1.0]
    SDSratioList = [4.0]
    SDScommonDivider = [0.14, 0.15, 0.16]
    SDDSizeList = range(minSdd, maxSdd)
    #testList.append(explore((512, 512), ratioThreadsCores, SDDSizeList, SDSratioList, SDScommonDivider))
    testList.append(strongSDS((4096, 4096), ratioThreadsCores, SDSratioList, SDScommonDivider, [8, 16, 32]))



battery = compileTestBattery(testList, SDSgeom, nruns)
runTestBattery(engineOptionDict, battery)
