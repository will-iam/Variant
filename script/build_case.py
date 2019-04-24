#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
import os
import sys
from importlib import *
from shutil import rmtree
import script.rio as io

def build_case(case_path, output_dir, force_build = False):
    '''
    Build all physical/numerical data from case
    '''

    # If the directory does not exist, then build:
    if not os.path.isdir(output_dir):
        force_build = True
        io.make_sure_path_exists(output_dir)

    if not force_build:
        last_modif = os.path.getmtime(os.path.join(case_path, 'chars.py'))
        case_build_dir =  os.path.join(os.path.dirname(os.path.realpath(__file__)), 'initial_condition')
        for f in os.listdir(case_build_dir):
            if f.endswith(".py"):
                last_modif = max(last_modif, os.path.getmtime(os.path.join(case_build_dir, f)))

        if last_modif < os.path.getctime(output_dir):
            print('case already built')
            sys.path.append(case_path)
            import chars
            qtyList = chars.quantityList
            del sys.path[-1]
            del sys.modules["chars"]
            del chars
            return list(qtyList)

    print("Case path:", case_path)
    sys.path.append(case_path)
    # Reload chars also else, you build the case with the wrong characteristics
    import chars as case
    reload(case)

    coords_to_uid = io.gen_coords_to_uid(case.Nx, case.Ny)
    coords_to_bc = dict()
    quantityDict = dict()
    case.buildme(quantityDict, coords_to_uid, coords_to_bc)

    # Merging uid and bc dictionaries
    coords_to_uid_bc = io.gen_coords_to_uid_bc(case.Nx, case.Ny, case.BClayer)
    ds = [coords_to_uid_bc, coords_to_bc]
    coords_to_uid_and_bc = dict()
    for coord in coords_to_bc:
        coords_to_uid_and_bc[coord] = tuple(d.get(coord) for d in ds)

    rmtree(output_dir, ignore_errors=True)
    io.make_sure_path_exists(output_dir)

    # Write scheme info
    io.write_scheme_info(output_dir, case.T, case.CFL, case.gamma)

    # Write domain
    io.write_domain(output_dir, case.lx, case.ly, case.Nx, case.Ny, coords_to_uid, case.BClayer)

    # Write boundary conditions
    io.write_bc(output_dir, coords_to_uid_and_bc)

    # Write quantities and boundary conditions if necessary
    for q_name, q in quantityDict.items():
        io.write_quantity(output_dir, q_name, q)

    # Use quantity list from the characteristics.
    q_name_list = list(case.quantityList)

    # Del case and chars
    del sys.path[-1]
    del sys.modules["chars"]
    del case

    # Return path to case directory
    return q_name_list

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(description="Build case tool")
    parser.add_argument("-d", type = str, help = "Root directory")
    parser.add_argument("-p", type = str, help = "Project name")
    parser.add_argument("-c", type = str, help = "Case name")
    args = parser.parse_args()

    build_case(args.d, args.p, args.c)
