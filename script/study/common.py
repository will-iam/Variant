import __future__
import sys
import os
import operator
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('ggplot')
from timeit import default_timer as timer
import argparse
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rio import read_quantity, read_converter
sys.path.insert(1, os.path.join(sys.path[0], '..','..'))
import config

parser = argparse.ArgumentParser(description="Visualize reference results from simulation", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("--case", type = str, help = "Case to visualize", required=True)
parser.add_argument("--rounding-mode", type = str, help = "Rounding mode searched", default='nearest', required=False)
parser.add_argument("--precision", type = str, help = "Precision searched", default='double', required=False)
parser.add_argument("--solver", type = str, help = "Exact Solver", default='sod', required=False)
parser.add_argument("--axis", type = str, help = "Axis along which you expect the solution", default='x', required=False)
args = parser.parse_args()

def outputCurve(filename, x, y):
    if len(x) != len(y):
        raise ValueError

    with open(filename, 'w+') as f:
        for p in zip(x,y):
            f.write(str(p[0]) + "\t" + "{:16.16g}".format(p[1]) + "\n")

def outputPoint(filename, pointDict):
    with open(filename, 'w+') as f:
        for k, v in pointDict.items():
            for e in v:
                f.write(str(k) + "\t" + "{:16.16g}".format(e) + "\n")
