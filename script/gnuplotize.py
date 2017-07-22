#!/usr/bin/python3
# -*- coding:utf-8 -*-

import __future__
import argparse
import os
from decimal import Decimal

parser = argparse.ArgumentParser(description="Build gnuplot-readable results out of domain and quantity data")

parser.add_argument("--quantity", type = str, help = "Name of quantity to read")
parser.add_argument("input_dir", type = str, help = "Path to quantity directory")
args = parser.parse_args()

input_dir = args.input_dir
quantity_name = args.quantity

# Opening domain file
print('Reading domain data')
f = open(os.path.join(input_dir, 'domain.dat'), 'r')

# Read dx and dy in first line
first_line = f.readline().split()
lx = Decimal(first_line[2])
ly = Decimal(first_line[3])
Nx = int(first_line[4])
Ny = int(first_line[5])
dx = lx / Nx
dy = ly / Ny

# Reading uid <-> coords correspondence in domain file
uid_to_coords = dict()
for line in f:
    line_list = line.split()
    if line_list:
        uid_to_coords[line_list[0]] = (Decimal(line_list[1]), Decimal(line_list[2]))
f.close()

output_path = os.path.join(input_dir, 'gnuplot_' + quantity_name + '.dat')
print('Reading quantity data')
print('Writing to output file ' + output_path)

# Reading quantity data and print to output file
quantity_f = open(os.path.join(input_dir, quantity_name + '.dat'), 'r')
output_f = open(output_path, 'w+')
# Write dx and dy info
output_f.write(str(lx) + '\n')
output_f.write(str(ly) + '\n')
output_f.write(str(Nx) + '\n')
output_f.write(str(Ny) + '\n')
for line in quantity_f:
    line_list = line.split(' ')
    coords = uid_to_coords[line_list[0]]
    value = line_list[1]
    output_f.write(str(dx * coords[0]) + ' ' + str(dy * coords[1]) + ' ' + value)

quantity_f.close()
output_f.close()




