import __future__
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
#plt.style.use('ggplot')
from decimal import Decimal
from timeit import default_timer as timer
import argparse
sys.path.insert(1, os.path.join(sys.path[0], 'sod'))
from sod import solve
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rio import read_quantity, read_converter
sys.path.insert(1, os.path.join(sys.path[0], '..','..'))
import config

parser = argparse.ArgumentParser(description="Visualize reference results from simulation", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("--case", type = str, help = "Case to visualize", required=True)
args = parser.parse_args()
