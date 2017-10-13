#!/usr/bin/python
# -*- coding:utf-8 -*-

import numpy as np
import os
import errno
from decimal import Decimal
from shutil import copy2

import numpy as np

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def read_quantity(input_dir, quantity_name, dtype = 'decimal'):
    domain_f = open(os.path.join(input_dir, 'domain.dat'), 'r')

    # Reading mesh info on the first line
    # Read dx and dy in first line
    first_line = domain_f.readline().split()
    lx = Decimal(first_line[2])
    ly = Decimal(first_line[3])
    Nx = int(first_line[4])
    Ny = int(first_line[5])

    dx = lx / Nx
    dy = ly / Ny

    uid_to_coords = dict()
    for line in domain_f:
        line_list = line.split()
        if line_list:
            uid_to_coords[line_list[0]] = (int(line_list[1]), int(line_list[2]))
    domain_f.close()

    data = None
    if dtype == 'decimal':
        data = np.zeros((Nx, Ny), dtype = np.dtype(Decimal))
    elif dtype == 'str':
        data = np.zeros((Nx, Ny), dtype = object)
    quantity_f = open(os.path.join(input_dir, quantity_name + '.dat'), 'r')
    for line in quantity_f:
        line_list = line.split(' ')
        coords = uid_to_coords[line_list[0]]
        if dtype == 'decimal':
            value = Decimal(line_list[1])
        elif dtype == 'str':
            value = line_list[1]

        data[coords[0]][coords[1]] = value

    quantity_f.close()
    return dx, dy, data

def read_exec_options(input_dir):
    f = open(os.path.join(output_dir, 'exec_options.dat'), 'r')
    line_list = f.readline().split()
    f.close()

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
    f = open(os.path.join(output_dir, 'domain.dat'), 'r')
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
    f.close()

    return domain

def read_perfs(input_dir):
    print("read_perfs: ", input_dir + "/" + "perfs.dat")
    f = open(os.path.join(input_dir, 'perfs.dat'), 'r')
    perfs = dict()
    for line in f.readlines():
        line_list = line.split()
        perfs[line_list[0]] = int(line_list[1])
        print "line", line
        print line_list[0], line_list[1]
    f.close()

    print perfs
    return perfs

def write_quantity_from_array(output_dir, data, domain_dir, quantity_name):
    # Reading domain first
    domain_f = open(os.path.join(domain_dir, 'domain.dat'), 'r')

    first_line = domain_f.readline().split()
    lx = Decimal(first_line[2])
    ly = Decimal(first_line[3])
    Nx = int(first_line[4])
    Ny = int(first_line[5])
    if Nx != data.shape[0] or Ny != data.shape[1]:
        print("ERROR: data shape does not match with domain info")
        sys.exit(1)

    dx = lx / Nx
    dy = ly / Ny

    coords_to_uid = dict()
    for line in domain_f:
        line_list = line.split()
        if line_list:
            coords_to_uid[(int(line_list[1]),
                int(line_list[2]))] = line_list[0]
    domain_f.close()

    # Copying domain file to output directory
    if not os.path.isfile(os.path.join(domain_dir, 'domain.dat')):
        copy2(os.path.join(domain_dir, 'domain.dat'), output_dir)
    quantity_f = open(os.path.join(output_dir, quantity_name + '.dat'), 'w')
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            quantity_f.write(coords_to_uid[i, j] + " " +
                    str(data[i][j]) + "\n")
    quantity_f.close()

def gen_coords_to_uid(Nx, Ny):
    coords_to_uid = dict()
    for i in range(Nx):
        for j in range(Ny):
            coords_to_uid[(i, j)] = i + j * Nx
    return coords_to_uid

def gen_coords_to_uid_bc(Nx, Ny):
    coords_to_uid_bc = dict()
    uid = Nx * Ny
    # Left border
    for j in range(-1, Ny):
        coords_to_uid_bc[(-1, j)] = uid
        uid += 1
    # Top border
    for i in range(-1, Nx):
        coords_to_uid_bc[(i, Ny)] = uid
        uid += 1
    # Right border
    for j in range(Ny, -1, -1):
        coords_to_uid_bc[(Nx, j)] = uid
        uid += 1
    # Bottom border
    for i in range(Nx, -1, -1):
        coords_to_uid_bc[(i, -1)] = uid
        uid += 1
    return coords_to_uid_bc

def write_domain(output_dir, lx, ly, Nx, Ny, coords_to_uid):
    make_sure_path_exists(output_dir)
    f = open(os.path.join(output_dir, 'domain.dat'), 'w+')
    f.write("2D cartesian ")
    f.write(str(lx) + " ")
    f.write(str(ly) + " ")
    f.write(str(Nx) + " ")
    f.write(str(Ny) + "\n")
    for coords, uid in coords_to_uid.iteritems():
        f.write(str(uid) + " ")
        f.write(str(coords[0]) + " ")
        f.write(str(coords[1]) + "\n")
    f.close()
    return coords_to_uid

def write_quantity(output_dir, quant_name, uid_to_val):
    f = open(os.path.join(output_dir, quant_name + '.dat'), 'w+')
    for uid, val in uid_to_val.iteritems():
        f.write(str(uid) + " " + str(val) + "\n")
    f.close()

def write_scheme_info(output_dir, T, CFL):
    f = open(os.path.join(output_dir, 'scheme_info.dat'), 'w+')
    f.write(str(T) + " ")
    f.write(str(CFL) + "\n")
    f.close()

def write_exec_options(output_dir, nSDD, nSDD_X, nSDD_Y, nSDS, SDSgeom, nThreads, nCoresPerSDD):
    f = open(os.path.join(output_dir, 'exec_options.dat'), 'w+')
    f.write(str(nSDD) + " ")
    f.write(str(nSDD_X) + " ")
    f.write(str(nSDD_Y) + " ")
    f.write(str(nSDS)+ " ")
    f.write(SDSgeom + " ")
    f.write(str(nThreads) + " ")
    f.write(str(nCoresPerSDD) + "\n")
    f.close()

def write_bc(output_dir, coords_to_uid_and_bc):
    f = open(os.path.join(output_dir, 'bc.dat'), 'w+')
    for bcc, (uid, bc) in coords_to_uid_and_bc.iteritems():
        f.write(str(uid) + " ")
        f.write(str(bcc[0]) + " " + str(bcc[1]) + " ")   # (i, j) coords
        f.write(str(bc[0]) + " " + str(bc[1]) + "\n")   # boundary condition
    f.close()

#def write_qbc(output_dir, quant_name, uid_to_qbc):
#    f = open(os.path.join(output_dir, quant_name + '_bc.dat'), 'w+')
#    for uid, qbc in uid_to_qbc.iteritems():
#        f.write(str(uid) + " ")
#        f.write(str(qbc[0]) + " ")   # BC type
#        f.write(str(qbc[1]) + "\n")  # BC value
#    f.close()

def read_variant_info(data_dir, nSDD):
    whole_data = []
    for i in range(nSDD):
        data = []
        f = open(os.path.join(data_dir, 'sdd' + str(i), 'variant_info.dat'), 'r')
        for line in f.readlines():
            for el in line.split():
                try:
                    data.append(int(el))
                except ValueError:
                    data.append(el)
        f.close()
        whole_data.append(tuple(data))

    return whole_data

def read_perf_info(data_dir, nSDD):
    perfs = {}
    for i in range(nSDD):
        f = open(os.path.join(data_dir, 'sdd' + str(i), 'perfs.dat'), 'r')
        for line in f.readlines():
            line_list = line.split()
            if line_list[0] not in perfs:
                perfs[line_list[0]] = []
            perfs[line_list[0]].append(int(line_list[1]))
        f.close()
    return perfs

def write_quantity_names(output_dir, qty_names):
    f = open(os.path.join(output_dir, 'quantities.dat'), 'w')
    f.write(' '.join(qty_names) + '\n')
    f.close()

def read_quantity_names(input_dir):
    f = open(os.path.join(input_dir, 'quantities.dat'), 'r')
    qty_names = f.readline().split()
    f.close()
    return qty_names

