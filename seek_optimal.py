#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import sys
import subprocess
from shutil import copyfile, copytree, rmtree
from decimal import *
import itertools
from timeit import default_timer as timer
import config
import script.compiler as compiler
from seek_common import *
from script.analytics import compare_data
from script.launcher import gen_ref_result, check_test, launch_test

# Define execution parameters
machine = args.machine
nTotalCores = args.max_proc_number
SDSgeom = 'line'
#caseSizeList = [128, 192, 256, 320, 384, 448, 512, 576, 640, 704, 768, 1024]
caseSizeList = [(256, 512), (512, 256)]
ratioThreadsCores = [1]
SDSratioList = [4]
nruns = 1

#nSDD = [1, 4, 16, 64, 256] en puissance de 2 = [0, 2, 4, 6, 8]
#SDD_powersOfTwo = [0, 2, 4, 6]
SDD_powersOfTwo = [0, 1, 2, 3, 4, 5, 6]
#SDD_powersOfTwo = [6]
#SDD_powersOfTwo = [0]
#SDD_powersOfTwo = [2, 3, 4, 5, 6, 7, 8]

project_name = args.project_name
comp = 'mpi'
mode = 'release'
precision = 'double'
std = 'c++11'
bool_compile = not args.nocompile

# Clean compile if requested.
if args.clean_compile:
    engine = compiler.Engine(project_name, False, comp, mode, precision, std, True)
    print("Cleaned target")
    sys.exit(0)

this_dir = os.path.split(os.path.abspath(__file__))[0]

# Get case names from all directories in case/project_name/
case_dir = os.path.join("case", project_name)
case_name = args.c
tmp_dir = os.path.join(config.tmp_dir, 'seek_optimal')

for caseSizeXY in caseSizeList:
	# Defining tmp directory
    cn = case_name + str(caseSizeXY[0]) + 'x' + str(caseSizeXY[1])
	
	# Cleaning tmp directory for new case
    rmtree(tmp_dir, ignore_errors=True)

	# Defining case path for results
    case_path = os.path.join(case_dir, cn)

	# Init results dir
    io.make_sure_path_exists(os.path.join(config.results_dir, 'seek_optimal', cn))
    results_path = os.path.join(config.results_dir, 'seek_optimal', cn, 'results_data.csv')

	# Getting/building referencephil collins son of man data for the case
    if not args.nocheck:
		ref_test_path = os.path.join(case_dir, cn, "ref", "final")
		if not os.path.isdir(ref_test_path):
		    print("Reference case does not exist, create ?")
		    if raw_input() != 'y':
		        sys.exit(0)
		    gen_ref_result(this_dir, tmp_dir, project_name, cn, comp, mode, precision)

	# Launch tests and compare results
    print(COLOR_BLUE + "Start seeking optimal with case: " + COLOR_ENDC + cn)

    for ratio in ratioThreadsCores:
        for p in SDD_powersOfTwo:
            # Different SDD splits, nSDD = 2**p
            for i in range(0, p/2 + 1):
                test = {}
                test['SDSgeom'] = SDSgeom
                test['nSDD'] = (2**i, 2**(p-i))
                nsdd = test['nSDD'][0]*test['nSDD'][1]
                for SDSratio in SDSratioList:
                    
                    # Exploration strong SDS, ncpmpi = nTotalCores / nsdd
                    coreNumberList = [nTotalCores / nsdd]
#                    coreNumberList = [1]
#                    coreNumberList = [1,2,4,8,16,32,64]
#                    coreNumberList = range(1, nTotalCores / nsdd + 1)
                    for ncpmpi in coreNumberList:
                        # élimine cas impossible
                        if ncpmpi > nTotalCores / nsdd:
                            continue

                        # Pour un calcul avec montée en charge (weak SDS)
                        #test['nThreads'] = (caseSize / (2 * ncpmpi))**2

                        # Pour un calcul avec montée en charge (weak SDD)
                        #test['nThreads'] = 1

                        # Pour un calcul à charge/ressource constante
                        test['nThreads'] = ncpmpi * ratio                    

                        # Définition du nombre de SDS    
#                        test['nSDS'] = compute_sds_number(case_path, nsdd, SDSsize)
                        test['nSDS'] = test['nThreads'] * SDSratio
                    
                        # the maximum number is the number of cells.
                        if test['nSDS'] > caseSizeXY[0] * caseSizeXY[1]:
                            continue 

					    # Launching runs for the test
                        perf_for_allruns = []
                        for n in range(nruns):
                            current_test_path, exec_time, variant_info, perf_info = launch_test(this_dir,
                            tmp_dir,
                            project_name, cn, comp, mode, precision, std, bool_compile,
                            test, ncpmpi, args.vtune)

                            # Check results and compare to reference.
                            if not args.nocheck:
	                            result, qty, error_data = check_test(current_test_path, ref_test_path)
	                            if result:
		                            print("Compared with reference: OK.")
	                            else :
		                            print("Compared with reference: ERROR, different result for quantity " + qty)
		                            sys.exit(1)
                            print("Total ExecTime:", exec_time)
                            print("Results for test: " + str(test) + " on run " + str(n) + " on " + str(nTotalCores) + " core(s).")
                            perf_for_allruns.append(make_perf_data(current_test_path, exec_time, perf_info))
                            print "perf_for_allruns", perf_for_allruns
                        # Join results
                        join_result_data(results_path, variant_info, perf_for_allruns, ncpmpi, machine)

print("\nTest successfully passed\n")

