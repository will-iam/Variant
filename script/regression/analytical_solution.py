#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__

from math import sin, pi

def rho_init(x, y):
    #if x >= 0.25 and x <= 0.75 and y >= 0.25 and y <= 0.75:
    #    return 1
    if abs(x - 0.5) < 0.25 and abs(y - 0.5) < 0.25:
        return 1
    return 0
    #return 1 + sin(2 * pi * (x - 2 * y))

cst_ux = 1.0
cst_uy = 1.0

def rho_t(t, x, y):
    return rho_init((x - cst_ux * t) % 1.0, (y - cst_uy * t) % 1.0)

