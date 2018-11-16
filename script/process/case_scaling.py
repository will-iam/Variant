#!/usr/bin/python3
# -*- coding:utf-8 -*-

import __future__
import parser
import sys
import matplotlib.pyplot as plt
#plt.style.use('ggplot')
import numpy as np
import operator
from collections import *

resource = 64
initSize = 128
maxPower = 14
minCase = (initSize * 2**maxPower, initSize * 2**maxPower)
maxCase = (0, 0)

if parser.args.res:
    resource = parser.args.res

# make point List
sizeList = []
caseSizeX = initSize / 2
caseSizeY = initSize
sizeDataDict = []
for p in range(0, maxPower):
	# Defining case directory
    if p % 2 == 1:
        caseSizeY = caseSizeY * 2
    else:
        caseSizeX = caseSizeX * 2
    filterDict = {'nSizeX' : caseSizeX, 'nSizeY' : caseSizeY, 'R' : resource}
    print filterDict
    data = parser.getData(filterDict)
    if len(data):
        sizeDataDict.append(data)


if len(sizeDataDict) == 0:
    print("No data found.")
    sys.exit(1)

sdsCaseWithoutHTDict = dict()
sdsCaseDict = dict()
sddCaseDict = dict()
sddHTCaseDict = dict()
hybridCaseDict = dict()
normalizeDict = dict()
for data in sizeDataDict:
    for key, value in data.items():
        keyDict = parser.extractKey(key)

        #if float(keyDict['Nt']) < 1.5:
        #    continue

        if keyDict['R'] != resource:
            print("I ask for a specific amount of ressources(%s), what happened?" % resource)
            sys.exit(1)

        nx = int(keyDict['Nx'])
        ny = int(keyDict['Ny'])
        nt = int(keyDict['Nt'])

#        if nx * ny < 512*512:
#            continue

        if maxCase[0] < nx or  maxCase[1] < ny:
            maxCase = (nx, ny)

        if minCase[0] > nx or  minCase[1] > ny:
            minCase = (nx, ny)

        caseNormalizer = nx * ny
        normalizeDict[caseNormalizer] = caseNormalizer
        Nt = keyDict['Nt']
        for run in value:
            nSDD = run['point'][0] * run['point'][1]
            t = run['loopTime']
            if nSDD == 1:
                if Nt == 1.0:
                    sdsCaseWithoutHTDict.setdefault(caseNormalizer, list()).append(t)
                if caseNormalizer not in sdsCaseDict.keys():
                    sdsCaseDict[caseNormalizer] = list()
                sdsCaseDict[caseNormalizer].append(t)
                #print 'SDS ressource: %s, loopTime: %s' % (R, t)

            if nSDD == resource and nt == 1.0:
                if caseNormalizer not in sddCaseDict.keys():
                    sddCaseDict[caseNormalizer] = list()
                sddCaseDict[caseNormalizer].append(t)
                #print 'SDD ressource: %s, loopTime: %s' % (R, t)

            if nSDD > resource:
                if caseNormalizer not in sddHTCaseDict.keys():
                    sddHTCaseDict[caseNormalizer] = list()
                sddHTCaseDict[caseNormalizer].append(t)
                print 'SDD %s, ressource: %s, loopTime: %s, Nt: %s, (%sx%s)' % (nSDD, resource, t, nt, run['point'][0], run['point'][1])

            if nSDD != resource and nSDD != 1:
                if caseNormalizer not in hybridCaseDict.keys():
                    hybridCaseDict[caseNormalizer] = list()
                hybridCaseDict[caseNormalizer].append(t)
                #print 'SDD ressource: %s, loopTime: %s' % (R, t)


if normalizeDict == dict():
    print("No data found.")
    sys.exit(1)

# And now, we must plot that
fig = plt.figure(0, figsize=(9, 6))
lastValueSDSwithoutHT = [np.min(v) for k, v in sorted(sdsCaseWithoutHTDict.items())][-1]
lastValueSDS = [np.min(v) for k, v in sorted(sdsCaseDict.items())][-1]
lastValueSDD = [np.min(v) for k, v in sorted(sddCaseDict.items())][-1]


#bx = fig.add_subplot(212)
bx = fig.add_subplot(111)
bx.set_xscale('log', basex=2)
bx.set_yscale('log')
bx.plot(sorted(sdsCaseWithoutHTDict), [np.min(v) for k, v in sorted(sdsCaseWithoutHTDict.items(), key=operator.itemgetter(0))], 'g+-', label="SDS scaling w/o HT")
bx.plot(sorted(sdsCaseDict), [np.min(v) for k, v in sorted(sdsCaseDict.items(), key=operator.itemgetter(0))], 'go-', label="SDS scaling")
bx.plot(sorted(sddCaseDict), [np.min(v) for k, v in sorted(sddCaseDict.items())], 'b+-', label="SDD scaling")
#bx.plot(sorted(sddHTCaseDict), [np.min(v) for k, v in sorted(sddHTCaseDict.items())], 'ro-', label="SDD scaling w/ SDD HT")
bx.plot(sorted(hybridCaseDict), [np.min(v) for k, v in sorted(hybridCaseDict.items())], 'y+-', label="Hybrid scaling")

bx.plot(sorted(sdsCaseWithoutHTDict), [lastValueSDSwithoutHT for k in sorted(sdsCaseWithoutHTDict.keys())], 'g--', label="SDS w/o HT ideal")
bx.plot(sorted(sdsCaseDict), [lastValueSDS for k in sorted(sdsCaseDict.keys())], 'g--', label="SDS ideal")
bx.plot(sorted(sddCaseDict), [lastValueSDD for k in sorted(sddCaseDict.keys())], 'b--', label="SDD ideal")

for k in sdsCaseDict:
    bx.plot(np.ones(len(sdsCaseDict[k])) * k, [i for i in sdsCaseDict[k]], 'g+')
for k in sddCaseDict:
    bx.plot(np.ones(len(sddCaseDict[k])) * k, [i for i in sddCaseDict[k]], 'b+')

#for k in sddHTCaseDict:
#    bx.plot(np.ones(len(sddHTCaseDict[k])) * k, [i for i in sddHTCaseDict[k]], 'r+')

plt.title('Case Scaling from %sx%s to %sx%s with %s core(s)' % (minCase[0], minCase[1], maxCase[0], maxCase[1], resource))
plt.xlabel('Cell Number')
plt.ylabel('Loop Time / (cell x iteration)')
plt.legend()


parser.outputCurve("plot/case_scaling_sds_HT-%s.dat" % initSize, sorted(sdsCaseDict), [np.min(v) for k, v in sorted(sdsCaseDict.items(), key=operator.itemgetter(0))])
parser.outputCurve("plot/case_scaling_sds_wo_HT-%s.dat" % initSize, sorted(sdsCaseWithoutHTDict), [np.min(v) for k, v in sorted(sdsCaseWithoutHTDict.items(), key=operator.itemgetter(0))])
parser.outputCurve("plot/case_scaling_sdd_wo_HT-%s.dat" % initSize, sorted(sddCaseDict), [np.min(v) for k, v in sorted(sddCaseDict.items(), key=operator.itemgetter(0))])
parser.outputCurve("plot/case_scaling_hybrid-%s.dat" % initSize, sorted(hybridCaseDict), [np.min(v) for k, v in sorted(hybridCaseDict.items(), key=operator.itemgetter(0))])

parser.outputCurve("plot/case_scaling_sds_ideal_wo_HT-%s.dat" % initSize, sorted(sdsCaseWithoutHTDict), [lastValueSDSwithoutHT for k in sorted(sdsCaseWithoutHTDict.keys())])
parser.outputCurve("plot/case_scaling_sds_ideal-%s.dat" % initSize, sorted(sdsCaseDict), [lastValueSDS for k in sorted(sdsCaseDict.keys())])
parser.outputCurve("plot/case_scaling_sdd_ideal-%s.dat" % initSize, sorted(sddCaseDict), [lastValueSDD for k in sorted(sddCaseDict.keys())])

parser.outputPoint("plot/case_scaling_sds_HT_dot-%s.dat" % initSize, sdsCaseDict)
parser.outputPoint("plot/case_scaling_sdd_HT_dot-%s.dat" % initSize, sddCaseDict)



plt.show()
