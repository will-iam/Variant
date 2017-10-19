#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import os
import sys
from shutil import copyfile, copytree, rmtree
from timeit import default_timer as timer

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import config
import script.build_case as build_case
import script.io as io
import script.sdd as sdd
import script.compiler as compiler
from script.analytics import compare_data

COLOR_BLUE = '\x1b[1;36m'
COLOR_ENDC = '\x1b[0m'

def gen_ref_result(root_dir, tmp_dir, project_name, cn, comp, mode, precision, std):
    test = dict()
    test['nSDD'] = (1, 1)
    test['nSDS'] = 1
    test['SDSgeom'] = 'line'
    test['nThreads'] = 1
    return launch_test(root_dir, tmp_dir, project_name, cn, comp, mode, precision,
    std, True, test, 1, False, False, False, "ref")

def check_test(test_path, ref_path):
    print("Checking test " + test_path + " against " + ref_path)
    qties_to_compare = io.read_quantity_names(test_path)
    results = compare_data(ref_path, test_path, qties_to_compare)
    if results[0]:
        print("OK for all quantities")
    else:
        print("Error for quantity " + str(results[1]))
    return results

def launch_test(root_dir, tmp_dir, project_name, cn, comp, mode, precision, std,
        bool_compile, test, nCoresPerSDD = 1, vtune = False, gdb = False, valgrind = False, ref_case = "tmp"):
    # Start time
    start = timer()

    # Build case
    print(COLOR_BLUE + "Building case data" + COLOR_ENDC)
    case_path, qty_name_list = build_case.build_case(root_dir, tmp_dir, project_name, cn, ref_case)

    # Manage number of SDD
    nSDD_X = test['nSDD'][0]
    nSDD_Y = test['nSDD'][1]

    # Add exec options
    io.write_exec_options(case_path, nSDD_X * nSDD_Y, nSDD_X, nSDD_Y, test['nSDS'], test['SDSgeom'], test['nThreads'], nCoresPerSDD)

    input_path = os.path.join(root_dir, 'cases', project_name, cn, 'init', str(nSDD_X) + 'x' + str(nSDD_Y))
    # Split case for SDDs into tmp directory
    if not os.path.isdir(input_path):
        print(COLOR_BLUE + "Splitting case data" + COLOR_ENDC)
        input_path = sdd.split_case(case_path, nSDD_X, nSDD_Y, qty_name_list)

    # Copying exec_options and scheme_info in input path too
    copyfile(os.path.join(case_path, 'exec_options.dat'), os.path.join(input_path, 'exec_options.dat'))
    copyfile(os.path.join(case_path, 'scheme_info.dat'), os.path.join(input_path, 'scheme_info.dat'))

    # Building output paths (the engine cannot create them itself)
    output_path = os.path.join(tmp_dir, project_name, cn, "final")
    rmtree(output_path, ignore_errors=True)
    copytree(input_path, output_path)

    # Compile (if needed) engine and call it
    print(COLOR_BLUE + "Compiling engine" + COLOR_ENDC)
    engine = compiler.Engine(project_name, bool_compile, comp, mode, precision, std)
    nprocs = nSDD_X * nSDD_Y
    print(COLOR_BLUE + "Calling engine" + COLOR_ENDC)
    engine.run(input_path, output_path, nprocs, nCoresPerSDD, gdb, valgrind, vtune)

    # Variant info
    variant_info = io.read_variant_info(output_path, nSDD_X * nSDD_Y)

    # Perfs info
    perf_info = io.read_perf_info(output_path, nSDD_X * nSDD_Y)

    if ref_case == "ref":
        final_path = os.path.abspath(os.path.join(case_path, os.pardir, "final"))
    else:
        final_path = os.path.join(tmp_dir, project_name, cn, 'full_domain')
    io.make_sure_path_exists(final_path)

    # Merge back
    print(COLOR_BLUE + "Merging final data" + COLOR_ENDC)
    sdd.merge_domain(output_path, final_path)
    for q_str in qty_name_list:
        sdd.merge_quantity(output_path, final_path, q_str)

    end = timer()

    # Copying perf results and quantity names to final path
    copyfile(os.path.join(output_path, 'perfs.dat'),
             os.path.join(final_path, 'perfs.dat'))
    copyfile(os.path.join(case_path, 'quantities.dat'),
             os.path.join(final_path, 'quantities.dat'))


    return final_path, int((end - start) * 1000), variant_info, perf_info
