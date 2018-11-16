#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
import os
import sys
import script.rio as io
from timeit import default_timer as timer
import numpy as np

def split_domain(domain_dir, output_dir, nSDD_X, nSDD_Y):
    io.make_sure_path_exists(output_dir)

    domain_f = open(os.path.join(domain_dir, 'domain.dat'), 'r')
    line_split = domain_f.readline().split()
    domain_lx = line_split[2]
    domain_ly = line_split[3]
    domain_Nx = int(line_split[4])
    domain_Ny = int(line_split[5])
    BClayer = int(line_split[6])

    SDD_Nx = domain_Nx // nSDD_X
    SDD_Ny = domain_Ny // nSDD_Y

    # Writing short domain info
    domain_shortinfo = open(os.path.join(output_dir, 'domain.info'), 'w+')
    domain_shortinfo.write(domain_lx + " " + domain_ly +\
            " " + str(domain_Nx) + " " + str(domain_Ny) +\
            " " + str(nSDD_X) + " " + str(nSDD_Y) + " " + str(BClayer) + "\n")
    domain_shortinfo.close()

    sdd_to_coords = dict()
    for SDDid in range(nSDD_X * nSDD_Y):
        sdd_to_coords[SDDid] = list()

    # Now iterating through all coords of domain
    for line in domain_f.readlines():
        line_split = line.split()
        uid = int(line_split[0])
        coordX = int(line_split[1])
        coordY = int(line_split[2])

        x = coordX // SDD_Nx
        y = coordY // SDD_Ny
        BL_X = SDD_Nx * x
        BL_Y = SDD_Ny * y

        # SDD id is known based on coords
        SDDid = y * nSDD_X + x
        sdd_to_coords[SDDid].append((uid, coordX - BL_X, coordY - BL_Y))

    # Closing all streams
    domain_f.close()

    # We build for each SDD a file stream that will be updated through
    # iterations on the domain data
    for x in range(nSDD_X):
        for y in range(nSDD_Y):
            # Writing SDD file
            SDDid = y * nSDD_X + x
            SDDpath = os.path.join(output_dir, 'sdd' + str(SDDid))
            io.make_sure_path_exists(SDDpath)

            # Writing bottom-left coords on domain
            BL_X = SDD_Nx * x
            BL_Y = SDD_Ny * y
            with open(os.path.join(SDDpath, 'sdd.dat'), 'w+') as file_stream:
                file_stream.write(str(BL_X) + " " + str(BL_Y) + "\n")
                file_stream.write(str(SDD_Nx) + " " + str(SDD_Ny) + "\n")

                # Finally writing uid on domain and position on SDD
                for c in sdd_to_coords[SDDid]:
                    file_stream.write("%s %s %s\n" % (c[0], c[1], c[2]))

    return sdd_to_coords

def merge_domain(split_dir, output_dir):
    domain_shortinfo = open(os.path.join(split_dir, "domain.info"), 'r')
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

            with open(os.path.join(SDDpath, 'sdd.dat'), 'r') as file_stream:
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
                        domain_f.write(uid + " " + str(BL_X + coordX_SDD) + " " + str(BL_Y + coordY_SDD) + "\n")

    domain_f.close()

def split_quantity(quantity_dir, output_dir, quantity_name, sdd_to_coords):

    quantity_file_name = os.path.join(quantity_dir, quantity_name + '.dat')

    # Assume the file is only zero in this case (to save space).
    if not os.path.exists(quantity_file_name):
        return

    domain_shortinfo = open(os.path.join(output_dir, "domain.info"), 'r')
    line_domain = domain_shortinfo.readline()
    line_split = line_domain.split()
    domain_shortinfo.close()

    nSDD = int(line_split[4]) * int(line_split[5])
    quantity = np.loadtxt(quantity_file_name, usecols=[1])

    # Opening streams for all SDDs
    for SDDid in range(nSDD):
        SDDpath = os.path.join(output_dir, 'sdd' + str(SDDid))
        with open(os.path.join(SDDpath, quantity_name + '.dat'), 'w+') as file_stream:
            # Now iterationg through all cell uids on quantity file
            for c in sdd_to_coords[SDDid]:
                file_stream.write("%s %s %16.16g\n" % (c[1], c[2], quantity[c[0]]))

def split_bc(bc_dir, output_dir):
    domain_shortinfo = open(os.path.join(output_dir, "domain.info"), 'r')
    line_split = domain_shortinfo.readline().split()

    domain_Nx = int(line_split[2])
    domain_Ny = int(line_split[3])
    nSDD_X = int(line_split[4])
    nSDD_Y = int(line_split[5])
    BClayer = int(line_split[6])

    nSDD = nSDD_X * nSDD_Y
    SDD_Nx = domain_Nx / nSDD_X
    SDD_Ny = domain_Ny / nSDD_Y
    domain_shortinfo.close()

    # Opening file streams
    file_streams = list()
    BL = list()
    for SDDid in range(nSDD):
        SDDpath = os.path.join(output_dir, 'sdd' + str(SDDid))
        # BL coordinates of SDDs, needed for coord conversion
        sdd_f = open(os.path.join(SDDpath, 'sdd.dat'), 'r')
        line_split = sdd_f.readline().split()
        BL.append((int(line_split[0]), int(line_split[1])))
        sdd_f.close()
        file_streams.append(open(os.path.join(SDDpath, 'bc.dat'), 'w+'))

    bc_f = open(os.path.join(bc_dir, 'bc.dat'), 'r')
    for line in bc_f:
        line_split = line.split()
        uid = line_split[0]
        coordX = int(line_split[1])
        coordY = int(line_split[2])
       

        # Determine to which SDD belongs the boundary cell
        eqCoordX = coordX
        eqCoordY = coordY

        # Left
        if coordX < 0:
            eqCoordX = 0
        # Top
        if coordY >= domain_Ny:
            eqCoordY = domain_Ny - 1
        # Right
        if coordX >= domain_Nx:
            eqCoordX = domain_Nx - 1
        # Bottom
        if coordY < 0:
            eqCoordY = 0

        # Determine SDD corresponding to eq coords
        x = eqCoordX // SDD_Nx
        y = eqCoordY // SDD_Ny
        SDDid = int(x + nSDD_X * y)

        # Determine coords on SDD: we use bottom-left coords of SDD
        BL_X = BL[SDDid][0]
        BL_Y = BL[SDDid][1]

        newLine = uid + " " + str(coordX - BL_X) + " " + str(coordY - BL_Y) + " " + " ".join(line_split[3:])  + "\n"
        # and add the boundary cell to the corresponding file
        file_streams[SDDid].write(newLine)

        # Corners ...
        cornerX = eqCoordX
        if BL_X > 0 and eqCoordX - BClayer - BL_X < 0:
            cornerX = eqCoordX - BClayer
        elif BL_X + SDD_Nx < domain_Nx and eqCoordX + BClayer - BL_X > 0:
            cornerX = eqCoordX + BClayer

        cornerY = eqCoordY
        if BL_Y > 0 and eqCoordY - BClayer - BL_Y < 0:
            cornerY = eqCoordY - BClayer
        elif BL_Y + SDD_Ny < domain_Ny and eqCoordY + BClayer - BL_Y > 0:
            cornerY = eqCoordY + BClayer

        otherX = cornerX // SDD_Nx
        otherY = cornerY // SDD_Ny
        otherSDDid = int(otherX + nSDD_X * otherY)

        '''
        if coordX == -1 and coordY == 32:
            print "BL_X: ", BL_X, "BL_Y: ", BL_Y
            print "coordX: ", coordX, "coordY: ", coordY
            print "eqCoordX: ", eqCoordX, "eqCoordY: ", eqCoordY
            print "cornerX: ", cornerX, "cornerY: ", cornerY
            print "my SDD: ", SDDid
            print "my other SDD: ", otherSDDid
        '''

        if otherSDDid != SDDid:
            # Determine coords on SDD: we use bottom-left coords of SDD
            otherBL_X = BL[otherSDDid][0]
            otherBL_Y = BL[otherSDDid][1]

            # and add the boundary cell to the corresponding file
            newLine = uid + " " + str(coordX - otherBL_X) + " " + str(coordY - otherBL_Y) + " " + " ".join(line_split[3:]) + "\n"
            file_streams[otherSDDid].write(newLine)

    bc_f.close()
    for i in range(nSDD):
        file_streams[i].close()

    return

def merge_quantity(split_dir, output_dir, quantity_name):
    domain_shortinfo = open(os.path.join(split_dir, "domain.info"), 'r')
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
        with open(os.path.join(SDDpath, quantity_name + '.dat'), 'r') as quantity_f:
            for line in quantity_f.readlines():
                line_split = line.split()
                coords = (int(line_split[0]), int(line_split[1]))
                qty_stream.write(coords_to_uid[coords] + " " + line_split[2] + "\n")

    qty_stream.close()


def split_case(domain_dir, nSDD_X, nSDD_Y, qty_name_list):
    output_dir = os.path.join(domain_dir, str(nSDD_X) + "x" + str(nSDD_Y))
    if os.path.isdir(output_dir):
        print("Split already exists")
        return output_dir
    io.make_sure_path_exists(output_dir)
    start = timer()
    sdd_to_coords = split_domain(domain_dir, output_dir, nSDD_X, nSDD_Y)
    end = timer()
    print("Time to split domain %s second(s)" % int((end - start)))

    split_bc(domain_dir, output_dir)
    for q_str in qty_name_list:
        start = timer()
        split_quantity(domain_dir, output_dir, q_str, sdd_to_coords)
        end = timer()
        print("Time to split quantity", q_str, "%s second(s)" % int((end - start)))

    return output_dir
