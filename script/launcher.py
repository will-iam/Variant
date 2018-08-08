#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
import os
import sys
import socket
import numpy as np
from shutil import copyfile, copytree, rmtree
from timeit import default_timer as timer

sys.path.insert(1, os.path.join(sys.path[0], '..'))

import config
from script.build_case import build_case
import script.rio as io
import script.sdd as sdd
import script.compiler as compiler
from script.analytics import compare_data

COLOR_BLUE = '\x1b[1;36m'
COLOR_ENDC = '\x1b[0m'

def get_ref_name(precision):
    #return os.path.join('ref' + str(sys.version_info[0]), socket.gethostname())
    #return os.path.join('ref' + str(sys.version_info[0]))

    # cmd = [config.mpi_CC, '--version']
    # res = subprocess.check_call(cmd)

    return os.path.join('ref', precision)

def get_case_path(project_name, case_name):
    return os.path.join(config.cases_dir, project_name, case_name)

def case_exist(project_name, case_name):
    case_path = get_case_path(project_name, case_name)
    if not os.path.isdir(case_path):
        return False

    if not os.path.isfile(os.path.join(case_path, 'init.py')):
        return False

    if not os.path.isfile(os.path.join(case_path, 'chars.py')):
        return False

    return True


def check_test(test_path, ref_path, qties_to_compare):
    print("Checking test " + test_path + " against " + ref_path)
    results = compare_data(ref_path, test_path, qties_to_compare)
    if results[0]:
        print("OK for all quantities")
    else:
        print("Error for quantity " + str(results[1]))
    return results

def create_ref(engineOptionDict, case_path, init_path, ref_path):
    '''
    test = dict()
    test['nSDD'] = (1, 1)
    test['nSDS'] = 1
    test['SDSgeom'] = 'line'
    test['nThreads'] = 1
    nCoresPerSDD = 1
    '''
    # Get case path, where to find the data to build the case.
    if os.path.isdir(ref_path):
        return

    print("Reference case does not exist, create it.")

    # Build case.
    print(COLOR_BLUE + "Building reference case data" + COLOR_ENDC)
    qty_name_list = build_case(case_path, init_path)

    # Split case for SDDs
    print(COLOR_BLUE + "Splitting case data 1x1" + COLOR_ENDC)
    input_path = sdd.split_case(init_path, 1, 1, qty_name_list)

    # Add exec options
    io.write_exec_options(input_path, 1, 1, 1, 1, 'line', 1, 0, 1)

    # Copying exec_options and scheme_info in input path too
    copyfile(os.path.join(init_path, 'scheme_info.dat'), os.path.join(input_path, 'scheme_info.dat'))

    # Building output paths (the engine cannot create them itself)
    rmtree(ref_path, ignore_errors=True)
    copytree(input_path, ref_path) # To get the same SDD directories.

    # Compile (if needed) engine and call it
    print(COLOR_BLUE + "Compiling engine" + COLOR_ENDC)
    engine = compiler.Engine(engineOptionDict)

    print(COLOR_BLUE + "Calling engine" + COLOR_ENDC)
    engine.run(input_path, ref_path, 1, 1, 1)

    # Merge back
    io.make_sure_path_exists(ref_path)
    print(COLOR_BLUE + "Merging final data for reference" + COLOR_ENDC)
    sdd.merge_domain(ref_path, ref_path)
    for q_str in qty_name_list:
        sdd.merge_quantity(ref_path, ref_path, q_str)
    rmtree(os.path.join(ref_path, "sdd0"), ignore_errors=True)

def launch_test(tmp_dir, engineOptionDict, case_name, test, compare_with_ref, fastref):
    # Check values for pure sequential test.
    if engineOptionDict['compiler'] != 'mpi':
        if test['nSDD'][0] != 1 or test['nSDD'][1] != 1 or test['nThreads'] != 1.0:
            print('Cannot start a test in pure sequential mode with these options.')
            sys.exit(1)

    # Define paths
    project_name = engineOptionDict['project_name']
    case_path = get_case_path(project_name, case_name)
    init_path = os.path.join(case_path, "init")

    # Path where the reference will be stored if any.
    ref_path = os.path.join(case_path, get_ref_name(engineOptionDict['precision']))
    if fastref == True:
        # Don't check if you want only to build the ref.
        compare_with_ref = False
        if os.path.isdir(ref_path):
            print("Reference for case does exist already, return.")
            return None, 0

    # Start time
    start = timer()

    # Build case
    print(COLOR_BLUE + "Building case data" + COLOR_ENDC)
    qty_name_list = build_case(case_path, init_path)

    # Manage number of SDD
    nSDD_X = test['nSDD'][0]
    nSDD_Y = test['nSDD'][1]

    # Split case for SDDs into tmp directory
    print(COLOR_BLUE + "Splitting case data " + str(nSDD_X) + "x" + str(nSDD_Y) + COLOR_ENDC)
    input_path = sdd.split_case(init_path, nSDD_X, nSDD_Y, qty_name_list)

    # Add exec options
    io.write_exec_options(input_path, nSDD_X * nSDD_Y, nSDD_X, nSDD_Y, test['nSDS'], test['SDSgeom'], test['nThreads'], test['nCommonSDS'], test['nCoresPerSDD'])

    # Copying exec_options and scheme_info in input path too
    copyfile(os.path.join(init_path, 'scheme_info.dat'), os.path.join(input_path, 'scheme_info.dat'))

    # Building output paths (the engine cannot create them itself)
    output_path = os.path.join(tmp_dir, project_name, case_name, "final")
    rmtree(output_path, ignore_errors=True)
    copytree(input_path, output_path)

    # Compile (if needed) engine and call it
    print(COLOR_BLUE + "Compiling engine" + COLOR_ENDC)
    engine = compiler.Engine(engineOptionDict, engineOptionDict['must_compile'])

    print(COLOR_BLUE + "Calling engine" + COLOR_ENDC)
    run_option = [] if compare_with_ref == True or fastref == True else ['--dry']

    engine.run(input_path, output_path, engineOptionDict['node_number'], nSDD_X * nSDD_Y, int(np.ceil(test['nCoresPerSDD'])), run_option)
    end = timer()

    # Now, look for differences, if any.
    if compare_with_ref == True:
        print(COLOR_BLUE + "Merging final data" + COLOR_ENDC)
        sdd.merge_domain(output_path, output_path)
        for q_str in qty_name_list:
            sdd.merge_quantity(output_path, output_path, q_str)

        # Getting/building reference for the case
        create_ref(engineOptionDict, case_path, init_path, ref_path)

        # Now actually compare.
        result, qty, error_data = check_test(output_path, ref_path, qty_name_list)
        if result:
            print("Compared with reference: OK.")
        else:
            print("Compared with reference: ERROR, different result for quantity " + qty)
            sys.exit(1)

    if fastref == True:
        print(COLOR_BLUE + "Merging final data" + COLOR_ENDC)
        io.make_sure_path_exists(ref_path)
        sdd.merge_domain(output_path, ref_path)
        for q_str in qty_name_list:
            sdd.merge_quantity(output_path, ref_path, q_str)


    return output_path, int((end - start) * 1000)
