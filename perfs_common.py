#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
import sys

COLOR_BLUE = '\x1b[1;36m'
COLOR_ENDC = '\x1b[0m'

# Performance attributes
perf_dtypes = [('initTime', int), ('computeTime', int), ('finalizeTime', int),
            ('nIterations', int), ('totalExecTime', int),
	    ('nCoresPerMPI', int)]
perf_attrnames = [t[0] for t in perf_dtypes]
vi_dtypes = [('n_SDD', 'int'), ('n_SDD_X', 'int'), ('n_SDD_Y', 'int'),
              ('n_neighbourSDD', 'int'), ('n_physicalCells', 'int'),
              ('n_overlapCells', 'int'), ('n_boundaryCells', 'int'),
              ('n_SDS', 'int'), ('SDSgeom', 'S10'), ('n_threads', 'int'),
              ('thread_iteration_type', 'S10'), ('SoA_or_AoS', 'S10')]
vi_attrnames = [t[0] for t in vi_dtypes]

parser = argparse.ArgumentParser(description="Performance measures", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("-c", type = str, help = "Case to test",
        required=True)
parser.add_argument("--nruns", type = int, help = "Number of runs per variant",
        default=1)
parser.add_argument("--max_thread_number", type = int, help = "Max. number of threads",
	default=1)
parser.add_argument("--max_proc_number", type = int, help = "Max. number of procs",
	default=1)
parser.add_argument("--core_per_mpi", type = int, help = "Number of cores per MPI node",
	default=1)
parser.add_argument("--nocompile", action='store_true', default=False,
        help = "Never compiles project before calling it")
parser.add_argument("--nocheck", action='store_true', default=False,
        help = "Never compare computed results to reference")
parser.add_argument("--vtune", action='store_true', default=False,
        help = "Enable vtune tool")
args = parser.parse_args()

def compute_sds_number2(total_cells, nSDD, SDSsize):
	return total_cells / (nSDD * SDSsize)

def compute_sds_number(case_path, nSDD, SDSsize):
    sys.path.append(case_path)
    print case_path
    import chars
    chars = reload(chars)
    totalCells = chars.Nx * chars.Ny
    del sys.path[-1]
    del chars
    return compute_sds_number2(totalCells, nSDD, SDSsize)

