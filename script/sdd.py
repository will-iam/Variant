#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import os
import sys
import argparse
import numpy as np

import io
import imp
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import config

def split_domain(domain_dir, output_dir, nSDD_X, nSDD_Y):
    io.make_sure_path_exists(output_dir)

    domain_f = open(os.path.join(domain_dir, 'domain.dat'), 'r')
    line_split = domain_f.readline().split()
    domain_lx = line_split[2]
    domain_ly = line_split[3]
    domain_Nx = int(line_split[4])
    domain_Ny = int(line_split[5])

    SDD_Nx = domain_Nx / nSDD_X
    SDD_Ny = domain_Ny / nSDD_Y

    # Writing short domain info
    domain_shortinfo = open(os.path.join(output_dir, 'domain.dat'), 'w+')
    domain_shortinfo.write(domain_lx + " " + domain_ly +\
            " " + str(domain_Nx) + " " + str(domain_Ny) +\
            " " + str(nSDD_X) + " " + str(nSDD_Y) + "\n")
    domain_shortinfo.close()

    uid_to_SDD_and_coords = [None] * (domain_Nx * domain_Ny)

    # We build for each SDD a file stream that will be updated through
    # iterations on the domain data
    file_streams = list()
    for x in range(nSDD_X):
        file_streams_tmp = list()
        for y in range(nSDD_Y):
            # Writing SDD file
            SDDid = y * nSDD_X + x
            SDDpath = os.path.join(output_dir, 'sdd' + str(SDDid))
            io.make_sure_path_exists(SDDpath)
            file_stream = open(os.path.join(SDDpath, 'sdd.dat'), 'w+')

            # Writing bottom-left coords on domain
            BL_X = SDD_Nx * x
            BL_Y = SDD_Ny * y
            file_stream.write(str(BL_X) + " " + str(BL_Y) + "\n")
            file_stream.write(str(SDD_Nx) + " " + str(SDD_Ny) + "\n")
            file_streams_tmp.append(file_stream)
        file_streams.append(file_streams_tmp)

    # Now iterating through all coords of domain
    for line in domain_f.readlines():
        line_split = line.split()

        coordX = int(line_split[1])
        coordY = int(line_split[2])
        x = coordX / SDD_Nx
        y = coordY / SDD_Ny
        BL_X = SDD_Nx * x
        BL_Y = SDD_Ny * y

        # SDD id is known based on coords
        uid = int(line_split[0])
        SDDid = y * nSDD_X + x

        # Finally writing uid on domain and position on SDD
        file_streams[x][y].write(str(uid) + " " +
                str(coordX - BL_X) + " " + str(coordY - BL_Y) + "\n")

        SDD_and_coords = dict()
        SDD_and_coords['SDDid'] = SDDid
        SDD_and_coords['coords'] = (coordX - BL_X, coordY - BL_Y)
        uid_to_SDD_and_coords[uid] = SDD_and_coords

    # Closing all streams
    domain_f.close()
    for y in range(nSDD_Y):
        for x in range(nSDD_X):
            file_streams[x][y].close()

    return uid_to_SDD_and_coords

def merge_domain(split_dir, output_dir):
    domain_shortinfo = open(os.path.join(split_dir, "domain.dat"), 'r')
    line_domain = domain_shortinfo.readline()
    line_split = line_domain.split()
    domain_shortinfo.close()

    io.make_sure_path_exists(output_dir)
    domain_f = open(os.path.join(output_dir, "domain.dat"), 'w+')
    domain_f.write("2D cartesian ")
    domain_f.write(" ".join([st for st in line_split[:4]]) + "\n")

    nSDD_X = int(line_split[4])
    nSDD_Y = int(line_split[5])

    for x in range(nSDD_X):
        for y in range(nSDD_Y):
            # Writing SDD file
            SDDid = y * nSDD_X + x
            SDDpath = os.path.join(split_dir, 'sdd' + str(SDDid))
            file_stream = open(os.path.join(SDDpath, 'sdd.dat'), 'r')

            line_split = file_stream.readline().split()
            BL_X = int(line_split[0])
            BL_Y = int(line_split[1])
            line_split = file_stream.readline().split()
            SDD_Nx = int(line_split[0])
            SDD_Ny = int(line_split[1])

            for i in range(SDD_Nx):
                for j in range(SDD_Ny):
                    line_split = file_stream.readline().split()
                    uid = line_split[0]
                    coordX_SDD = int(line_split[1])
                    coordY_SDD = int(line_split[2])
                    domain_f.write(uid + " " + str(BL_X + coordX_SDD) + " " +
                            str(BL_Y + coordY_SDD) + "\n")

    domain_f.close()

def split_quantity(quantity_dir, output_dir, quantity_name,
        uid_to_SDD_and_coords):
    domain_shortinfo = open(os.path.join(output_dir, "domain.dat"), 'r')
    line_domain = domain_shortinfo.readline()
    line_split = line_domain.split()
    domain_shortinfo.close()

    nSDD = int(line_split[4]) * int(line_split[5])

    quantity_f = open(os.path.join(quantity_dir, quantity_name + '.dat'), 'r')

    file_streams = list()
    # Opening streams for all SDDs
    for SDDid in range(nSDD):
        SDDpath = os.path.join(output_dir, 'sdd' + str(SDDid))
        file_streams.append(open(os.path.join(SDDpath, quantity_name + '.dat'),
            'w+'))

    # Now iterationg through all cell uids on quantity file
    for line in quantity_f.readlines():
        line_split = line.split()
        uid = int(line_split[0])
        value = line_split[1]
        SDD_and_coords = uid_to_SDD_and_coords[uid]
        SDDid = SDD_and_coords['SDDid']
        coords = SDD_and_coords['coords']
        file_streams[SDDid].write(str(coords[0]) + " " + str(coords[1]) + " " +
                value + "\n")

    # Closing all streams
    quantity_f.close()
    for fs in file_streams:
        fs.close()

def split_bc(bc_dir, output_dir):
    domain_shortinfo = open(os.path.join(output_dir, "domain.dat"), 'r')
    line_split = domain_shortinfo.readline().split()
    domain_Nx = int(line_split[2])
    domain_Ny = int(line_split[3])
    nSDD_X = int(line_split[4])
    nSDD_Y = int(line_split[5])
    nSDD = nSDD_X * nSDD_Y
    SDD_Nx = domain_Nx / nSDD_X
    SDD_Ny = domain_Ny / nSDD_Y
    domain_shortinfo.close()

    uid_to_SDD_and_coords_bc = [None] * (2 * (domain_Nx + domain_Ny) + 4)

    # Opening file streams
    file_streams = list()
    BL = list()
    for SDDid in range(nSDD):
        SDDpath = os.path.join(output_dir, 'sdd' + str(SDDid))
        file_streams.append(open(os.path.join(SDDpath, 'bc.dat'), 'w+'))
        # BL coordinates of SDDs, needed for coord conversion
        sdd_f = open(os.path.join(SDDpath, 'sdd.dat'), 'r')
        line_split = sdd_f.readline().split()
        BL.append((int(line_split[0]), int(line_split[1])))
        sdd_f.close()

    bc_f = open(os.path.join(bc_dir, 'bc.dat'), 'r')
    for line in bc_f:
        line_split = line.split()
        uid = line_split[0]
        coordX = int(line_split[1])
        coordY = int(line_split[2])
        BCtype = line_split[3]
        value = line_split[4]

        # Determine to which SDD belongs the boundary cell
        eqCoordX = coordX
        eqCoordY = coordY

        # Left
        if coordX == -1:
            eqCoordX = 0
        # Top
        if coordY == domain_Ny:
            eqCoordY = domain_Ny - 1
        # Right
        if coordX == domain_Nx:
            eqCoordX = domain_Nx - 1
        # Bottom
        if coordY == -1:
            eqCoordY = 0

        # Determine SDD corresponding to eq coords
        x = eqCoordX / SDD_Nx
        y = eqCoordY / SDD_Ny
        SDDid = x + nSDD_X * y

        # Determine coords on SDD: we use bottom-left coords of SDD
        BL_X = BL[SDDid][0]
        BL_Y = BL[SDDid][1]

        # and add the boundary cell to the corresponding file
        file_streams[SDDid].write(uid + " " + str(coordX - BL_X) + " " +
                str(coordY - BL_Y) + " " + BCtype + " " + value + "\n")

        SDD_and_coords = dict()
        SDD_and_coords['SDDid'] = SDDid
        SDD_and_coords['coords'] = (coordX - BL_X, coordY - BL_Y)
        uid_to_SDD_and_coords_bc[int(uid) - domain_Nx * domain_Ny] = SDD_and_coords

    for SDDid in range(nSDD):
        file_streams[SDDid].close()

    return uid_to_SDD_and_coords_bc

def split_qbc(split_dir, output_dir, quantity_name, uid_to_SDD_and_coords_bc):
    domain_shortinfo = open(os.path.join(output_dir, "domain.dat"), 'r')
    line_split = domain_shortinfo.readline().split()
    domain_Nx = int(line_split[2])
    domain_Ny = int(line_split[3])
    nSDD = int(line_split[4]) * int(line_split[5])
    domain_shortinfo.close()

    qbc_f = open(os.path.join(split_dir, quantity_name + '_bc.dat'), 'r')

    file_streams = list()
    # Opening streams for all SDDs
    for SDDid in range(nSDD):
        SDDpath = os.path.join(output_dir, 'sdd' + str(SDDid))
        file_streams.append(open(os.path.join(SDDpath, quantity_name + '_bc.dat'),
            'w+'))

    # Now iterationg through all cell uids on quantity file
    for line in qbc_f.readlines():
        line_split = line.split()
        uid = int(line_split[0])
        BCtype = line_split[1]
        value = line_split[2]
        SDD_and_coords = uid_to_SDD_and_coords_bc[uid - domain_Nx * domain_Ny]
        SDDid = SDD_and_coords['SDDid']
        coords = SDD_and_coords['coords']
        file_streams[SDDid].write(str(coords[0]) + " " + str(coords[1]) + " " +
                BCtype + " " + value + "\n")

    # Closing all streams
    qbc_f.close()
    for fs in file_streams:
        fs.close()

def merge_quantity(split_dir, output_dir, quantity_name):
    domain_shortinfo = open(os.path.join(split_dir, "domain.dat"), 'r')
    line_domain = domain_shortinfo.readline()
    line_split = line_domain.split()
    nSDD_X = int(line_split[4])
    nSDD_Y = int(line_split[5])
    domain_shortinfo.close()

    qty_stream = open(os.path.join(output_dir, quantity_name + '.dat'), 'w+')

    for SDDid in range(nSDD_X * nSDD_Y):
        # Build coords -> uid correspondence
        coords_to_uid = dict()
        SDDpath = os.path.join(split_dir, 'sdd' + str(SDDid))
        sdd_f = open(os.path.join(SDDpath, 'sdd.dat'), 'r')

        # First line is bottom-left coords of SDD
        # Second line is size of SDD
        # Both are useless here
        sdd_f.readline()
        sdd_f.readline()

        for line in sdd_f.readlines():
            line_split = line.split()
            coords = (int(line_split[1]), int(line_split[2]))
            uid = line_split[0]
            coords_to_uid[coords] = uid

        sdd_f.close()

        # Now iterating through quantity and add to global quantity stream
        quantity_f = open(os.path.join(SDDpath, quantity_name + '.dat'), 'r')
        i = 0
        for line in quantity_f.readlines():
            line_split = line.split()
            coords = (int(line_split[0]), int(line_split[1]))
            qty_stream.write(coords_to_uid[coords] + " " + line_split[2] +
                    "\n")

    qty_stream.close()


def split_case(domain_dir, nSDD_X, nSDD_Y, qty_name_list):
	output_dir = os.path.join(domain_dir, str(nSDD_X) + "x" + str(nSDD_Y))
	if os.path.isdir(output_dir):
	    print("Split already exists")
	    return output_dir
	io.make_sure_path_exists(output_dir)
	usc = split_domain(domain_dir, output_dir, nSDD_X,
		nSDD_Y)
	usc_bc = split_bc(domain_dir, output_dir)
	for q_str in qty_name_list:
	    split_quantity(domain_dir, output_dir, q_str, usc)
	return output_dir

#def merge_qbc(split_dir, output_dir, quantity_name):
#    domain_shortinfo = open(os.path.join(split_dir, "domain.dat"), 'r')
#    line_domain = domain_shortinfo.readline()
#    line_split = line_domain.split()
#    nSDD_X = int(line_split[4])
#    nSDD_Y = int(line_split[5])
#    domain_shortinfo.close()
#
#    qbc_stream = open(os.path.join(output_dir, quantity_name + '_bc.dat'), 'w+')
#
#    for SDDid in range(nSDD_X * nSDD_Y):
#        # Build coords -> uid correspondence
#        coords_to_uid = dict()
#        SDDpath = os.path.join(split_dir, 'sdd' + str(SDDid))
#        bc_f = open(os.path.join(SDDpath, 'bc.dat'), 'r')
#        for line in bc_f.readlines():
#            line_split = line.split()
#            coords = (int(line_split[1]), int(line_split[2]))
#            uid = line_split[0]
#            coords_to_uid[coords] = uid
#
#        sdd_f.close()
#
#        # Now iterating through quantity and add to global quantity stream
#        qbc_f = open(os.path.join(SDDpath, quantity_name + '_bc.dat'), 'r')
#        i = 0
#        for line in quantity_f.readlines():
#            line_split = line.split()
#            coords = (int(line_split[0]), int(line_split[1]))
#            qty_stream.write(coords_to_uid[coords] + " " + line_split[2] +
#                    "\n")
#
#    qty_stream.close()

