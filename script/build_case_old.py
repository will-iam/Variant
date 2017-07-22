#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import os
import sys
import argparse

import io
import imp

def build_case(root_dir, project_name, case_name, subdir = "tmp"):
    # Load all physical/numerical data from case
    case_path = os.path.join(root_dir, 'case', project_name, case_name)
    sys.path.append(case_path)
    import init as case
    case = reload(case)
    del sys.path[-1]

    output_dir = os.path.join(case_path, subdir, "init")
    io.make_sure_path_exists(output_dir)

    # Write scheme info
    sys.path.insert(1, root_dir)
    io.write_scheme_info(output_dir, case.T, case.CFL)

    # Write domain
    io.write_domain(output_dir, case.lx, case.ly, case.Nx, case.Ny,
            case.coords_to_uid)

    # Write quantities and boundary conditions if necessary
    for q_name, q in case.quantityDict.iteritems():
        io.write_quantity(output_dir, q_name, q['uid_to_val'])
        if q.get('uid_to_bc') is not None:
            io.write_boundary_conditions(output_dir, q_name,
                    q.get('uid_to_bc'))

    del case
    # Return path to case directory
    return output_dir

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(description="Build case tool")
    parser.add_argument("-d", type = str, help = "Root directory")
    parser.add_argument("-p", type = str, help = "Project name")
    parser.add_argument("-c", type = str, help = "Case name")
    args = parser.parse_args()

    build_case(args.d, args.p, args.c)

