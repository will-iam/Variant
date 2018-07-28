#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import os
import sys
from importlib import *
from shutil import rmtree
import config
import script.io as io

def build_case(case_path, output_dir, force_build = False):
    '''
    Load all physical/numerical data from case
    '''

    # If the directory does not exist, then build:
    if not os.path.isdir(output_dir):
        force_build = True
        io.make_sure_path_exists(output_dir)

    if not force_build:
        last_modif = max(os.path.getmtime(os.path.join(case_path, 'init.py')),
            os.path.getmtime(os.path.join(case_path, 'chars.py')))
        if last_modif < os.path.getctime(output_dir):
            print('case already built')
            sys.path.append(case_path)
            import chars
            chars = reload(chars)
            del sys.path[-1]
            qtyList = chars.quantityList
            del chars
            return list(qtyList)

    print(case_path)
    sys.path.append(case_path)
    # Reload chars also else, you build the case with the wrong characteristics
    import chars
    # chars = reload(chars)

    import init as case
    # case = reload(case)

    del sys.path[-1]

    rmtree(output_dir, ignore_errors=True)

    io.make_sure_path_exists(output_dir)

    # Write scheme info
    io.write_scheme_info(output_dir, case.T, case.CFL)

    # Write domain
    io.write_domain(output_dir, case.lx, case.ly, case.Nx, case.Ny, case.coords_to_uid, case.BClayer)

    # Write boundary conditions
    io.write_bc(output_dir, case.coords_to_uid_and_bc)

    # Write quantities and boundary conditions if necessary
    for q_name, q in case.quantityDict.items():
        io.write_quantity(output_dir, q_name, q)
    
    # Use quantity list from the characteristics.
    q_name_list = list(chars.quantityList)

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
