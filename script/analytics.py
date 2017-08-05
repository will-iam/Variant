#!/usr/bin/python
# -*- coding:utf-8 -*-

import numpy as np
from decimal import Decimal
from io import read_quantity

def mass(data, dx, dy):
    mass = 0
    shape = data.shape
    for i in range(shape[0]):
        for j in range(shape[1]):
            mass += data[i][j] * dx * dy
    return mass

def norm(data, p, dx, dy):
    topower = lambda x: dx * dy * (Decimal(str(x)).copy_abs() ** p)
    return np.sum(np.vectorize(topower)(data)) ** (Decimal('1') / p)

def compare_data(input_path1, input_path2, quantityNameList):
    for q in quantityNameList:
        data1 = read_quantity(input_path1, q)
        data2 = read_quantity(input_path2, q)
        if not data1[2].shape == data2[2].shape:
            print("Shape mismatch between data")
            return False, q, data1[2]
        comparedata = data2[2] - data1[2]
        if not data1[0] == data2[0] \
            or not data1[1] == data2[1] \
            or not np.array_equal(data1[2], data2[2]):
                return False, q, comparedata

    return True, "", np.empty([1, 1])

