#!/usr/bin/python
# -*- coding:utf-8 -*-

import numpy as np
import os
import errno
import sys
from decimal import Decimal
from shutil import copy2

import numpy as np

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def read_converter(input_dir, uid_to_coords):
    with open(os.path.join(input_dir, 'domain.dat'), 'r') as domain_f:
        # Reading mesh info on the first line
        # Read dx and dy in first line
        first_line = domain_f.readline().split()
        lx = Decimal(first_line[2])
        ly = Decimal(first_line[3])
        Nx = int(first_line[4])
        Ny = int(first_line[5])

        dx = lx / Nx
        dy = ly / Ny

        for line in domain_f:
            line_list = line.split()
            if line_list:
                uid_to_coords[int(line_list[0])] = (int(line_list[1]), int(line_list[2]))

    return Nx, Ny, dx, dy


def read_quantity(data, input_dir, uid_to_coords, quantity_name):

#    with open(os.path.join(input_dir, quantity_name + '.dat'), 'r') as quantity_f:
#        for line in quantity_f:
#            line_list = line.split(' ')
#            coords = uid_to_coords[int(line_list[0])]
#            value = Decimal(line_list[1])
#            data[coords[0]][coords[1]] = value

    quantity = np.loadtxt(os.path.join(input_dir, quantity_name + '.dat'))
    for i, v in quantity:
        coords = uid_to_coords[int(i)]
        data[coords[0]][coords[1]] = v

def read_exec_options(input_dir):
    with open(os.path.join(output_dir, 'exec_options.dat'), 'r') as f:
        line_list = f.readline().split()

    exec_options = dict()
    exec_options['nSDD'] = int(line_list[0])
    exec_options['nSDD_X'] = int(line_list[1])
    exec_options['nSDD_Y'] = int(line_list[2])
    exec_options['nSDS'] = int(line_list[3])
    exec_options['SDSgeom'] = line_list[4]
    exec_options['nThreads'] = int(line_list[5])
    exec_options['nCoresPerSDD'] = int(line_list[6])

    return exec_options

def read_domain(input_dir):
    with open(os.path.join(output_dir, 'domain.dat'), 'r') as f:
        line_list = f.readline().split()
        domain = dict()
        domain['lx'] = float(line_list[2])
        domain['ly'] = float(line_list[3])
        domain['Nx'] = float(line_list[4])
        domain['Ny'] = float(line_list[5])

        data = np.zeros((Nx, Ny), dtype=int)
        for line in f.readlines():
            line_list = line.split()
            data[int(line_list[1])][int(line_list[2])] = line_list[0]

    return domain

def read_perfs(input_dir):
    f = open(os.path.join(input_dir, 'perfs.dat'), 'r')
    perfs = dict()
    for line in f.readlines():
        line_list = line.split()
        perfs[line_list[0]] = int(line_list[1])
    f.close()
    return perfs

def gen_coords_to_uid(Nx, Ny):
    coords_to_uid = dict()
    for i in range(Nx):
        for j in range(Ny):
            coords_to_uid[(i, j)] = i + j * Nx
    return coords_to_uid

def gen_coords_to_uid_bc(Nx, Ny, BClayer):
    coords_to_uid_bc = dict()
    uid = Nx * Ny

    for k in range(1, BClayer + 1):
        # Left border
        for j in range(-k, Ny - 1 + k):
            coords_to_uid_bc[(-k, j)] = uid
            uid += 1
        # Top border
        for i in range(-k, Nx - 1 + k):
            coords_to_uid_bc[(i, Ny - 1 + k)] = uid
            uid += 1
        # Right border
        for j in range(Ny, -k, -1):
            coords_to_uid_bc[(Nx - 1 + k, j)] = uid
            uid += 1
        # Bottom border
        for i in range(Nx, -k, -1):
            coords_to_uid_bc[(i, -k)] = uid
            uid += 1
    return coords_to_uid_bc

def write_domain(output_dir, lx, ly, Nx, Ny, coords_to_uid, BClayer):
    make_sure_path_exists(output_dir)
    with open(os.path.join(output_dir, 'domain.dat'), 'w+') as f:
        f.write("2D cartesian %s %s %s %s %s\n" % (lx, ly, Nx, Ny, BClayer))
        for coords, uid in coords_to_uid.items():
            f.write("%s %s %s\n" % (uid, coords[0], coords[1]))

    return coords_to_uid

def write_quantity(output_dir, quant_name, uid_to_val):
    #if quant_name == "rhoe":
    #    import pdb; pdb.set_trace()
    #"{:16.16g}".format(val)

    #with open(os.path.join(output_dir, quant_name + '.dat'), 'w+') as f:
    #    for uid, val in uid_to_val:
    #        f.write(str(uid) + " " + "{:16.16g}".format(val) + "\n")

    x = np.arange(len(uid_to_val))
    np.savetxt(os.path.join(output_dir, quant_name + '.dat'), np.c_[x, uid_to_val], fmt='%d\t%16.16g')

def write_scheme_info(output_dir, T, CFL):
    with open(os.path.join(output_dir, 'scheme_info.dat'), 'w+') as f:
        f.write(str(T) + " ")
        f.write(str(CFL) + "\n")

def write_exec_options(output_dir, nSDD, nSDD_X, nSDD_Y, nSDS, SDSgeom, nThreads, nCommonSDS, nCoresPerSDD):
    with open(os.path.join(output_dir, 'exec_options.dat'), 'w+') as f:
        f.write(str(nSDD) + " ")
        f.write(str(nSDD_X) + " ")
        f.write(str(nSDD_Y) + " ")
        f.write(str(nSDS)+ " ")
        f.write(SDSgeom + " ")
        f.write(str(nThreads) + " ")
        f.write(str(nCommonSDS) + " ")
        f.write(str(nCoresPerSDD) + "\n")

def write_bc(output_dir, coords_to_uid_and_bc):
    with open(os.path.join(output_dir, 'bc.dat'), 'w+') as f:
        for bcc, (uid, bc) in coords_to_uid_and_bc.items():
            f.write(str(uid) + " ")
            f.write(str(bcc[0]) + " " + str(bcc[1]) + " ")   # (i, j) coords
            f.write(str(bc[0]) + " " + str(bc[1]) + "\n")   # boundary condition

def read_variant_info(data_dir, nSDD):
    whole_data = []
    for i in range(nSDD):
        with open(os.path.join(data_dir, 'sdd' + str(i), 'variant_info.dat'), 'r') as f:
            data = []
            for line in f.readlines():
                for el in line.split():
                    try:
                        data.append(int(el))
                    except ValueError:
                        data.append(el)
            whole_data.append(tuple(data))

    return whole_data

def read_perf_info(data_dir, nSDD):
    computeTime = {}
    iterationTime = {}
    for i in range(nSDD):
        computeTime[i] = np.loadtxt(os.path.join(data_dir, 'sdd' + str(i), 'timer-compute.dat'))
        iterationTime[i] = np.loadtxt(os.path.join(data_dir, 'sdd' + str(i), 'timer-iteration.dat'))

    return {'computeTime': computeTime, 'iterationTime': iterationTime}
