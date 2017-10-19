#!/usr/bin/python
# -*- coding:utf-8 -*-

import numpy as np
from decimal import Decimal
from script.io import read_quantity

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
        dx1, dy1, data1 = read_quantity(input_path1, q)
        dx2, dy2, data2 = read_quantity(input_path2, q)
        if not data1.shape == data2.shape:
            print("Shape mismatch between data")
            return False, q, (None, None, None)
        comparedata = data2 - data1
        if not dx1 == dx2 \
            or not dy1 == dy2 \
            or not np.array_equal(data1, data2):
                print (q, input_path1, input_path2)
                print (dx1, dy1, dx2, dy2)
                print (data1 - data2)
                return False, q, (dx1, dy1, comparedata)

    return True, None, (None, None, None)
