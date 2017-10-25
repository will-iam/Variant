#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import os
import sys
from io import read_quantity_names
from analytics import compare_data
import argparse

COLOR_BLUE = '\x1b[1;36m'
COLOR_ENDC = '\x1b[0m'

parser = argparse.ArgumentParser(description="Compare Outputs", prefix_chars='-')
parser.add_argument("path1", type = str, help = "Case 1 to test")
parser.add_argument("path2", type = str, help = "Case 2 to test")
args = parser.parse_args()

print("Checking test " + args.path1 + " against " + args.path2)
qties_to_compare = read_quantity_names(args.path1)
results = compare_data(args.path1, args.path2, qties_to_compare)
if results[0]:
    print("OK for all quantities")
else:
    print("Error for quantity " + str(results[1]))
print results
