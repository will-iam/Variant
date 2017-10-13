#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import os
import sys
import argparse

import io
import imp
from shutil import rmtree

def build_case(root_dir, tmp_dir, project_name, case_name, subdir = "tmp",
        force_build = False):
    # Load all physical/numerical data from case
    case_path = os.path.join(root_dir, 'case', project_name, case_name)

    output_dir = os.path.join("case", project_name, case_name, "ref", "init")\
            if subdir == "ref" else os.path.join(tmp_dir, case_name, "init")
    if os.path.isdir(output_dir) and not force_build and subdir != "ref":
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
            return output_dir, list(qtyList)

    sys.path.append(case_path)
    import init as case
    case = reload(case)
    del sys.path[-1]

    rmtree(output_dir, ignore_errors=True)

    io.make_sure_path_exists(output_dir)

    # Write scheme info
    sys.path.insert(1, root_dir)
    io.write_scheme_info(output_dir, case.T, case.CFL)

    # Write domain
    io.write_domain(output_dir, case.lx, case.ly, case.Nx, case.Ny,
            case.coords_to_uid)

    # Write boundary conditions
    io.write_bc(output_dir, case.coords_to_uid_and_bc)

    # Write quantities and boundary conditions if necessary
    for q_name, q in case.quantityDict.iteritems():
        io.write_quantity(output_dir, q_name, q)

    # Write file with list of quantities
    io.write_quantity_names(output_dir, case.quantityDict.keys())

    q_name_list = list(case.quantityDict.keys())

    del case

    # Return path to case directory
    return output_dir, q_name_list

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(description="Build case tool")
    parser.add_argument("-d", type = str, help = "Root directory")
    parser.add_argument("-p", type = str, help = "Project name")
    parser.add_argument("-c", type = str, help = "Case name")
    args = parser.parse_args()

    build_case(args.d, args.p, args.c)

