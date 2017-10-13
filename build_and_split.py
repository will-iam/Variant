#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import sys
import os
import argparse

import script.build_case as build_case
import script.sdd as sdd

parser = argparse.ArgumentParser(description="Regression test", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("-c", type = str, help = "Case to test", required=True)
#parser.add_argument("-x", type = str, help = "Number of SDDs alongs x-axis", required=True)
#parser.add_argument("-y", type = str, help = "Number of SDDs alongs y-axis", required=True)
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

SDD_powersOfTwo = [0, 1, 2, 3, 4, 5, 6]
nSDD = []
for p in SDD_powersOfTwo:
    # Different SDD splits
    for i in range(p+1):
		nSDD.append((2**i, 2**(p-i)))

this_path = os.path.split(os.path.abspath(__file__))[0]

# Get case names from all directories in case/project_name/
project_path = os.path.join("/ccc/cont002/temp/m7/weens4x/VariantCase/case", project_name)
case_path = os.path.join(project_path, case_name)
full_domain_path, qty_name_list = build_case.build_case(this_path, project_path, project_name, case_name)

for (nSDD_X, nSDD_Y) in nSDD:
	print("Splitting into " + str((nSDD_X, nSDD_Y)))
	sdd.split_case(full_domain_path, nSDD_X, nSDD_Y, qty_name_list)




