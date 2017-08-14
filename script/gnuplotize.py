#!/usr/bin/python3
# -*- coding:utf-8 -*-

import __future__
import argparse
import os
from decimal import Decimal
from math import sqrt

parser = argparse.ArgumentParser(description="Build gnuplot-readable results out of domain and quantity data")

parser.add_argument("--quantity", type = str, help = "Name of quantity to read")
parser.add_argument("-t", type = str, choices=['scalar', 'vector'], help =
"Quantity type : scalar or vector")
parser.add_argument("input_dir", type = str, help = "Path to quantity directory")
args = parser.parse_args()

input_dir = args.input_dir
quantity_name = args.quantity
quantity_type = args.t

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
if quantity_type == 'scalar':
    quantity_f = open(os.path.join(input_dir, quantity_name + '.dat'), 'r')
    output_f = open(output_path, 'w+')
    # Write dx and dy info
    output_f.write(str(lx) + '\n')
    output_f.write(str(ly) + '\n')
    output_f.write(str(Nx) + '\n')
    output_f.write(str(Ny) + '\n')
    current_x = -1
    for line in quantity_f:
        line_list = line.split(' ')
        coords = uid_to_coords[line_list[0]]
        if coords[0] != current_x:
            current_x = coords[0]
            output_f.write('\n')
        value = line_list[1]
        output_f.write(str(dx * coords[0]) + ' ' + str(dy * coords[1]) + ' ' + value)

    quantity_f.close()
    output_f.close()

elif quantity_type == 'vector':
    quantity_x_f = open(os.path.join(input_dir, quantity_name + '_x.dat'), 'r')
    quantity_y_f = open(os.path.join(input_dir, quantity_name + '_y.dat'), 'r')
    output_f = open(output_path, 'w+')
    # Write dx and dy info
    #output_f.write(str(lx) + '\n')
    #output_f.write(str(ly) + '\n')
    #output_f.write(str(Nx) + '\n')
    #output_f.write(str(Ny) + '\n')
    # First finding max to normalize
    for line_x in quantity_x_f:
        line_y = quantity_y_f.readline()
        line_x_list = line_x.split(' ')
        line_y_list = line_y.split(' ')

        coords = uid_to_coords[line_x_list[0]]
        value_x = Decimal(line_x_list[1][:-1])
        value_y = Decimal(line_y_list[1][:-1])
        value_norm = (value_x * value_x + value_y * value_y).sqrt()

        xv = dx * coords[0]
        dxv = dx * value_x / value_norm if value_norm > 0 else 0
        yv = dy * coords[1]
        dyv = dy * value_y / value_norm if value_norm > 0 else 0
        output_f.write(str(xv) + '\t' + str(yv) + '\t' + str(dxv) + '\t' +
                str(dyv) + '\t' + str(value_norm) + '\n')

    quantity_x_f.close()
    quantity_y_f.close()
    output_f.close()


