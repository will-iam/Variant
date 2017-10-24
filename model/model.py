#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import sys
from collections import *
import parser
from pprint import *
from scipy import stats
#from pandas import Series
import numpy as np
from numpy.linalg import inv, pinv
import matplotlib.pyplot as plt
import operator

# Calcule le nombre de voisins d'un domaine
def computeNeighborNumber(x, y, withCorner = False):
    if x == 1 and y == 1:
        return 0

    total = 0.0
    if x == 1: # then y > 1
        total += (y - 2) * 2 # border without corners
        total += 2 # corners
        return total

    if y == 1: # then x > 1
        total += (x-2) * 2 # border without corners
        total += 2 # corners
        return total

    # Now we know that x > 1 and y > 1
    if withCorner == True:
        a = 8
        b = 5
        c = 3
    else:
        a = 4
        b = 3
        c = 2

    total += (x-2) * (y-2) * a # internal sub-domains
    total += 2 * (x-2) * b # x borders without corners
    total += 2 * (y-2) * b # y borders without corners
    total += 4 * c # corners

    # return total
    return total



def expectation(data, field, filterKey):
    '''
    Dans cette première étape on récupère les données produites sur un seul coeur pour estimer le
    temps de calcul Tc.
    '''
    caseKeyList = [k for k in data.keys() if k.endswith(filterKey)]
    if len(caseKeyList) > 1:
        print("Weird ...")
        sys.exit(1)

    TcData = data[caseKeyList[0]]

    if not len(TcData):
        print("Aucune données sur le cas %s" % caseKey)
        sys.exit(1)
    #pprint(TcData)

    pointTimeDict = {}
    for element in TcData:
        coord = element['point']
        a = np.log(element[field])
        if coord not in pointTimeDict.keys():
            pointTimeDict[coord] = []
        pointTimeDict[coord].append(a)

    pointExpectDict = {}
    for point, TcLoopTimeList in pointTimeDict.items():
        sample = np.array(TcLoopTimeList)
        meanTc, stdTc = stats.norm.fit(TcLoopTimeList)
        pointExpectDict[(point[0], point[1], point[2], len(TcLoopTimeList))] = np.exp(meanTc)
    return pointExpectDict

def synchronizeEstimate(data, resource):

    rawTsData = {}
    for k, v in data.items():
        if  k.endswith(str(resource) + ':1:4'):
            for p in v:
                coord = p['point']
                if coord not in rawTsData.keys():
                    rawTsData[coord] = []
                t = p['maxIterationSum'] - p['maxComputeSum']
                #print p['point'], 100. * p['synchronizeTime'] / (p['loopTime'] - p["computeTime"]), "%%"
                rawTsData[coord].append(np.log(t))

    if not len(rawTsData):
        print("Aucune données sur le cas %s" % rawTsData)
        sys.exit(1)
    #pprint(rawTsData)

    pointExpectDict = {}
    for point, synchronizeTimeList in rawTsData.items():
        meanTs, stdTs = stats.norm.fit(synchronizeTimeList)
        pointExpectDict[(point[0], point[1], point[2], len(synchronizeTimeList))] = np.exp(meanTs)

        '''
        fig = plt.figure(0, figsize=(9, 6))
        ax = fig.add_subplot(111)
        ax.hist(synchronizeTimeList, bins=25, alpha=0.3, normed= True)
        x = np.linspace(meanTs - 2*stdTs, meanTs + 2*stdTs, 100)
        normal_dist = stats.norm(meanTs, stdTs)
        normal_pdf = normal_dist.pdf(x)
        ax.plot(x, normal_pdf, '--', label="%s x %s" % (point[0], point[1]))
        plt.legend()
        plt.show()
        '''

    return pointExpectDict

def chargeEstimate(data, resource):
    '''
    Dans cette première étape on récupère les données produites avec un seul thread et 64 SDD pour estimer le
    temps de calcul Tc.
    '''
    TcKeyFiltered = [k for k in data.keys() if k.endswith(':' + str(resource) + ':1:4')]
    if len(TcKeyFiltered) > 1:
        print("Weird ...")
        sys.exit(1)

    TcData = data[TcKeyFiltered[0]]
    if not len(TcData):
        print("Aucune données sur le cas %s" % TcKeyFiltered[0])
        sys.exit(1)
    #pprint(TcData)

    allTime = []
    timeByPointDict = {}
    machinePointTimeDict = {}
    pointMachineTimeDict = {}
    for element in TcData:
        coord = element['point']
        if coord[0] * coord[1] != resource:
            continue

        point = element['point']
        machine = element['machine']

        if point not in timeByPointDict.keys():
            timeByPointDict[point] = []

        if point not in pointMachineTimeDict.keys():
            pointMachineTimeDict[point] = {}

        if machine not in pointMachineTimeDict[point].keys():
            pointMachineTimeDict[point][machine] = []

        if machine not in machinePointTimeDict.keys():
            machinePointTimeDict[machine] = {}

        if point not in machinePointTimeDict[machine].keys():
            machinePointTimeDict[machine][point] = []

        a = np.log(element["maxComputeSum"])
        allTime.append(a)
        timeByPointDict[point].append(a)
        pointMachineTimeDict[point][machine].append(a)
        machinePointTimeDict[machine][point].append(a)

    expectTimeDict = {}
    for point, pointTimeDict in pointMachineTimeDict.items():
        if point not in expectTimeDict.keys():
            expectTimeDict[point] = {}

        for machine, timeList in pointTimeDict.items():
            sample = np.array(timeList)

            # kstest is the Kolmogrov-Smirnov test for goodness of fit
            # Here its sample is being tested against the normal distribution
            # D is the KS statistic and the closer it is to 0 the better.

            ## Normale
            meanTc, stdTc = stats.norm.fit(timeList)
            expectTimeDict[point][machine] = (meanTc, stdTc, len(timeList))
            ktOut = stats.kstest(sample, 'norm', args=(meanTc, stdTc))
            print('\n\tkstest output for the Normal distribution')
            print('\tD = ' + str(ktOut[0]))
            print('\tP-value = ' + str(ktOut[1]))
            print(machine, point, meanTc, stdTc, len(timeList))

            ## wald : moins bon que lognormal
            ## normal : non
            ## rayleigh : non
            ## nakagami : non
            '''
            ## Lognormal
            shape, location, scale = stats.lognorm.fit(TcLoopTimeList)
            muTc, sigmaTc = np.log(scale), shape
            log_dist = stats.lognorm(s=shape, loc=location, scale=scale)
            print "\tlog_dist.expect()",  log_dist.expect()
            print "\tLoi Lognormale: espérance de Tc = %s, écart-type (sigma) de Tc = %s sur %s points" % (np.exp(-muTc), sigmaTc, len(TcLoopTimeList))
            ktOut = stats.kstest(sample, 'lognorm', args=(shape, location, scale))
            print('\n\tkstest output for the Lognormal distribution')
            print('\tD = ' + str(ktOut[0]))
            print('\tP-value = ' + str(ktOut[1]))

            ## Wald
            wald_location, wald_scale = stats.wald.fit(TcLoopTimeList)
            ktOut = stats.kstest(sample, 'wald', args=(wald_location, wald_scale))
            print('\n\tkstest output for the Wald distribution')
            print('\tD = ' + str(ktOut[0]))
            print('\tP-value = ' + str(ktOut[1]))

            ## RayleighcomputeMeanNeighborhoodNumber
            rayleigh_a, rayleigh_b = stats.rayleigh.fit(TcLoopTimeList)
            #ktOut = stats.kstest(sample, 'rayleigh')
            print('\n\tkstest output for the rayleigh distribution')
            print('\tD = ' + str(ktOut[0]))
            print('\tP-value = ' + str(ktOut[1]))

            ## Normale
            meanTc, stdTc = stats.norm.fit(TcLoopTimeList)
            ktOut = stats.kstest(sample, 'norm', args=(meanTc, stdTc))
            print('\n\tkstest output for the Normal distribution')
            print('\tD = ' + str(ktOut[0]))
            print('\tP-value = ' + str(ktOut[1]))


            # Trace l'histogramme
            fig = plt.figure(0, figsize=(9, 6))
            ax = fig.add_subplot(111)
            ax.hist(sample, bins=25, alpha=0.3, color='k', normed= True)
            x = np.linspace(np.min(sample)*0.996, np.max(sample)*1.004, 500)
            normal_dist = stats.norm(meanTc, stdTc)
            normal_pdf = normal_dist.pdf(x)
            ax.plot(x, normal_pdf, 'k--', label="%s with %s point(s)" % (machine, len(timeList)))
            plt.legend()
            plt.show()
            '''

        '''
        # Trace l'histogramme
        fig = plt.figure(0, figsize=(9, 6))
        ax = fig.add_subplot(111)
        ax.hist(timeByPointDict[point], bins=25, alpha=0.3, normed= True)
        x = np.linspace(np.min(timeByPointDict[point])*0.996, np.max(timeByPointDict[point])*1.004, 500)
        for machine, normal in expectTimeDict[point].items():
            normal_dist = stats.norm(normal[0], normal[1])
            normal_pdf = normal_dist.pdf(x)
            ax.plot(x, normal_pdf, '--', label="%s with %s point(s)" % (machine, normal[2]))
        plt.legend()
        plt.show()
        '''

    print("\nExpectation by point:")
    allExpectTime = []
    for point, machineExpectDict in expectTimeDict.items():
        print("Expectation(s) on point", point)
        for machine, normal in machineExpectDict.items():
            t = np.exp(normal[0])
            allExpectTime.append(t)
            print("\t%s %s" % (machine, t))
        print("\tmean of expectation(s) = %s" % (np.mean([np.exp(v[0]) for v in machineExpectDict.values()])))

    mean = np.mean(allExpectTime)
    print("Mean of all expectation values: ", mean)

    '''
    # Normal of all points.
    sample = np.array(allTime)
    meanTc, stdTc = stats.norm.fit(sample)
    fig = plt.figure(0, figsize=(9, 6))
    ax = fig.add_subplot(111)
    ax.hist(sample, bins=100, alpha=0.3, normed= True)
    x = np.linspace(meanTc - 2*stdTc, meanTc + 2*stdTc, 500)
    normal_dist = stats.norm(meanTc, stdTc)
    normal_pdf = normal_dist.pdf(x)
    ax.plot(x, normal_pdf, 'r--', label="full sample %s point(s)" % (len(allTime)))
    plt.legend()
    plt.show()
    print "Expectations of points all together:", np.exp(meanTc)
    '''
    return np.exp(meanTc) * resource


def greeksEstimate(data, resource):
    '''
    delta = débit de la communication.
    lambda = latence pour ouvrir une communication.
    '''

    TsData = []
    for k, v in data.items():
        if not k.endswith(':' + str(resource) + ':1:4'):
            continue

        for p in v:

            coord = p['point']
            if coord[0] * coord[1] * coord[2] != resource:
                print("Erreur dans la récupération des données")
                sys.exit(1)

            if coord[0] == 1 and coord[1] == 1:
                continue

            #if coord[0] != coord[1]:
            #  continue

            #caseSize = int(np.sqrt(p['nPhysicalCells'] * coord[0] * coord[1]))
            #if caseSize > 700:
            #    continue
            extractedKey = parser.extractKey(k)
            p['Nx'] = extractedKey['Nx']
            p['Ny'] = extractedKey['Ny']

            TsData.append(p)


    # Estimation des paramètres du modèle
    TsList = []
    coupleList = []
    interfaceSizeDict = {}
    neighbourhoodDict = {}
    for p in TsData:
        ts = np.log(p['maxIterationSum'] - p['maxComputeSum'])
        #ts = p['loopTime'] - p['computeTime']

        coord = p['point']
        nx = float(coord[0])
        ny = float(coord[1])
        Nx = p['Nx']
        Ny = p['Ny']

        h =  parser.fn(nx) * ny + parser.fn(ny) * nx
        i =  h * (Nx + Ny)

        coupleList.append([1.0, np.log(h), np.log(i)])
        TsList.append(ts)

        if h not in interfaceSizeDict.keys():
            interfaceSizeDict[h] = {}
        if i not in interfaceSizeDict[h].keys():
            interfaceSizeDict[h][i] = []
        interfaceSizeDict[h][i].append(ts)

        if i not in neighbourhoodDict.keys():
            neighbourhoodDict[i] = {}
        if h not in neighbourhoodDict[i].keys():
            neighbourhoodDict[i][h] = []
        neighbourhoodDict[i][h].append(ts)

    Ts = np.array(TsList)
    F = np.array(coupleList)
    B = np.dot(pinv(F), Ts)

    print(len(Ts), " simulations. Valeur de B:", B)
    TsEstimate = np.dot(F, B)
    err = np.sqrt(np.sum(np.dot((Ts - TsEstimate), (Ts - TsEstimate)))) / len(Ts)
    print("Erreur entre le modèle bruité non calibré et le modèle calibré: ", err)


    # i =  h * caseSize, j =  h * np.log(caseSize) : err = 0.00505024734782
    # i =  h * np.log(caseSize) : err = 0.005053122627
    # i =  h * np.sqrt(caseSize) : err = 0.00505726721335
    # i =  h * caseSize         : err = 0.00505726721335

    # Best = [-2.11062418  1.41218773 -1.39434254]
    '''
    # Estimation du bruit sur les temps de synchronisation ?


    Pf = np.dot(np.dot(F, inv(F.T.dot(F))), F.T)

    index = 0
    varYDict = {}
    for c in coupleList:
        varY = Pf[index][index]
        h = c[0]
        i = c[1]/h
        varYDict[i] = {}
        varYDict[i][h] = varY
        index += 1
    # Estimation de l'erreur entre le modèle non calibré bruité et le modèle calibré



    X = []
    Y = []
    err = []
    for i in sorted(neighbourhoodDict):
        for h,v in sorted(neighbourhoodDict[i].items()):
            for y in neighbourhoodDict[i][h]:
                x = h*(lambdaValue + deltaValue*i)
                Y.append(y)
                X.append(x)
                err.append(np.abs(x-y))

    sigma = np.std(err)
    print "err var:", np.var(err),", err std:", sigma
    Pf = Pf * sigma * sigma
    '''


    ### fig ###
    fig = plt.figure(0, figsize=(9, 6))

    boxDist = {}


    # Trace la courbe en fonction de i
    ax = fig.add_subplot(111)
    #ax = fig.add_subplot(211)
    xMin = np.min(neighbourhoodDict.keys())
    xMax = np.max(neighbourhoodDict.keys())
    #ax.set_xscale('log')
    #ax.set_yscale('log')
    x = np.linspace(xMin, xMax, 60)
    for h in sorted(interfaceSizeDict):
        #if h != 224 and h != 48 and h != 8 and h != 2:
        #    continue

        #if h < 8:
        #    continue

        for k, vL in interfaceSizeDict[h].items():
            if k not in boxDist.keys():
                boxDist[k] = []

            for v in vL:
                boxDist[k].append(v)

        ax.plot(sorted(interfaceSizeDict[h].keys()), [np.mean(t) for k, t in sorted(interfaceSizeDict[h].items())], "o--", label="total neighbour: " + str(h))

        #for i, tsList in interfaceSizeDict[h].items():
        #    ii = [i for p in tsList]
        #    ax.plot(ii, tsList, "+")

        # Estimate
        y = [B[0] +  B[1] * np.log(h) + B[2] * np.log(i) for i in x]
        ax.plot(x, y, "-", label="total neighbour: " + str(h))

        #Best = [-2.11062418,  1.41218773, -1.39434254]
        #y = [np.exp(Best[0]) * np.power(h, Best[1] + Best[2]) * np.power(i / h, Best[2]) for i in x]
        #ax.plot(x, y, "-", label="total neighbour: " + str(h))

    #ax.boxplot(boxDist.values(), positions=boxDist.keys())

    plt.xlabel('max interface size')
    plt.legend()
    plt.title('synchronized time model')
    plt.ylabel('Time')

    '''
(1, 1, 64, 123) - (0)

(1, 2, 32, 111) - (2.0)
(1, 4, 16, 123) - (6.0)
(1, 8, 8, 111) - (14.0)
(1, 16, 4, 123) - (30.0)
(1, 32, 2, 111) - (62.0)
(1, 64, 1, 138) - (126.0)

(2, 2, 16, 123) - (8.0)
(2, 4, 8, 111) - (20.0)
(2, 8, 4, 123) - (44.0)
(2, 16, 2, 111) - (92.0)
(2, 32, 1, 105) - (188.0)

(4, 4, 4, 123) - (48.0)
(4, 8, 2, 111) - (104.0)
(4, 16, 1, 105) - (216.0)

(8, 8, 1, 105) - (224.0)
    '''
    '''
    # Trace la courbe en fonction de h
    bx = fig.add_subplot(212)
#    bx = fig.add_subplot(111)
    x = np.linspace(0, 256, 10)
    for i in sorted(neighbourhoodDict):
        bx.plot(sorted(neighbourhoodDict[i].keys()), [np.mean(t) for k, t in sorted(neighbourhoodDict[i].items())], "o-", label="interfacesize: " + str(i))
        # Estimate
        #y = [lambdaValue + deltaValue * np.log(h) + thetaValue * np.log(i) for h in x]
#        bx.plot(x, y, "--")


    plt.xlabel('total neighbour number')
    #plt.legend(loc='upper left')
    plt.title('synchronized time model')
    plt.ylabel('Time')
    '''

    '''
    for i in varYDict.keys():
        errbarp = {}
        errbarm = {}
        for h, v in varYDict[i].items():
            print i, h, v
            x = h
            yp = h*(lambdaValue + deltaValue*i) + v * sigma * sigma
            ym = h*(lambdaValue + deltaValue*i) - v * sigma * sigma
            errbarp[x] = yp
            errbarm[x] = ym

        bx.plot(errbarp.keys(), errbarp.values(), "+")
        bx.plot(errbarm.keys(), errbarm.values(), "x")



    positionList = []
    valueList = []
    for s in sorted(neighbourhoodDict):
        for k in neighbourhoodDict[s].keys():
            positionList.append(k)
        for k in neighbourhoodDict[s].values():
            valueList.append(k)
    bx.boxplot(valueList, positions=positionList)

    plt.legend(loc='upper left')
    plt.title('synchronized time model')

    # Trace la courbe en fonction de predict
    cx = fig.add_subplot(111)
    cx.plot(X,Y,"+")
    cx.plot(X,X,"--")
    '''


    plt.show()

    return B

# Définition du cas d'étude
filterDict = {'nSizeX' : 512, 'nSizeY' : 512}
resource = 8
data = parser.getData(filterDict)
if not len(data):
    print("Aucune données.")
    sys.exit(1)
#pprint(data)

# Estimation de Tc sur un seul point de fonctionnement.
expectTc = chargeEstimate(data, resource)
print("E[Tc] = %s milliseconds per (iteration x cell number)" % (expectTc))

# Estimation des paramètres du modèle de Ts en fonction de plusieurs cas
greeks = greeksEstimate(data, resource)
print("Greeks: ", greeks)

# Estimation de Ts par point de fonctionnement.
expectTsDict = synchronizeEstimate(data, resource)
for point, expectTs in expectTsDict.items():
    print("E[Ts] = %s milliseconds per (iteration x cell number) - %s - (%s)" % (expectTs, point, computeNeighborNumber(point[0],point[1])))
minTuple = sorted(expectTsDict.items(), key=operator.itemgetter(1))[1]
print("min(E[Ts]) value = %s on point: %s" % (minTuple[1], minTuple[0]))
maxTuple = sorted(expectTsDict.items(), key=operator.itemgetter(1))[-1]
print("max(E[Ts]) value = %s on point: %s" % (maxTuple[1], maxTuple[0]))

# Estimation de T par point de fonctionnement.
expectTtotDict = expectation(data, 'loopTime', str(resource) + ':1:4')
minPoint = (0,0,0)
minValue = 1e300
for point, expectTot in expectTtotDict.items():
    if expectTot < minValue:
        minValue = expectTot
        minPoint = point
    print("E[T] = %s milliseconds per (iteration x cell number) - %s - (%s)" % (expectTot, point, computeNeighborNumber(point[0],point[1])))
print("min(E[T]) value = %s on point: %s" % (minValue, minPoint))

# Estimation de Tt par point de fonctionnement.
expectTtDict = {}
for point, expectTot in expectTtotDict.items():
    expectTt = expectTot - expectTc / (point[0] * point[1] * point[2]) - expectTsDict[point]
    # print "E[Tt] = %s - %s / %s - %s = %s" % (expectTot, expectTc, (point[0] * point[1] * point[2]), expectTsDict[point], expectTt)
    expectTtDict[point] = expectTt
    print("E[Tt] = %s milliseconds per (iteration x cell number) - %s - (%s)" % (expectTt, point, computeNeighborNumber(point[0],point[1])))

minTuple = sorted(expectTtDict.items(), key=operator.itemgetter(1))[0]
print("min(E[Tt]) value = %s on point: %s" % (minTuple[1], minTuple[0]))

maxTuple = sorted(expectTtDict.items(), key=operator.itemgetter(1))[-1]
print("max(E[Tt]) value = %s on point: %s" % (maxTuple[1], maxTuple[0]))

# Estimation de Tmod par point de fonctionnement.
expectTmodDict = {}
expectTsmodDict = {}
for point, expectTt in expectTtDict.items():

    nx = point[0]
    ny = point[1]
    h = computeNeighborNumber(nx, ny)
    interface_size = filterDict['nSizeX'] + filterDict['nSizeY']

    estimate = np.exp(greeks[0]) * np.power(h, greeks[1] + greeks[2]) * np.power(interface_size, greeks[2])
    estimateMod = estimate * np.power(2, 2 + greeks[2])
    expectTsmod = estimateMod

    #print(point, "expectTsmod:", expectTsmod, "expectTs:", expectTsDict[point], "estimateTs:", estimate, "estimateTsmod:", estimateMod)
    expectTsmodDict[point] = expectTsmod
    expectTmodDict[point] = expectTt + expectTsmod + expectTc / (point[0] * point[1] * point[2])

    print("E[Tm] = %s milliseconds per (iteration x cell number) - %s - (%s)" % (expectTmodDict[point], point, computeNeighborNumber(point[0], point[1])))
minTuple = sorted(expectTmodDict.items(), key=operator.itemgetter(1))[0]
print("min(E[Tm]) value = %s on point: %s" % (minTuple[1], minTuple[0]))

# Final Plot
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
#ax.set_xscale('log', basex=2)
x = np.linspace(1, 128, 40)
coeff = 0.5
y = [expectTc / (point[0] * point[1] * point[2]) * coeff * (p - 1.0) / (p - coeff * (p - 1.0)) for p in x]
#ax.plot(x, y, "--", label='ideal')


plotTtDict = {}
for k, v in expectTtDict.items():
    if k[2] not in plotTtDict.keys():
        plotTtDict[k[2]] = []
    plotTtDict[k[2]].append(v)
ax.boxplot(plotTtDict.values(), positions=plotTtDict.keys())
ax.plot(sorted(plotTtDict.keys()), [np.mean(v) for k, v in sorted(plotTtDict.items())], label='E[Tt]')

plotTsDict = {}
for k, v in expectTsDict.items():
    if k[2] not in plotTsDict.keys():
        plotTsDict[k[2]] = []
    plotTsDict[k[2]].append(v)
ax.boxplot(plotTsDict.values(), positions=plotTsDict.keys())
ax.plot(sorted(plotTsDict.keys()), [np.mean(v) for k, v in sorted(plotTsDict.items())], label='E[Ts]')


plotTsmodDict = {}
for k, v in expectTsmodDict.items():
    if k[2] not in plotTsmodDict.keys():
        plotTsmodDict[k[2]] = []
    plotTsmodDict[k[2]].append(v)
ax.boxplot(plotTsmodDict.values(), positions=plotTsmodDict.keys())
ax.plot(sorted(plotTsmodDict.keys()), [np.mean(v) for k, v in sorted(plotTsmodDict.items())], label='E[TsMod]')

plt.legend(loc='upper right')
plt.show()



'''

# Estimation de T_c avec des données sur 1 coeur

On modélise T_c comme un processus gaussien stationnaire. On estime avec 30 tirages sa moyenne et sa variance.
(comme c'est stationnaire, quelque soit le point de fonctionnement, la moyenne et la variance sont les m\^emes)
Test Khi2 ou visuel avec l'histogramme.

# Trace l'histogramme
from pandas import Series
values = Series(sample)
values.hist(bins=20, alpha=0.3, color='k', normed= True)
values.plot(kind='kde', style='k--')
plt.show()

Deuxième étape:
- estimation du bruit sur T_s (voir pour tous les nx, ny) avec moindre carrés. (parce qu'il n'est pas stationnaire).
- calibration "traditionnelle" (par minimisation des moindres carrés) du modèle pour $T_s$ ($lambda$ et $theta$ dans le cas différent de 0)
- Leave one out pour valider

Troisième étape:
'''
