#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
import numpy as np
import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from script.rio import read_quantity, read_converter
from timeit import default_timer as timer

def compare_data(input_path1, input_path2, quantityNameList, precision):
    uid_to_coords_1 = dict()
    uid_to_coords_2 = dict()
    floatType = np.float64 if precision == 'double' else np.float32

    Nx1, Ny1, dx1, dy1 = read_converter(input_path1, uid_to_coords_1)
    Nx2, Ny2, dx2, dy2 = read_converter(input_path2, uid_to_coords_2)

    if not dx1 == dx2 or not dy1 == dy2 or not Nx1 == Nx2 or not Ny1 == Ny2:
        return False, "domain", (dx1, dy1, None)

    
    data1 = np.zeros((Nx1, Ny1), dtype = floatType)
    data2 = np.zeros((Nx2, Ny2), dtype = floatType)

    for q in quantityNameList:
        start = timer()
        read_quantity(data1, input_path1, uid_to_coords_1, q)
        read_quantity(data2, input_path2, uid_to_coords_2, q)
        end = timer()
        print("Time to load quantity", q, "%s second(s)" % int((end - start)))

        if not np.array_equal(data1, data2):
            print(q, input_path1, input_path2)
            print(dx1, dy1, dx2, dy2)
            print(data1 - data2)
            comparedata = data2 - data1
            return False, q, (dx1, dy1, comparedata)

    return True, None, (None, None, None)
