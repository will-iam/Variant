#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
import sys
import os
import argparse

import script.build_case as build_case
import script.sdd as sdd
from script.launcher import get_case_path
from timeit import default_timer as timer

parser = argparse.ArgumentParser(description="Build and Split case", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("-c", type = str, help = "Case to test", required=True)
args = parser.parse_args()

project_name = args.project_name
case_name = args.c
#nSDD_X = args.x
#nSDD_Y = args.y
#nSDD = [(1,1),(2, 2),(4, 4),(8, 8),(16, 16),(32, 32)]
#nSDD = [(1,1),(2, 2),(4, 4),(8, 8),(16, 16)]
#nSDD = [(1,1),(2, 2),(4, 4),(8, 8)]
#nSDD = [(1,1),(2, 2),(4, 4)]
#nSDD = [(1,1),(2, 2)]

SDD_powersOfTwo = [0, 1, 2, 3, 4, 5, 6, 7, 8]

nSDD = []
for p in SDD_powersOfTwo:
    # Different SDD splits
    for i in range(int(p//2 + 1)):
        nSDD.append((2**i, 2**(p-i)))

nSDD = [(2, 2), (2, 4), (4, 4), (4, 8), (8, 8), (8, 16), (16, 16), (16, 32)]
#nSDD = [(16, 32), (32, 32), (32, 64)]
nSDD = [(1, 1)]

this_path = os.path.split(os.path.abspath(__file__))[0]

# Get case names from all directories in case/project_name/
case_path = get_case_path(project_name, case_name)
init_path = os.path.join(case_path, "init")

# Build case
start = timer()
qty_name_list = build_case.build_case(case_path, init_path)
end = timer()
print("Build case %s in %s second(s)" % (case_path, int((end - start))))

for (nSDD_X, nSDD_Y) in nSDD:
	print("Splitting into " + str((nSDD_X, nSDD_Y)))
	sdd.split_case(init_path, nSDD_X, nSDD_Y, qty_name_list)
